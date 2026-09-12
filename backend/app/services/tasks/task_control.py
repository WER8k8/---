"""统一任务控制面服务（总纲 §4.6-1/§4.6-2 / §8 082；轮23 任务端接线）。

把 ai_tasks → task_traces → terminal_hook(evolution) → meter_events 接成一条真实链路：
- 状态机：11 态（与迁移 082 / app.models.ai_task.TASK_STATUSES 严格一致），
  非法转移抛 InvalidTaskTransition；终态不可再转移（红线）；
  重试 ≤3 次，超限只能转 wait_human（§4.8/R6）。
- 幂等：create 按 (tenant_id, idempotency_key) 去重（并发唯一键冲突回读）；
  complete 的计量埋点按 event_key=task:{id}:ai_generation 幂等。
- 预算门：AI 类任务（task_type 以 "ai_" 开头，或显式 quota_gate=True）create 时
  走 plan_gate_service.evaluate_ai_quota（只读判定，不改租户状态）。
- 副作用（Trace / 终态钩子 / 计量）一律 best-effort：TASK_CONTROL_ENABLED 默认关，
  开关关或副作用异常均回滚不阻断核心状态机（红线 2：零回归）。
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.ai_task import AiTask
from app.services.billing.meter_event import MeterEventService
from app.services.trace.terminal_hook import record_terminal_state
from app.services.trace.trace_service import TaskTraceService

logger = logging.getLogger("uj-admin.tasks")

# ── 状态常量（与 app.models.ai_task.TASK_STATUSES 逐项对应）──────────
CREATED = "created"
PLANNING = "planning"
EXECUTING = "executing"
REVIEW = "review"
PAUSED = "paused"
RETRYING = "retrying"
WAIT_HUMAN = "wait_human"
DONE = "done"
FAILED = "failed"
CANCELLED = "cancelled"
TIMEOUT = "timeout"

# 主链：created→(planning)→executing→(review)→done
# 支路：任意活动态可转 failed/cancelled/timeout；paused 可恢复；wait_human 人工介入；
# retrying 有界（≤3，超限只能转 wait_human）；终态（done/failed/cancelled/timeout）为空集。
TRANSITIONS: dict[str, frozenset[str]] = {
    CREATED: frozenset({PLANNING, EXECUTING, CANCELLED, FAILED, TIMEOUT}),
    PLANNING: frozenset(
        {EXECUTING, PAUSED, WAIT_HUMAN, RETRYING, CANCELLED, FAILED, TIMEOUT}
    ),
    EXECUTING: frozenset(
        {REVIEW, DONE, PAUSED, WAIT_HUMAN, RETRYING, CANCELLED, FAILED, TIMEOUT}
    ),
    REVIEW: frozenset({DONE, PAUSED, WAIT_HUMAN, CANCELLED, FAILED}),
    PAUSED: frozenset({EXECUTING, CANCELLED, FAILED, TIMEOUT}),
    RETRYING: frozenset({EXECUTING, WAIT_HUMAN, CANCELLED, FAILED, TIMEOUT}),
    WAIT_HUMAN: frozenset({EXECUTING, PAUSED, RETRYING, CANCELLED, FAILED}),
    DONE: frozenset(),
    FAILED: frozenset(),
    CANCELLED: frozenset(),
    TIMEOUT: frozenset(),
}

MAX_RETRY = 3  # §4.8/R6：有界重试

# AI 类任务前缀（create 时自动过预算门；显式传 quota_gate 可覆盖）
AI_TASK_TYPE_PREFIXES = ("ai_",)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def can_transition(current: str, target: str) -> bool:
    """状态机合法性判定（纯函数，供测试与外部复用）。"""
    if current not in TRANSITIONS:
        return False
    return target in TRANSITIONS[current]


def side_effects_enabled() -> bool:
    """TASK_CONTROL_ENABLED（默认关）：只控制副作用（Trace/Meter/Hook），不控制状态机。"""
    try:
        from app.core.config import settings  # noqa: PLC0415

        return bool(getattr(settings, "TASK_CONTROL_ENABLED", False))
    except Exception:  # noqa: BLE001
        return False


class TaskControlError(Exception):
    """任务控制面异常基类。"""


class TaskNotFound(TaskControlError):
    def __init__(self, task_id: str, tenant_id: Optional[str] = None):
        self.task_id = task_id
        self.tenant_id = tenant_id
        super().__init__(
            f"task_not_found: {task_id}"
            + (f" (tenant={tenant_id})" if tenant_id else "")
        )


class InvalidTaskTransition(TaskControlError):
    """非法状态转移（含越权重试）。"""

    def __init__(self, current: str, target: str, reason: str = ""):
        self.current = current
        self.target = target
        super().__init__(
            f"非法转移 {current} -> {target}" + (f"（{reason}）" if reason else "")
        )


class QuotaGateDenied(TaskControlError):
    """预算门拒绝（plan_gate_service 判定不允许）。"""

    def __init__(self, verdict: dict[str, Any]):
        self.verdict = verdict
        super().__init__(f"quota_gate_denied: {verdict}")


class TaskControlService:
    """统一任务控制面：ai_tasks 生命周期 + Trace/终态钩子/计量副作用接线。"""

    def __init__(self, db: Session):
        self.db = db

    # ──────────────────────────────────────────────
    # 查询
    # ──────────────────────────────────────────────
    def get_task(
        self, task_id: str, *, tenant_id: Optional[str] = None
    ) -> Optional[AiTask]:
        q = self.db.query(AiTask).filter(AiTask.id == task_id)
        if tenant_id is not None:
            q = q.filter(AiTask.tenant_id == tenant_id)
        return q.first()

    def find_by_idempotency(
        self,
        *,
        idempotency_key: str,
        tenant_id: Optional[str] = None,
    ) -> Optional[AiTask]:
        """按幂等键反查任务（影子双写定位用；tenant_id 已知时必须带隔离）。"""
        q = self.db.query(AiTask).filter(AiTask.idempotency_key == idempotency_key)
        if tenant_id is not None:
            q = q.filter(AiTask.tenant_id == tenant_id)
        return q.first()

    # ──────────────────────────────────────────────
    # 创建（幂等 + 预算门）
    # ──────────────────────────────────────────────
    def create_task(
        self,
        *,
        tenant_id: str,
        task_type: str,
        input_data: Optional[dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        priority: int = 5,
        budget_limit: Optional[float] = None,
        parent_task_id: Optional[str] = None,
        throttle_key: Optional[str] = None,
        source: Optional[str] = None,
        created_by: Optional[str] = None,
        quota_gate: Optional[bool] = None,
        tenant: Optional[Any] = None,
    ) -> AiTask:
        """创建任务（status=created）。

        - 幂等：(tenant_id, idempotency_key) 已存在时直接返回既有任务，不重复建。
        - 预算门：quota_gate 为 None 时按 task_type 前缀自动判定（ai_* → 过门）；
          判定走 plan_gate_service.evaluate_ai_quota（只读），拒绝抛 QuotaGateDenied。
        """
        if idempotency_key:
            existing = (
                self.db.query(AiTask)
                .filter(
                    AiTask.tenant_id == tenant_id,
                    AiTask.idempotency_key == idempotency_key,
                )
                .first()
            )
            if existing:
                return existing
        if quota_gate is None:
            quota_gate = task_type.startswith(AI_TASK_TYPE_PREFIXES)
        if quota_gate:
            self._check_quota(tenant_id, tenant)

        task = AiTask(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            parent_task_id=parent_task_id,
            task_type=task_type,
            status=CREATED,
            priority=priority,
            input_json=(
                json.dumps(input_data, ensure_ascii=False) if input_data else None
            ),
            idempotency_key=idempotency_key,
            budget_limit=budget_limit,
            throttle_key=throttle_key,
            source=source,
            created_by=created_by,
        )
        self.db.add(task)
        try:
            self.db.commit()
        except IntegrityError:
            # 并发重复 (tenant_id, idempotency_key)：回滚并回读既有任务
            self.db.rollback()
            if idempotency_key:
                existing = (
                    self.db.query(AiTask)
                    .filter(
                        AiTask.tenant_id == tenant_id,
                        AiTask.idempotency_key == idempotency_key,
                    )
                    .first()
                )
                if existing:
                    return existing
            raise
        self.db.refresh(task)
        self._emit_event("task.created", task)
        return task

    # ──────────────────────────────────────────────
    # 生命周期
    # ──────────────────────────────────────────────
    def start_task(
        self,
        task_id: str,
        *,
        tenant_id: Optional[str] = None,
        executor_type: str = "skill",
        executor_id: Optional[str] = None,
        skill_id: Optional[str] = None,
        skill_version: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> AiTask:
        """created/planning → executing；开 TaskTrace（副作用，best-effort）。"""
        task = self._require(task_id, tenant_id)
        self._apply(task, EXECUTING)
        if not task.started_at:
            task.started_at = _utcnow()
        self.db.commit()
        self.db.refresh(task)

        def _open_trace() -> None:
            svc = TaskTraceService(self.db)
            trace = svc.start_trace(
                tenant_id=task.tenant_id,
                trace_type=task.task_type,
                source_id=executor_id or task.source,
                task_id=task.id,
                skill_id=skill_id,
                skill_version=skill_version,
                model_name=model_name,
                input_summary=(task.input_json or "")[:200] or None,
                metadata={"executor_type": executor_type, "task_control": True},
            )
            task.trace_id = trace.id
            self.db.commit()

        self._fire("start 开 Trace", _open_trace)
        self._emit_event("task.resumed", task) # start counts as resumed/started
        self.db.refresh(task)
        return task

    def complete_task(
        self,
        task_id: str,
        *,
        tenant_id: Optional[str] = None,
        output_data: Optional[dict[str, Any]] = None,
        output_summary: Optional[str] = None,
        tokens_used: int = 0,
        cost: float = 0.0,
        duration_ms: int = 0,
        skill_id: Optional[str] = None,
        skill_version: Optional[str] = None,
        model_name: Optional[str] = None,
        executor_type: str = "skill",
        executor_id: Optional[str] = None,
    ) -> AiTask:
        """executing/review → done；关 Trace + ai_generation 计量 + 终态钩子（副作用）。"""
        task = self._require(task_id, tenant_id)
        self._apply(task, DONE)
        task.finished_at = _utcnow()
        if output_data is not None:
            task.output_json = json.dumps(output_data, ensure_ascii=False)
        if cost:
            task.budget_used = float(task.budget_used or 0) + float(cost)
        self.db.commit()
        self.db.refresh(task)

        def _effects() -> None:
            if task.trace_id:
                TaskTraceService(self.db).complete_trace(
                    task.trace_id,
                    output_summary=output_summary,
                    duration_ms=duration_ms,
                    cost=cost,
                    tokens_used=tokens_used,
                )
            if tokens_used or cost:
                MeterEventService(self.db).emit_ai_generation(
                    tenant_id=task.tenant_id,
                    event_key=f"task:{task.id}:ai_generation",
                    token_delta=tokens_used,
                    cost_cents=int(round(float(cost) * 100)),
                    model_name=model_name,
                    source_ref_id=task.id,
                    metadata={"task_type": task.task_type, "source": task.source},
                )
            record_terminal_state(
                self.db,
                task_type=task.task_type,
                executor_type=executor_type,
                executor_id=executor_id or skill_id or task.source or str(task.id),
                success=True,
                tenant_id=task.tenant_id,
                duration_ms=duration_ms,
                cost=cost,
                tokens_used=tokens_used,
                trace_id=task.trace_id,
                skill_id=skill_id,
                skill_version=skill_version,
                model_name=model_name,
                input_summary=(task.input_json or "")[:200] or None,
                output_summary=output_summary,
            )

        self._fire("complete 副作用", _effects)
        self._emit_event("task.completed", task,
                         tokens_used=tokens_used, cost=cost,
                         duration_ms=duration_ms, model_name=model_name)
        self.db.refresh(task)
        return task

    def fail_task(
        self,
        task_id: str,
        *,
        tenant_id: Optional[str] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        duration_ms: int = 0,
        cost: float = 0.0,
        skill_id: Optional[str] = None,
        skill_version: Optional[str] = None,
        model_name: Optional[str] = None,
        executor_type: str = "skill",
        executor_id: Optional[str] = None,
    ) -> AiTask:
        """活动态 → failed；Trace 失败 + 终态钩子（失败经验快速入库，副作用）。"""
        task = self._require(task_id, tenant_id)
        self._apply(task, FAILED)
        task.finished_at = _utcnow()
        task.error_message = (error_message or "")[:2000] or None
        if cost:
            task.budget_used = float(task.budget_used or 0) + float(cost)
        self.db.commit()
        self.db.refresh(task)

        def _effects() -> None:
            if task.trace_id:
                TaskTraceService(self.db).fail_trace(
                    task.trace_id,
                    error_code=error_code,
                    error_message=error_message,
                    duration_ms=duration_ms,
                    cost=cost,
                )
            record_terminal_state(
                self.db,
                task_type=task.task_type,
                executor_type=executor_type,
                executor_id=executor_id or skill_id or task.source or str(task.id),
                success=False,
                tenant_id=task.tenant_id,
                duration_ms=duration_ms,
                cost=cost,
                error_code=error_code,
                error_message=error_message,
                trace_id=task.trace_id,
                skill_id=skill_id,
                skill_version=skill_version,
                model_name=model_name,
                input_summary=(task.input_json or "")[:200] or None,
            )

        self._fire("fail 副作用", _effects)
        self._emit_event("task.failed", task,
                         error_code=error_code, error_message=error_message,
                         duration_ms=duration_ms)
        self.db.refresh(task)
        return task

    def pause_task(self, task_id: str, *, tenant_id: Optional[str] = None) -> AiTask:
        """活动态 → paused（planning/executing/review/wait_human 合法）。"""
        task = self._require(task_id, tenant_id)
        self._apply(task, PAUSED)
        self.db.commit()
        self._emit_event("task.paused", task)
        self.db.refresh(task)
        return task

    def resume_task(self, task_id: str, *, tenant_id: Optional[str] = None) -> AiTask:
        """paused/wait_human → executing（恢复执行 / 人工放行）。"""
        task = self._require(task_id, tenant_id)
        self._apply(task, EXECUTING)
        self.db.commit()
        self._emit_event("task.resumed", task)
        self.db.refresh(task)
        return task

    def cancel_task(self, task_id: str, *, tenant_id: Optional[str] = None) -> AiTask:
        """非终态 → cancelled。"""
        task = self._require(task_id, tenant_id)
        self._apply(task, CANCELLED)
        task.finished_at = _utcnow()
        self.db.commit()
        self._emit_event("task.cancelled", task)
        self.db.refresh(task)
        return task

    def timeout_task(self, task_id: str, *, tenant_id: Optional[str] = None) -> AiTask:
        """非终态 → timeout（租约到期驱动）。"""
        task = self._require(task_id, tenant_id)
        self._apply(task, TIMEOUT)
        task.finished_at = _utcnow()
        self.db.commit()
        self._emit_event("task.timeout", task)
        self.db.refresh(task)
        return task

    def review_task(self, task_id: str, *, tenant_id: Optional[str] = None) -> AiTask:
        """executing → review（进入人审）。"""
        task = self._require(task_id, tenant_id)
        self._apply(task, REVIEW)
        self.db.commit()
        # review not explicitly added in events, skip for now or use task.paused? Just normal commit.
        self.db.refresh(task)
        return task

    def plan_task(self, task_id: str, *, tenant_id: Optional[str] = None) -> AiTask:
        """created → planning（规划阶段）。"""
        task = self._require(task_id, tenant_id)
        self._apply(task, PLANNING)
        self.db.commit()
        self.db.refresh(task)
        return task

    def retry_task(self, task_id: str, *, tenant_id: Optional[str] = None) -> AiTask:
        """→ retrying（有界：≤MAX_RETRY 次，超限抛异常并提示转 wait_human）。"""
        task = self._require(task_id, tenant_id)
        self._apply(task, RETRYING)
        self.db.commit()
        self._emit_event("task.retried", task)
        self.db.refresh(task)
        return task

    # ──────────────────────────────────────────────
    # checkpoint（长任务可恢复，§4.6-1）
    # ──────────────────────────────────────────────
    def save_checkpoint(
        self,
        task_id: str,
        checkpoint: dict[str, Any],
        *,
        tenant_id: Optional[str] = None,
    ) -> AiTask:
        task = self._require(task_id, tenant_id)
        task.checkpoint_json = json.dumps(checkpoint, ensure_ascii=False)
        self.db.commit()
        self.db.refresh(task)
        return task

    def load_checkpoint(
        self, task_id: str, *, tenant_id: Optional[str] = None
    ) -> Optional[dict[str, Any]]:
        task = self._require(task_id, tenant_id)
        if not task.checkpoint_json:
            return None
        return json.loads(task.checkpoint_json)

    # ──────────────────────────────────────────────
    # 内部
    # ──────────────────────────────────────────────
    def _require(self, task_id: str, tenant_id: Optional[str] = None) -> AiTask:
        task = self.get_task(task_id, tenant_id=tenant_id)
        if not task:
            raise TaskNotFound(task_id, tenant_id)
        return task

    def _apply(self, task: AiTask, target: str) -> None:
        """校验并落位状态转移（含终态冻结与有界重试红线）。"""
        current = task.status or CREATED
        if current not in TRANSITIONS:
            raise InvalidTaskTransition(current, target, "未知状态")
        if target not in TRANSITIONS[current]:
            raise InvalidTaskTransition(current, target)
        if target == RETRYING:
            if (task.retry_count or 0) >= MAX_RETRY:
                raise InvalidTaskTransition(
                    current, target,
                    f"重试已达上限 {MAX_RETRY} 次，必须转 wait_human",
                )
            task.retry_count = (task.retry_count or 0) + 1
        task.status = target

    def _fire(self, label: str, fn: Callable[[], Any]) -> Any:
        """副作用执行器：TASK_CONTROL_ENABLED 关闭时跳过；异常回滚不阻断主链路。"""
        if not side_effects_enabled():
            return None
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            logger.warning("task_control: %s 失败（已忽略，不影响主链路）: %s", label, exc)
            try:
                self.db.rollback()
            except Exception:  # noqa: BLE001
                pass
            return None

    def _emit_event(self, event_type: str, task: AiTask, **extra: Any) -> None:
        """通过事件总线广播任务状态变更事件（best-effort，不阻断主流程）。"""
        try:
            from app.core.event_bus import Event, event_bus  # noqa: PLC0415

            payload = {
                "task_id": str(task.id),
                "task_type": task.task_type,
                "status": task.status,
                "tenant_id": str(task.tenant_id) if task.tenant_id else "",
                **extra,
            }
            event = Event(
                event_type=event_type,
                data=payload,
                tenant_id=str(task.tenant_id) if task.tenant_id else "",
                trace_id=task.trace_id or "",
            )
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(event_bus.emit(event))
            except RuntimeError:
                # 没有运行中的事件循环，使用 emit_sync
                event_bus.emit_sync(event)
        except Exception as exc:  # noqa: BLE001
            logger.debug("task_control: 事件发射 '%s' 失败（已忽略）: %s", event_type, exc)

    def _check_quota(self, tenant_id: str, tenant: Optional[Any]) -> dict[str, Any]:
        """AI 配额预算门（plan_gate_service.evaluate_ai_quota，只读）。"""
        from app.services.plan_gate_service import evaluate_ai_quota  # noqa: PLC0415

        if tenant is None:
            tenant = self._load_tenant(tenant_id)
        verdict = evaluate_ai_quota(tenant)
        if not verdict.get("allowed"):
            raise QuotaGateDenied(verdict)
        return verdict

    def _load_tenant(self, tenant_id: str) -> Optional[Any]:
        """从库加载 Tenant；加载失败按无租户处理（evaluate_ai_quota(None) 安全拒绝）。"""
        try:
            from app.models.tenant import Tenant  # noqa: PLC0415

            return (
                self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
            )
        except Exception:  # noqa: BLE001
            return None
