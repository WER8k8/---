"""DeerFlow 执行引擎状态机核心。

定义任务生命周期状态、转移规则和转移逻辑。
使用数据库事务保证状态转移的一致性。

状态流转图：
    CREATED -> PLANNING -> EXECUTING -> REVIEW -> WAIT_HUMAN -> DONE
                                |                        |
                            FAILED -> RETRY -------------
                                |
                            CANCELLED
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.deerflow_job import DeerflowJob

logger = logging.getLogger(__name__)


class DeerFlowStatus(str, Enum):
    """DeerFlow 任务状态枚举。"""
    CREATED = "created"
    PLANNING = "planning"
    EXECUTING = "executing"
    REVIEW = "review"
    WAIT_HUMAN = "wait_human"
    DONE = "done"
    FAILED = "failed"
    RETRY = "retry"
    CANCELLED = "cancelled"


# ---------------------------------------------------------------------------
# 状态转移表：定义哪些状态可以转移到哪些状态
# ---------------------------------------------------------------------------

_TRANSITIONS: dict[DeerFlowStatus, set[DeerFlowStatus]] = {
    DeerFlowStatus.CREATED: {DeerFlowStatus.PLANNING, DeerFlowStatus.CANCELLED},
    DeerFlowStatus.PLANNING: {DeerFlowStatus.EXECUTING, DeerFlowStatus.FAILED, DeerFlowStatus.CANCELLED},
    DeerFlowStatus.EXECUTING: {DeerFlowStatus.REVIEW, DeerFlowStatus.FAILED, DeerFlowStatus.CANCELLED},
    DeerFlowStatus.REVIEW: {DeerFlowStatus.DONE, DeerFlowStatus.WAIT_HUMAN, DeerFlowStatus.EXECUTING, DeerFlowStatus.CANCELLED},
    DeerFlowStatus.WAIT_HUMAN: {DeerFlowStatus.DONE, DeerFlowStatus.CANCELLED},
    DeerFlowStatus.FAILED: {DeerFlowStatus.RETRY, DeerFlowStatus.CANCELLED},
    DeerFlowStatus.RETRY: {DeerFlowStatus.EXECUTING, DeerFlowStatus.CANCELLED},
    DeerFlowStatus.DONE: set(),  # 终态
    DeerFlowStatus.CANCELLED: set(),  # 终态
}


# ---------------------------------------------------------------------------
# 转移结果
# ---------------------------------------------------------------------------

@dataclass
class TransitionResult:
    """状态转移结果。"""
    success: bool
    from_status: DeerFlowStatus
    to_status: DeerFlowStatus
    message: str = ""
    job_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    def to_dict(self) -> dict[str, Any]:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "success": self.success,
            "from_status": self.from_status.value,
            "to_status": self.to_status.value,
            "message": self.message,
            "job_id": self.job_id,
            "timestamp": self.timestamp,
        }


# ---------------------------------------------------------------------------
# 状态机核心
# ---------------------------------------------------------------------------

class DeerFlowStateMachine:
    """DeerFlow 任务状态机。

    管理单个 DeerFlow 任务的状态生命周期，提供：
    - 状态转移验证（基于 _TRANSITIONS 表）
    - 数据库事务保证一致性
    - 转移前/后钩子（可扩展）
    - 重试计数与上限控制
    """
    def __init__(
        self,
        db: Session,
        job_id: str,
        max_retries: int = 3,
        on_transition: Optional[Callable[[DeerFlowStatus, DeerFlowStatus, DeerflowJob], None]] = None,
    ):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :param job_id: 参数 job_id
        :param max_retries: 参数 max_retries
        :param on_transition: 参数 on_transition
        :return: 返回处理结果。
        """
        self.db = db
        self.job_id = job_id
        self.max_retries = max_retries
        self.on_transition = on_transition

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------
    def get_status(self) -> DeerFlowStatus:
        """获取当前任务状态。"""
        job = self._get_job()
        return DeerFlowStatus(job.status)

    def can_transition(self, to_status: DeerFlowStatus) -> bool:
        """检查是否可以转移到目标状态。"""
        job = self._get_job()
        current = DeerFlowStatus(job.status)
        return to_status in _TRANSITIONS.get(current, set())

    def transition(
        self,
        to_status: DeerFlowStatus,
        *,
        message: str = "",
        extra_fields: Optional[dict[str, Any]] = None,
    ) -> TransitionResult:
        """执行状态转移。

        在数据库事务中完成状态更新，保证一致性。
        如果转移非法，返回失败结果而不抛异常。

        Args:
            to_status: 目标状态
            message: 转移附注信息
            extra_fields: 额外需要更新的字段（如 error_message, result_json 等）

        Returns:
            TransferResult 描述转移结果
        """
        job = self._get_job()
        from_status = DeerFlowStatus(job.status)
        # 验证转移合法性
        if to_status not in _TRANSITIONS.get(from_status, set()):
            logger.warning(
                "Illegal transition: job=%s from=%s to=%s",
                self.job_id, from_status.value, to_status.value,
            )
            return TransitionResult(
                success=False,
                from_status=from_status,
                to_status=to_status,
                message=f"非法状态转移: {from_status.value} -> {to_status.value}",
                job_id=self.job_id,
            )

        # 重试上限检查
        if to_status == DeerFlowStatus.RETRY:
            retry_count = (job.retry_count or 0) + 1
            if retry_count > self.max_retries:
                logger.warning(
                    "Retry limit exceeded: job=%s retry_count=%d max=%d",
                    self.job_id, retry_count, self.max_retries,
                )
                # 自动转为 CANCELLED
                return self._do_transition(
                    DeerFlowStatus.CANCELLED,
                    from_status=from_status,
                    message=f"超过最大重试次数 ({self.max_retries})，自动取消",
                    extra_fields={"retry_count": retry_count},
                )

        return self._do_transition(
            to_status,
            from_status=from_status,
            message=message,
            extra_fields=extra_fields,
        )

    # ------------------------------------------------------------------
    # 便捷方法：语义化转移
    # ------------------------------------------------------------------
    def start_planning(self) -> TransitionResult:
        """CREATED -> PLANNING: 开始规划。"""
        return self.transition(DeerFlowStatus.PLANNING, message="开始任务规划")

    def finish_planning(self) -> TransitionResult:
        """PLANNING -> EXECUTING: 规划完成，开始执行。"""
        return self.transition(DeerFlowStatus.EXECUTING, message="规划完成，开始执行")

    def finish_executing(self) -> TransitionResult:
        """EXECUTING -> REVIEW: 执行完成，进入审核。"""
        return self.transition(DeerFlowStatus.REVIEW, message="执行完成，进入审核")

    def fail(self, error: str = "") -> TransitionResult:
        """EXECUTING -> FAILED: 执行失败。"""
        return self.transition(
            DeerFlowStatus.FAILED,
            message=f"执行失败: {error}" if error else "执行失败",
            extra_fields={"error_message": error},
        )

    def approve(self) -> TransitionResult:
        """REVIEW -> DONE: 审核通过。"""
        return self.transition(DeerFlowStatus.DONE, message="审核通过")

    def reject(self, reason: str = "") -> TransitionResult:
        """REVIEW -> EXECUTING: 审核打回重做。"""
        return self.transition(
            DeerFlowStatus.EXECUTING,
            message=f"审核打回重做: {reason}" if reason else "审核打回重做",
        )

    def wait_for_human(self, reason: str = "") -> TransitionResult:
        """REVIEW -> WAIT_HUMAN: 需要人工确认。"""
        return self.transition(
            DeerFlowStatus.WAIT_HUMAN,
            message=f"等待人工确认: {reason}" if reason else "等待人工确认",
        )

    def human_approve(self) -> TransitionResult:
        """WAIT_HUMAN -> DONE: 人工确认通过。"""
        return self.transition(DeerFlowStatus.DONE, message="人工确认通过")

    def human_cancel(self) -> TransitionResult:
        """WAIT_HUMAN -> CANCELLED: 人工取消。"""
        return self.transition(DeerFlowStatus.CANCELLED, message="人工取消")

    def trigger_retry(self) -> TransitionResult:
        """FAILED -> RETRY: 触发重试。"""
        job = self._get_job()
        retry_count = (job.retry_count or 0) + 1
        return self.transition(
            DeerFlowStatus.RETRY,
            message=f"触发第 {retry_count} 次重试",
            extra_fields={"retry_count": retry_count},
        )

    def retry_execute(self) -> TransitionResult:
        """RETRY -> EXECUTING: 重试执行。"""
        return self.transition(DeerFlowStatus.EXECUTING, message="重试执行")

    def cancel(self) -> TransitionResult:
        """取消任务（从任意非终态）。"""
        job = self._get_job()
        current = DeerFlowStatus(job.status)
        return self.transition(DeerFlowStatus.CANCELLED, message="任务已取消")

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------
    def _get_job(self) -> DeerflowJob:
        """获取任务记录（带锁）。"""
        job = (
            self.db.query(DeerflowJob)
            .filter(DeerflowJob.id == self.job_id)
            .with_for_update()
            .first()
        )
        if not job:
            raise DeerFlowJobNotFoundError(f"DeerFlow job not found: {self.job_id}")
        return job

    def _do_transition(
        self,
        to_status: DeerFlowStatus,
        *,
        from_status: DeerFlowStatus,
        message: str = "",
        extra_fields: Optional[dict[str, Any]] = None,
    ) -> TransitionResult:
        """在数据库事务中执行状态更新。"""
        try:
            job = self._get_job()
            # 更新状态
            job.status = to_status.value
            job.updated_at = datetime.now(timezone.utc)
            # 设置时间戳
            if to_status == DeerFlowStatus.EXECUTING and not job.started_at:
                job.started_at = datetime.now(timezone.utc)
            if to_status in (DeerFlowStatus.DONE, DeerFlowStatus.CANCELLED):
                job.finished_at = datetime.now(timezone.utc)

            # 更新重试计数
            if extra_fields and "retry_count" in extra_fields:
                job.retry_count = extra_fields["retry_count"]

            # 更新错误信息
            if extra_fields and "error_message" in extra_fields:
                job.error_message = extra_fields["error_message"]

            # 追加日志
            log_entry = f"[{datetime.now(timezone.utc).isoformat()}] {from_status.value} -> {to_status.value}: {message}"
            if job.log_text:
                job.log_text = job.log_text + "\n" + log_entry
            else:
                job.log_text = log_entry

            # 提交事务
            self.db.commit()
            self.db.refresh(job)
            logger.info(
                "State transition: job=%s %s -> %s (%s)",
                self.job_id, from_status.value, to_status.value, message,
            )
            # 执行钩子
            if self.on_transition:
                try:
                    self.on_transition(from_status, to_status, job)
                except Exception as hook_exc:
                    logger.warning(
                        "Transition hook error: job=%s exc=%s",
                        self.job_id, hook_exc,
                    )

            return TransitionResult(
                success=True,
                from_status=from_status,
                to_status=to_status,
                message=message,
                job_id=self.job_id,
            )

        except SQLAlchemyError as db_exc:
            self.db.rollback()
            logger.exception(
                "State transition DB error: job=%s from=%s to=%s",
                self.job_id, from_status.value, to_status.value,
            )
            return TransitionResult(
                success=False,
                from_status=from_status,
                to_status=to_status,
                message=f"数据库错误: {str(db_exc)[:200]}",
                job_id=self.job_id,
            )


# ---------------------------------------------------------------------------
# 异常
# ---------------------------------------------------------------------------

class DeerFlowStateMachineError(Exception):
    """状态机基础异常。"""

class DeerFlowJobNotFoundError(DeerFlowStateMachineError):
    """任务不存在异常。"""
