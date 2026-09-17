# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""终态钩子 — 任务终态接线至经验飞轮（总纲 §4.6-7 / §6.6 P3）。

触发时机：Pipeline / Hermes / DeerFlow 等执行到达终态（done/failed）后调用。
动作：
1. 写 EvolutionTaskRecord（数据收集，进化引擎原始输入）；
2. 聚合记分卡（skill_performance / agent_scorecards，从终态 Trace 更新）；
3. 失败经验直接入 ExperienceEntry（failure_pattern），按阈值分级
   raw → validated → pattern → sop → skill（§4.6-7 阈值控制）；
4. 成功经验不在此处直接建条目——由 ExperienceStore.extract_from_records
   批量提炼（阈值 + 样本数控制），本钩子只负责失败快速入库。
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.evolution import EvolutionTaskRecord, ExperienceEntry
from app.services.trace.trace_service import TaskTraceService

logger = logging.getLogger("uj-admin.trace.terminal_hook")

# 经验成熟度分级阶梯（§4.6-7：Raw→Validated→Pattern→SOP→Skill）
EXPERIENCE_STAGE_ORDER = ("raw", "validated", "pattern", "sop", "skill")
# 分级晋升阈值（occurrence_count 达到即升一级）
_STAGE_PROMOTION_THRESHOLDS = {
    "validated": 3,   # 同一失败模式出现 3 次 → 视为有效（validated）
    "pattern": 5,     # 5 次 → 提炼为可复用模式（pattern）
    "sop": 10,        # 10 次 → 具备沉淀为 SOP 的价值
    "skill": 20,      # 20 次 → 具备自动优化 Skill 的价值
}


def promote_experience_stage(db: Session, entry_id: str, min_occurrence: Optional[int] = None) -> ExperienceEntry:
    """按阈值推进经验成熟度分级。返回更新后的条目。"""
    entry = db.query(ExperienceEntry).filter(ExperienceEntry.id == entry_id).first()
    if not entry:
        raise ValueError(f"experience_not_found: {entry_id}")

    cur_idx = EXPERIENCE_STAGE_ORDER.index(entry.stage) if entry.stage in EXPERIENCE_STAGE_ORDER else 0
    count = entry.occurrence_count
    # 逐级向上推进：当前级别未达标则停在当前级
    while cur_idx < len(EXPERIENCE_STAGE_ORDER) - 1:
        next_stage = EXPERIENCE_STAGE_ORDER[cur_idx + 1]
        threshold = min_occurrence if min_occurrence is not None else _STAGE_PROMOTION_THRESHOLDS.get(next_stage, 0)
        if count < threshold:
            break
        cur_idx += 1
        entry.stage = EXPERIENCE_STAGE_ORDER[cur_idx]

    entry.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(entry)
    return entry


def record_terminal_state(
    db: Session,
    *,
    task_type: str,
    executor_type: str = "skill",
    executor_id: str,
    success: bool,
    tenant_id: Optional[str] = None,
    duration_ms: int = 0,
    cost: float = 0.0,
    tokens_used: int = 0,
    error_code: Optional[str] = None,
    error_message: Optional[str] = None,
    input_summary: Optional[str] = None,
    output_summary: Optional[str] = None,
    trace_id: Optional[str] = None,
    skill_id: Optional[str] = None,
    skill_version: Optional[str] = None,
    model_name: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
    capture_failure_experience: bool = True,
) -> dict[str, Any]:
    """终态钩子主入口。

    返回：
        {
            "record_id": str,
            "trace_id": str | None,
            "experience_id": str | None,   # 失败快速入库的经验（若有）
            "experience_stage": str | None,
            "skill_performance_updated": bool,
            "agent_scorecard_updated": bool,
        }
    """
    now = datetime.now(timezone.utc)
    record = EvolutionTaskRecord(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        task_type=task_type,
        executor_type=executor_type,
        executor_id=executor_id,
        success=success,
        duration_ms=duration_ms,
        cost=cost,
        tokens_used=tokens_used,
        error_code=error_code,
        error_message=error_message,
        input_summary=input_summary,
        output_summary=output_summary,
        metadata_json=metadata or {},
        created_at=now,
    )
    db.add(record)

    exp_id: Optional[str] = None
    exp_stage: Optional[str] = None
    # 失败经验快速入库（§4.6-7：失败经验入 ExperienceEntry(kind='failure')）
    if capture_failure_experience and not success:
        exp = _capture_failure_experience(
            db, task_type=task_type, executor_type=executor_type,
            executor_id=executor_id, error_code=error_code,
            error_message=error_message, tenant_id=tenant_id,
            trace_id=trace_id, model_name=model_name,
        )
        if exp:
            exp_id = str(exp.id)
            exp_stage = exp.stage

    db.commit()

    # 记分卡聚合（best-effort，失败不阻断主链路）
    perf_updated = False
    card_updated = False
    try:
        svc = TaskTraceService(db)
        if skill_id:
            perf_updated = (
                svc.aggregate_skill_performance(
                    skill_id, skill_version=skill_version or "",
                    tenant_id=tenant_id,
                ) is not None
            )
        if trace_id and executor_type in ("agent", "workflow"):
            card_updated = (
                svc.aggregate_agent_scorecard(
                    executor_id, task_type, tenant_id=tenant_id,
                ) is not None
            )
    except Exception as exc:  # pragma: no cover — 记分卡故障不应阻断主链路
        logger.warning("terminal_hook: 记分卡聚合失败（忽略）: %s", exc)
        db.rollback()

    logger.info(
        "terminal_state: task=%s executor=%s/%s success=%s trace=%s",
        task_type, executor_type, executor_id, success, trace_id,
    )
    return {
        "record_id": str(record.id),
        "trace_id": trace_id,
        "experience_id": exp_id,
        "experience_stage": exp_stage,
        "skill_performance_updated": perf_updated,
        "agent_scorecard_updated": card_updated,
    }


def _capture_failure_experience(
    db: Session,
    *,
    task_type: str,
    executor_type: str,
    executor_id: str,
    error_code: Optional[str],
    error_message: Optional[str],
    tenant_id: Optional[str],
    trace_id: Optional[str],
    model_name: Optional[str],
) -> Optional[ExperienceEntry]:
    """失败经验入库：按 (task_type, failure_pattern, executor) 合并计数并推进分级。"""
    key = _failure_key(task_type, executor_type, executor_id)
    existing = (
        db.query(ExperienceEntry)
        .filter(
            ExperienceEntry.task_type == task_type,
            ExperienceEntry.pattern_type == "failure_pattern",
            ExperienceEntry.pattern_data["executor_id"].as_string() == executor_id,
        )
        .order_by(ExperienceEntry.updated_at.desc())
        .first()
    )
    now = datetime.now(timezone.utc)
    pattern_data = {
        "executor_id": executor_id,
        "executor_type": executor_type,
        "error_code": error_code,
        "error_message": (error_message or "")[:300],
        "model_name": model_name,
        "trace_id": trace_id,
        "last_failed_at": now.isoformat(),
    }
    if existing:
        existing.occurrence_count += 1
        existing.pattern_data = {**existing.pattern_data, **pattern_data}
        existing.confidence = min(0.99, existing.confidence + 0.05)
        existing.updated_at = now
        entry = existing
    else:
        entry = ExperienceEntry(
            id=str(uuid.uuid4()),
            task_type=task_type,
            pattern_type="failure_pattern",
            stage="raw",
            title=f"失败经验: {executor_type}/{executor_id}",
            description=(
                f"任务 {task_type} 执行失败"
                + (f"（{error_code}）" if error_code else "")
                + (f": {error_message}" if error_message else "")
            ),
            pattern_data=pattern_data,
            confidence=0.5,
            occurrence_count=1,
            applied=False,
            source_record_ids=[trace_id] if trace_id else [],
            created_at=now,
            updated_at=now,
        )
        db.add(entry)
        db.flush()

    # 按阈值推进分级（validated → pattern → sop → skill）
    staged = promote_experience_stage(db, str(entry.id))
    logger.debug("failure_experience: key=%s count=%d stage=%s", key, staged.occurrence_count, staged.stage)
    return staged


def _failure_key(task_type: str, executor_type: str, executor_id: str) -> str:
    return f"{task_type}:{executor_type}:{executor_id}"
