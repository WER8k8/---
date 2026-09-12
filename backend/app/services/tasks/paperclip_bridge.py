"""Paperclip → ai_tasks 影子双写桥（总纲 §4.6-1 收编过渡第 2 迭代；轮24-B）。

与 deerflow_bridge 同构：把 PaperclipTask 生命周期（created→running→success/failed）
影子同步到统一任务控制面，不改变 Paperclip 任何既有行为：

- 开关：复用 `TASK_CONTROL_ENABLED`（默认关）——开关关时完全旁路，零回归。
- 幂等：ai_task 以 (tenant_id, idempotency_key="paperclip:{task_id}") 定位。
- 去重裁决：经 DeerFlow 执行的 PaperclipTask（provider=deerflow）不再由
  deerflow_bridge 重复影子——deerflow_bridge 检测 payload.context.paperclip=True
  时跳过，一次执行只产生一条 ai_task / 一条 Trace / 一条 Evolution 记录
  （执行归属记为 agent，executor_id=paperclip:{agent_id}）。
- 影子忠实映射：PaperclipTask 经 DeerFlow 执行但 job 失败时 Paperclip 自身仍会
  置 success（run_job 内部吞错返回结果 dict），影子按 PaperclipTask 状态映射，
  output_json 携带 result（内含 job status）供核查——不替源表"纠错"。
- 租户解析：company_id → PaperclipCompany.tenant_id，查不到降级用 company_id
  （与 heartbeat_engine._run_via_deerflow 的降级策略一致）。
- best-effort：任何异常吞掉并回滚，绝不阻断 Paperclip 主链路（红线 2）。

未接挂点（诚实清单）：blocked/cancelled 状态流转未接（delegate_task 的
blocked→queued 复活路径影子保持 executing 直到终态，轻微偏差已记录）。
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.services.tasks.task_control import (
    TaskControlService,
    side_effects_enabled,
)

logger = logging.getLogger("uj-admin.tasks.paperclip_bridge")

IDEMPOTENCY_PREFIX = "paperclip:"
SOURCE = "paperclip"


def idempotency_key_for(task_id: str) -> str:
    """PaperclipTask.id → ai_tasks.idempotency_key（稳定映射，供反查）。"""
    return f"{IDEMPOTENCY_PREFIX}{task_id}"


def resolve_tenant_id(db: Session, company_id: str) -> str:
    """company_id → tenant_id（查不到降级用 company_id，与心跳引擎策略一致）。"""
    try:
        from app.models.paperclip import PaperclipCompany

        company = (
            db.query(PaperclipCompany)
            .filter(PaperclipCompany.id == company_id)
            .first()
        )
        return str(company.tenant_id) if company and company.tenant_id else str(company_id)
    except Exception:  # noqa: BLE001 — 租户解析失败不阻断双写
        return str(company_id)


def _summary_of(value: Any, limit: int = 200) -> Optional[str]:
    if value is None:
        return None
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return text[:limit] or None


def _result_dict(task) -> Optional[dict[str, Any]]:
    try:
        return json.loads(task.result_json) if task.result_json else None
    except (json.JSONDecodeError, TypeError):
        return None


class PaperclipTaskBridge:
    """PaperclipTask → TaskControlService 影子双写（全部 best-effort）。"""

    def __init__(self, db: Session):
        self.db = db

    def _fire(self, label: str, fn) -> None:
        if not side_effects_enabled():
            return
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 — 双写故障绝不阻断 Paperclip
            logger.warning("paperclip_bridge: %s 失败（已忽略）: %s", label, exc)
            try:
                self.db.rollback()
            except Exception:  # noqa: BLE001
                pass

    def _control(self) -> TaskControlService:
        return TaskControlService(self.db)

    def on_task_created(self, task) -> None:
        """创建影子同步：PaperclipTask(queued) → ai_tasks(created)。"""
        def _sync() -> None:
            tenant_id = resolve_tenant_id(self.db, str(task.company_id))
            self._control().create_task(
                tenant_id=tenant_id,
                task_type=f"paperclip_{(task.intent or 'generic').strip() or 'generic'}",
                input_data={
                    "title": task.title,
                    "description": task.description,
                    "goal_id": str(task.goal_id) if task.goal_id else None,
                    "agent_id": str(task.assigned_agent_id) if task.assigned_agent_id else None,
                },
                idempotency_key=idempotency_key_for(str(task.id)),
                priority=int(task.priority or 0) + 3,  # paperclip 0 优最高，映射到 ai_tasks 5 档中段
                source=SOURCE,
                quota_gate=False,  # 影子写入不因配额拒绝而失败（与 deerflow_bridge 同裁决）
            )
        self._fire("create 双写", _sync)

    def on_task_running(self, task) -> None:
        """开始执行影子同步：PaperclipTask(running) → ai_tasks(executing)。"""
        def _sync() -> None:
            tenant_id = resolve_tenant_id(self.db, str(task.company_id))
            ctl = self._control()
            shadow = ctl.find_by_idempotency(
                tenant_id=tenant_id,
                idempotency_key=idempotency_key_for(str(task.id)),
            )
            if not shadow:
                # 影子缺失（如开关中途才开）先补建再启动，保证链路完整
                self.on_task_created(task)
                shadow = ctl.find_by_idempotency(
                    tenant_id=tenant_id,
                    idempotency_key=idempotency_key_for(str(task.id)),
                )
                if not shadow:
                    return
            agent_ref = (
                f"paperclip:{task.assigned_agent_id}"
                if task.assigned_agent_id
                else f"paperclip_task:{task.id}"
            )
            ctl.start_task(
                shadow.id,
                tenant_id=tenant_id,
                executor_type="agent",
                executor_id=agent_ref,
            )
        self._fire("running 双写", _sync)

    def on_task_finished(self, task, *, success: bool) -> None:
        """终态影子同步：success → done；failed → failed。"""
        def _sync() -> None:
            tenant_id = resolve_tenant_id(self.db, str(task.company_id))
            ctl = self._control()
            shadow = ctl.find_by_idempotency(
                tenant_id=tenant_id,
                idempotency_key=idempotency_key_for(str(task.id)),
            )
            if not shadow:
                return
            agent_ref = (
                f"paperclip:{task.assigned_agent_id}"
                if task.assigned_agent_id
                else f"paperclip_task:{task.id}"
            )
            if success:
                result = _result_dict(task)
                ctl.complete_task(
                    shadow.id,
                    tenant_id=tenant_id,
                    output_data=result,
                    output_summary=_summary_of(result) or _summary_of(task.title),
                    executor_type="agent",
                    executor_id=agent_ref,
                )
            else:
                error = ""
                try:
                    result = _result_dict(task) or {}
                    error = str(result.get("error") or "")
                except Exception:  # noqa: BLE001
                    pass
                ctl.fail_task(
                    shadow.id,
                    tenant_id=tenant_id,
                    error_code="PAPERCLIP_TASK_FAILED",
                    error_message=error or None,
                    executor_type="agent",
                    executor_id=agent_ref,
                )
        self._fire("finish 双写", _sync)
