"""DeerFlow → ai_tasks 影子双写桥（总纲 §4.6-1 收编过渡；轮24-A 首批调用方）。

总纲裁决：ai_tasks 是任务真相源，DeerflowJob/PaperclipTask 双写过渡 2 个迭代后
降级为从表。本桥把 DeerflowJob 生命周期（enqueue→running→success/failed）影子
同步到统一任务控制面（TaskControlService），不改变 DeerflowJob 任何既有行为：

- 开关：复用 `TASK_CONTROL_ENABLED`（默认关）——开关关时本桥完全旁路，零回归。
- 幂等：ai_task 以 (tenant_id, idempotency_key="deerflow:{job_id}") 定位，
  重复同步返回既有任务，不重复建行。
- 预算门：影子写入传 quota_gate=False（DeerFlow 链路自有闸门，双写不得因
  配额拒绝而失败）。
- best-effort：任何异常吞掉并回滚，绝不阻断 DeerFlow 主链路（红线 2）。
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

logger = logging.getLogger("uj-admin.tasks.deerflow_bridge")

IDEMPOTENCY_PREFIX = "deerflow:"
SOURCE = "deerflow"


def idempotency_key_for(job_id: str) -> str:
    """DeerflowJob.id → ai_tasks.idempotency_key（稳定映射，供反查）。"""
    return f"{IDEMPOTENCY_PREFIX}{job_id}"


def _summary_of(value: Any, limit: int = 200) -> Optional[str]:
    if value is None:
        return None
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return text[:limit] or None


class DeerflowTaskBridge:
    """DeerflowJob → TaskControlService 影子双写（全部 best-effort）。"""

    def __init__(self, db: Session):
        self.db = db

    def _fire(self, label: str, fn) -> None:
        if not side_effects_enabled():
            return
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 — 双写故障绝不阻断 DeerFlow
            logger.warning("deerflow_bridge: %s 失败（已忽略）: %s", label, exc)
            try:
                self.db.rollback()
            except Exception:  # noqa: BLE001
                pass

    def _control(self) -> TaskControlService:
        return TaskControlService(self.db)

    def on_job_enqueued(self, job) -> None:
        """入队影子同步：DeerflowJob(queued) → ai_tasks(created)。

        轮24-B 去重裁决：Paperclip 心跳引擎代执行的任务（payload.context 带
        paperclip=True + task_id）由 paperclip_bridge 影子（一次执行只产生一条
        ai_task/Trace/Evolution 记录），此处跳过。
        """
        def _sync() -> None:
            payload = _payload_dict(job)
            ctx = payload.get("context") or {}
            if ctx.get("paperclip") and ctx.get("task_id"):
                logger.debug(
                    "deerflow_bridge: job %s 由 paperclip task %s 代执行，跳过影子"
                    "（归属见 paperclip:{task_id}）",
                    job.id, ctx.get("task_id"),
                )
                return
            self._control().create_task(
                tenant_id=str(job.tenant_id),
                task_type=f"deerflow_{job.intent}",
                input_data=payload,
                idempotency_key=idempotency_key_for(str(job.id)),
                source=SOURCE,
                created_by=str(job.created_by) if job.created_by else None,
                quota_gate=False,
            )
        self._fire("enqueue 双写", _sync)

    def on_job_started(self, job) -> None:
        """开始执行影子同步：DeerflowJob(running) → ai_tasks(executing)。"""
        def _sync() -> None:
            task = self._control().find_by_idempotency(
                tenant_id=str(job.tenant_id) if job.tenant_id else None,
                idempotency_key=idempotency_key_for(str(job.id)),
            )
            if not task:
                return
            self._control().start_task(
                task.id,
                tenant_id=str(job.tenant_id) if job.tenant_id else None,
                executor_type="workflow",
                executor_id=f"deerflow:{job.intent}",
            )
        self._fire("start 双写", _sync)

    def on_job_finished(self, job, *, success: bool) -> None:
        """终态影子同步：success → done；failed → failed。"""
        def _sync() -> None:
            ctl = self._control()
            task = ctl.find_by_idempotency(
                tenant_id=str(job.tenant_id) if job.tenant_id else None,
                idempotency_key=idempotency_key_for(str(job.id)),
            )
            if not task:
                return
            if success:
                result = _result_dict(job)
                ctl.complete_task(
                    task.id,
                    tenant_id=str(job.tenant_id) if job.tenant_id else None,
                    output_data=result,
                    output_summary=_summary_of(result),
                    executor_type="workflow",
                    executor_id=f"deerflow:{job.intent}",
                )
            else:
                ctl.fail_task(
                    task.id,
                    tenant_id=str(job.tenant_id) if job.tenant_id else None,
                    error_code="DEERFLOW_JOB_FAILED",
                    error_message=str(job.error_message or "")[:1000] or None,
                    executor_type="workflow",
                    executor_id=f"deerflow:{job.intent}",
                )
        self._fire("finish 双写", _sync)


def _payload_dict(job) -> dict[str, Any]:
    try:
        return json.loads(job.payload_json or "{}")
    except (json.JSONDecodeError, TypeError):
        return {}


def _result_dict(job) -> Optional[dict[str, Any]]:
    try:
        return json.loads(job.result_json) if job.result_json else None
    except (json.JSONDecodeError, TypeError):
        return None
