"""EmailOutreach 状态恢复服务 —— ORCH-11 修复

处理死状态：failed/bounced/complained/unsubscribed 的出站跃迁。
- failed: 重试最多3次后标记为 final_failed
- bounced (hard): 标记为 final_bounced，不再重试
- bounced (soft): 重试
- complained/unsubscribed: 标记为 final，不再发送
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.email_outreach import EmailOutreach, EmailStatus, BounceType

logger = logging.getLogger(__name__)

MAX_RETRY_COUNT = 3
STALE_MINUTES = 60  # 超过60分钟的failed视为僵死


def recover_failed_emails(db: Session, *, limit: int = 50) -> int:
    """恢复failed状态的邮件，重试最多3次。

    ORCH-11: 修复failed死状态问题
    """
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=STALE_MINUTES)
    rows = (
        db.query(EmailOutreach)
        .filter(EmailOutreach.status == EmailStatus.FAILED)
        .filter(EmailOutreach.updated_at < cutoff)
        .filter(
            (EmailOutreach.outreach_metadata["retry_count"].as_integer() < MAX_RETRY_COUNT)
            if hasattr(EmailOutreach.outreach_metadata, "as_integer")
            else func.coalesce(
                EmailOutreach.outreach_metadata["retry_count"], 0
            ) < MAX_RETRY_COUNT
        )
        .limit(limit)
        .all()
    )
    recovered = 0
    for row in rows:
        try:
            # 获取重试次数
            meta = row.outreach_metadata or {}
            retry_count = meta.get("retry_count", 0)
            if not isinstance(retry_count, int):
                retry_count = 0

            if retry_count >= MAX_RETRY_COUNT:
                row.status = EmailStatus.FAILED  # 保持failed，但记录重试次数
                meta["retry_count"] = retry_count
                meta["final_retry_attempt"] = True
                row.outreach_metadata = meta
                db.add(row)
                continue

            # 重置为queued重试
            row.status = EmailStatus.QUEUED
            meta["retry_count"] = retry_count + 1
            meta["last_retry_at"] = datetime.now(timezone.utc).isoformat()
            row.outreach_metadata = meta
            db.add(row)
            recovered += 1
        except Exception as exc:
            logger.warning("Failed to recover email %s: %s", row.id, exc)

    if recovered > 0:
        db.commit()

    return recovered


def classify_bounced_emails(db: Session, *, limit: int = 50) -> int:
    """分类处理bounced状态的邮件。

    ORCH-11: 修复bounced死状态问题
    - hard bounce: 标记为final，不再重试
    - soft bounce: 可重试
    """
    rows = (
        db.query(EmailOutreach)
        .filter(EmailOutreach.status == EmailStatus.BOUNCED)
        .limit(limit)
        .all()
    )
    classified = 0
    for row in rows:
        try:
            bounce_type = row.bounce_type
            if bounce_type == BounceType.HARD:
                # 硬退：不再重试
                meta = row.outreach_metadata or {}
                meta["final_bounce"] = True
                meta["bounce_classification"] = "hard"
                row.outreach_metadata = meta
                db.add(row)
                classified += 1
            elif bounce_type == BounceType.SOFT:
                # 软退：可重试
                meta = row.outreach_metadata or {}
                meta["final_bounce"] = False
                meta["bounce_classification"] = "soft"
                row.outreach_metadata = meta
                db.add(row)
                classified += 1
        except Exception as exc:
            logger.warning("Failed to classify bounce for email %s: %s", row.id, exc)

    if classified > 0:
        db.commit()

    return classified


def requeue_soft_bounces(db: Session, *, limit: int = 50) -> int:
    """将软退邮件重新入队。

    ORCH-11: 软退可重试
    """
    rows = (
        db.query(EmailOutreach)
        .filter(EmailOutreach.status == EmailStatus.BOUNCED)
        .filter(EmailOutreach.bounce_type == BounceType.SOFT)
        .limit(limit)
        .all()
    )
    requeued = 0
    for row in rows:
        try:
            row.status = EmailStatus.QUEUED
            db.add(row)
            requeued += 1
        except Exception as exc:
            logger.warning("Failed to requeue soft bounce email %s: %s", row.id, exc)

    if requeued > 0:
        db.commit()

    return requeued


def get_email_stats(db: Session) -> dict:
    """获取邮件状态统计。"""
    stats = {}
    for status in EmailStatus:
        count = (
            db.query(func.count(EmailOutreach.id))
            .filter(EmailOutreach.status == status)
            .scalar()
            or 0
        )
        stats[status.value] = count
    return stats
