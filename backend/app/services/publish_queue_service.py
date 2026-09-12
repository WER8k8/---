"""发布队列生产化：统计、僵死恢复、失败重试。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.content import PublishTask

STALE_PROCESSING_MINUTES = 30


def recover_stale_processing(db: Session) -> int:
    """将超时仍 processing 的任务退回 pending。"""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=STALE_PROCESSING_MINUTES)
    rows = (
        db.query(PublishTask)
        .filter(
            PublishTask.status == "processing",
            PublishTask.updated_at < cutoff,
        )
        .all()
    )
    for row in rows:
        row.status = "pending"
        row.error_message = (row.error_message or "")[:400] + " [stale recovered]"
    if rows:
        db.commit()
    return len(rows)


def requeue_retryable_failed(db: Session, *, limit: int = 50) -> int:
    """失败且未达 max_retries 的任务重新入队。"""
    rows = (
        db.query(PublishTask)
        .filter(PublishTask.status == "failed")
        .filter(PublishTask.retry_count < PublishTask.max_retries)
        .order_by(PublishTask.updated_at.asc())
        .limit(limit)
        .all()
    )
    for row in rows:
        row.status = "pending"
        row.error_message = None
    if rows:
        db.commit()
    return len(rows)


def queue_stats(db: Session) -> dict[str, int]:
    """队列深度统计。"""
    now = datetime.now(timezone.utc)
    pending = (
        db.query(func.count(PublishTask.id))
        .filter(
            PublishTask.status == "pending",
            (PublishTask.scheduled_time.is_(None))
            | (PublishTask.scheduled_time <= now),
        )
        .scalar()
        or 0
    )
    processing = (
        db.query(func.count(PublishTask.id))
        .filter(PublishTask.status == "processing")
        .scalar()
        or 0
    )
    failed = (
        db.query(func.count(PublishTask.id))
        .filter(PublishTask.status == "failed")
        .scalar()
        or 0
    )
    success = (
        db.query(func.count(PublishTask.id))
        .filter(PublishTask.status == "success")
        .scalar()
        or 0
    )
    scheduled_future = (
        db.query(func.count(PublishTask.id))
        .filter(
            PublishTask.status == "pending",
            PublishTask.scheduled_time.isnot(None),
            PublishTask.scheduled_time > now,
        )
        .scalar()
        or 0
    )
    return {
        "pending": int(pending),
        "processing": int(processing),
        "failed": int(failed),
        "success": int(success),
        "scheduled_future": int(scheduled_future),
    }
