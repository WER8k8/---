"""DeerFlow 执行引擎 Celery 任务。

提供 DeerFlow 任务的异步执行能力，与状态机协作完成完整的任务生命周期。
"""

from __future__ import annotations

import logging

from celery import shared_task
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="execute_deerflow_job",
    max_retries=2,
    default_retry_delay=60,
    queue="deerflow",
)
def execute_deerflow_job(self, job_id: str) -> dict:
    """异步执行 DeerFlow 任务。

    完整的执行流程：
    1. 加载任务，状态 EXECUTING
    2. 加载执行规划
    3. 逐个执行子任务
    4. 审核执行结果
    5. 根据审核结论转移状态

    Args:
        job_id: DeerFlow 任务 ID

    Returns:
        执行结果摘要
    """
    from app.core.database import SessionLocal
    from app.models.deerflow_job import DeerflowJob
    from app.services.deerflow.checkpoint import Checkpoint, CheckpointManager
    from app.services.deerflow.executor import SubTaskExecutionError, SubTaskExecutor
    from app.services.deerflow.planner import TaskPlanner
    from app.services.deerflow.reviewer import ResultReviewer, ReviewDecision
    from app.services.deerflow.state_machine import DeerFlowJobNotFoundError, DeerFlowStateMachine, DeerFlowStatus
    db = SessionLocal()
    try:
        return _execute_deerflow_core(db, job_id)
    except DeerFlowJobNotFoundError:
        logger.error("DeerFlow job not found: %s", job_id)
        return {"status": "error", "message": "任务不存在"}
    except SQLAlchemyError as db_exc:
        logger.exception("DeerFlow job DB error: job=%s", job_id)
        raise self.retry(exc=db_exc) from db_exc
    except Exception as exc:
        logger.exception("DeerFlow job unexpected error: job=%s", job_id)
        # 尝试标记失败
        try:
            job = db.query(DeerflowJob).filter(DeerflowJob.id == job_id).first()
            if job:
                machine = DeerFlowStateMachine(db, job_id)
                machine.fail(error=str(exc)[:500])
        except Exception:
            pass
        raise self.retry(exc=exc) from exc
    finally:
        db.close()


def _execute_deerflow_core(db, job_id: str) -> dict:
    """DeerFlow 任务核心执行流程（不含 DB 会话生命周期与重试）。"""
    from app.core.database import SessionLocal
    from app.models.deerflow_job import DeerflowJob
    from app.services.deerflow.checkpoint import Checkpoint, CheckpointManager
    from app.services.deerflow.executor import SubTaskExecutionError, SubTaskExecutor
    from app.services.deerflow.planner import TaskPlanner
    from app.services.deerflow.reviewer import ResultReviewer, ReviewDecision
    from app.services.deerflow.state_machine import DeerFlowJobNotFoundError, DeerFlowStateMachine, DeerFlowStatus
    # 1. 加载任务
    job = db.query(DeerflowJob).filter(DeerflowJob.id == job_id).first()
    if not job:
        logger.error("DeerFlow job not found: %s", job_id)
        return {"status": "error", "message": "任务不存在"}

    machine = DeerFlowStateMachine(db, job_id)
    planner = TaskPlanner(db)
    checkpoint_mgr = CheckpointManager(db, job)
    # 2. 加载执行计划
    plan = planner.load_plan(job)
    if not plan:
        logger.warning("No plan found for job %s, creating default", job_id)
        plan = planner.create_plan(job)
        planner.save_plan(job, plan)

    # 3. 检查恢复点
    if checkpoint_mgr.can_resume():
        batch_idx, subtask_idx = checkpoint_mgr.get_resume_point()
        pending_ids = checkpoint_mgr.get_pending_subtasks()
        logger.info(
            "Resuming job %s from batch=%d index=%d, pending=%d",
            job_id, batch_idx, subtask_idx, len(pending_ids),
        )

    # 4. 执行子任务
    executor = SubTaskExecutor(db, job)
    try:
        results = executor.execute_plan(plan)
    except SubTaskExecutionError as exec_err:
        # 子任务执行失败，进入 FAILED
        machine.fail(error=f"子任务 {exec_err.subtask_id} 失败: {str(exec_err)[:200]}")
        logger.error("DeerFlow job execution failed: job=%s error=%s", job_id, exec_err)
        return {
            "status": "failed",
            "job_id": job_id,
            "error": str(exec_err),
            "subtask_id": exec_err.subtask_id,
        }

    # 5. 执行完成，进入 REVIEW
    machine.finish_executing()
    # 6. 审核结果
    reviewer = ResultReviewer(db, job)
    review_result = reviewer.review(results)
    # 7. 根据审核决策转移状态
    if review_result.decision == ReviewDecision.APPROVED:
        machine.approve()
        logger.info("DeerFlow job approved: job=%s score=%.2f", job_id, review_result.score)
        return {
            "status": "done",
            "job_id": job_id,
            "review_score": review_result.score,
            "subtasks_completed": len(results),
        }
    elif review_result.decision == ReviewDecision.WAIT_HUMAN:
        machine.wait_for_human(reason="; ".join(review_result.reasons[:3]))
        logger.info("DeerFlow job waiting for human: job=%s", job_id)
        return {
            "status": "wait_human",
            "job_id": job_id,
            "review_score": review_result.score,
            "reasons": review_result.reasons,
        }
    else:
        # REJECTED -> 打回重做
        machine.reject(reason="; ".join(review_result.reasons[:3]))
        logger.info("DeerFlow job rejected: job=%s score=%.2f", job_id, review_result.score)
        return {
            "status": "rejected",
            "job_id": job_id,
            "review_score": review_result.score,
            "reasons": review_result.reasons,
            "suggestions": review_result.suggestions,
        }


@shared_task(
    bind=True,
    name="deerflow_periodic_cleanup",
    max_retries=1,
    default_retry_delay=300,
)
def deerflow_periodic_cleanup(self, days: int = 30) -> dict:
    """定期清理已完成的 DeerFlow 任务 checkpoint 快照。

    Args:
        days: 清理多少天前的已完成任务快照
    """
    from datetime import timedelta
    from app.core.database import SessionLocal
    from app.models.deerflow_job import DeerflowJob
    from app.services.deerflow.checkpoint import CheckpointManager
    from app.services.deerflow.state_machine import DeerFlowStatus
    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        completed_jobs = (
            db.query(DeerflowJob)
            .filter(
                DeerFlowJob.status.in_([DeerFlowStatus.DONE.value, DeerFlowStatus.CANCELLED.value]),
                DeerflowJob.updated_at < cutoff,
            )
            .limit(100)
            .all()
        )
        cleaned = 0
        for job in completed_jobs:
            try:
                mgr = CheckpointManager(db, job)
                mgr.cleanup_old_snapshots(keep=1)
                cleaned += 1
            except Exception:
                pass

        return {"cleaned": cleaned, "total": len(completed_jobs)}
    except Exception:
        logger.exception("deerflow_periodic_cleanup error")
        return {"cleaned": 0, "error": "cleanup_failed"}
    finally:
        db.close()


# 避免循环导入
from datetime import datetime, timezone  # noqa: E402
