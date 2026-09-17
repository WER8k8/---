# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""节点终态钩子链（H.7：D 类机制层 Evolution / Pipeline 变钩子，不做独立引擎）。

接线纪律（与 n8n 出站通知同规格）：
- 钩子 best-effort：任何异常都记录并吞掉，绝不阻断主编排主链（主链终态已由
  complete_task / fail_task 落定，钩子只读任务面、只写进化/管线域）。
- 不新增 `ROUTERS` 路由、不改任务状态机：唯一触发点 = 节点终态（done / failed）。
- 经验回流载体 = Evolution 引擎（record_task_execution 数据入口 + 达阈值时
  run_experience_extraction 沉淀），管线关卡载体 = Pipeline gate_content
  （特性开关 PIPELINE_GATES_ENABLED，标记语义，默认 off 零回归）。
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger("uj-admin.hermes.node_terminal_hooks")

# 管线关卡只挂「内容产出/分发」族节点，其余节点不介入。
_CONTENT_NODE_MARKERS = ("content", "publish")

# 经验沉淀阈值：回溯窗口内记录数达到该值才触发一次提取（避免每节点都全量扫描）。
_EXTRACTION_MIN_RECORDS = 5
_EXTRACTION_LOOKBACK_HOURS = 24


@dataclass
class NodeTerminalHookReport:
    """钩子执行留痕（只进日志，不回写 ai_tasks）。"""

    task_id: str
    success: bool
    evolution_recorded: bool = False
    evolution_record_id: str = ""
    experiences_created: int = 0
    pipeline_gate: str = "off"  # off / approved / needs_review / blocked_cleanse / skipped
    errors: Dict[str, str] = field(default_factory=dict)

    def summary(self) -> str:
        """summary。

        参数说明：
        :return: 返回处理结果。
        """
        parts = [
            f"task={self.task_id}",
            f"success={self.success}",
            f"evolution={'recorded' if self.evolution_recorded else 'skipped'}",
            f"experiences={self.experiences_created}",
            f"gate={self.pipeline_gate}",
        ]
        if self.errors:
            parts.append("errors=" + ";".join(f"{k}={v[:80]}" for k, v in self.errors.items()))
        return " ".join(parts)


def _executor_name_of(task: Any) -> str:
    task_type = str(getattr(task, "task_type") or "")
    if task_type.startswith("hermes_node:"):
        return task_type.split(":", 1)[1]
    return task_type


def _content_text_of(result: Dict[str, Any]) -> tuple[str, str]:
    """从节点产出里取（title, body）供管线关卡评估；取不到就空串。"""
    title = str((result or {}).get("title") or (result or {}).get("product_name") or "")
    body = str(
        (result or {}).get("reply")
        or (result or {}).get("content")
        or (result or {}).get("summary")
        or ""
    )
    return title, body


def _fire_evolution(
    db: Any,
    task: Any,
    *,
    success: bool,
    result: Optional[Dict[str, Any]],
    error_code: Optional[str],
    error_message: Optional[str],
    report: NodeTerminalHookReport,
) -> None:
    """经验回流钩子：数据入口 record + 达阈值时沉淀经验。"""
    from app.services.evolution.engine import EvolutionEngine
    from app.models.evolution import EvolutionTaskRecord
    from sqlalchemy import func
    from datetime import datetime, timezone, timedelta

    task_type = _executor_name_of(task)
    engine = EvolutionEngine(db)
    record = engine.record_task_execution(
        task_type=task_type,
        executor_type="hermes",
        executor_id=str(getattr(task, "id", "") or ""),
        success=success,
        tenant_id=str(task.tenant_id) if getattr(task, "tenant_id", None) else None,
        error_code=error_code,
        error_message=(error_message or "")[:500] or None,
        input_summary=str(getattr(task, "input_json", "") or "")[:500] or None,
        output_summary=str((result or {}).get("summary") or (result or {}).get("reply") or "")[:500] or None,
        metadata={
            "task_id": str(getattr(task, "id", "") or ""),
            "parent_task_id": str(getattr(task, "parent_task_id", "") or ""),
            "task_plane": "hermes",
        },
    )
    report.evolution_recorded = True
    report.evolution_record_id = str(getattr(record, "id", "") or "")

    # 同步沉淀至 ExperienceEngine（供 DAG Governor 拓扑分析与少样本增强）
    try:
        from app.services.hermes.experience_engine import get_engine
        duration = 0.0
        if getattr(task, "created_at", None) and getattr(task, "updated_at", None):
            try:
                duration = max(0.0, (task.updated_at - task.created_at).total_seconds())
            except Exception:
                duration = 0.0
        get_engine().record(
            task_type=task_type,
            success=success,
            duration=duration,
            error_type=error_code,
            solution=str(error_message or "")[:200] if not success else None,
        )
    except Exception as exp_exc:  # noqa: BLE001
        logger.debug("experience_engine record failed (ignored): %s", exp_exc)

    # 机会式经验沉淀：只有回溯窗口内样本够多才扫（低开销护栏，不新增调度入口）。
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=_EXTRACTION_LOOKBACK_HOURS)
        count = (
            db.query(func.count(EvolutionTaskRecord.id))
            .filter(
                EvolutionTaskRecord.task_type == task_type,
                EvolutionTaskRecord.created_at >= cutoff,
            )
            .scalar()
            or 0
        )
        if count >= _EXTRACTION_MIN_RECORDS:
            outcome = engine.run_experience_extraction(
                task_type, lookback_hours=_EXTRACTION_LOOKBACK_HOURS
            )
            report.experiences_created = int(outcome.get("created") or 0)
    except Exception as exc:  # noqa: BLE001 - 沉淀失败不影响记录成功
        report.errors["evolution_extract"] = f"{type(exc).__name__}: {exc}"


def _fire_pipeline_gate(
    db: Any,
    task: Any,
    result: Optional[Dict[str, Any]],
    report: NodeTerminalHookReport,
) -> None:
    """管线关卡钩子：内容族节点终态时打一次 gate_content 标记（默认 off 零回归）。"""
    if os.environ.get("PIPELINE_GATES_ENABLED") != "1":
        report.pipeline_gate = "off"
        return
    executor_name = _executor_name_of(task)
    if not any(marker in executor_name for marker in _CONTENT_NODE_MARKERS):
        report.pipeline_gate = "skipped"
        return
    title, body = _content_text_of(result or {})
    if not body and not title:
        report.pipeline_gate = "skipped"
        return
    try:
        from app.services.pipeline.chains import gate_content

        report.pipeline_gate = gate_content(
            db,
            tenant_id=str(getattr(task, "tenant_id", "") or ""),
            title=title,
            content=body,
            chain="article",
            meta={"task_id": str(getattr(task, "id", "") or "")},
        ).verdict
    except Exception as exc:  # noqa: BLE001 - 关卡故障视为 off，不改变原流程
        report.errors["pipeline_gate"] = f"{type(exc).__name__}: {exc}"
        report.pipeline_gate = "off"


def fire_node_terminal_hooks(
    db: Any,
    task: Any,
    *,
    success: bool,
    result: Optional[Dict[str, Any]] = None,
    error_code: Optional[str] = None,
    error_message: Optional[str] = None,
) -> NodeTerminalHookReport:
    """节点终态统一钩子入口。永不抛出：调用方（桥）无需再做容错。"""
    report = NodeTerminalHookReport(
        task_id=str(getattr(task, "id", "") or ""),
        success=success,
    )
    try:
        _fire_evolution(
            db,
            task,
            success=success,
            result=result,
            error_code=error_code,
            error_message=error_message,
            report=report,
        )
    except Exception as exc:  # noqa: BLE001 - 钩子异常不得打断主链
        report.errors["evolution"] = f"{type(exc).__name__}: {exc}"
        logger.exception("node_terminal_hooks: evolution 钩子失败 task=%s", report.task_id)
    if success:
        try:
            _fire_pipeline_gate(db, task, result, report)
        except Exception as exc:  # noqa: BLE001
            report.errors["pipeline_gate"] = f"{type(exc).__name__}: {exc}"
            logger.exception("node_terminal_hooks: pipeline 钩子失败 task=%s", report.task_id)
    logger.info("node_terminal_hooks: %s", report.summary())
    return report
