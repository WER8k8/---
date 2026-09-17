# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""ScheduledPublish 重试服务 —— ORCH-12 修复

处理死状态：failed/dispatched 的出站跃迁。
- failed: 重试最多 max_attempts 次
- dispatched: 检查是否超时，超时则重置为 pending
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.nurture_cycle import ScheduledPublish

logger = logging.getLogger(__name__)

STALE_DISPATCHED_MINUTES = 30  # dispatched超过30分钟视为超时


def retry_failed_publishes(db: Session, *, limit: int = 50) -> int:
    """重试failed状态的定时发布任务。

    ORCH-12: 修复failed死状态问题
    """
    rows = (
        db.query(ScheduledPublish)
        .filter(ScheduledPublish.status == "failed")
        .filter(ScheduledPublish.attempts < ScheduledPublish.max_attempts)
        .order_by(ScheduledPublish.created_at.asc())
        .limit(limit)
        .all()
    )
    retried = 0
    for row in rows:
        try:
            row.status = "pending"
            row.attempts += 1
            row.error_message = None
            db.add(row)
            retried += 1
        except Exception as exc:
            logger.warning("Failed to retry publish %s: %s", row.id, exc)

    if retried > 0:
        db.commit()

    return retried


def recover_stale_dispatched(db: Session, *, limit: int = 50) -> int:
    """恢复超时dispatched状态的定时发布任务。

    ORCH-12: 修复dispatched死状态问题
    """
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=STALE_DISPATCHED_MINUTES)
    rows = (
        db.query(ScheduledPublish)
        .filter(ScheduledPublish.status == "dispatched")
        .filter(ScheduledPublish.dispatched_at < cutoff)
        .limit(limit)
        .all()
    )
    recovered = 0
    for row in rows:
        try:
            row.status = "pending"
            row.error_message = (row.error_message or "")[:400] + " [stale recovered]"
            db.add(row)
            recovered += 1
        except Exception as exc:
            logger.warning("Failed to recover stale dispatched publish %s: %s", row.id, exc)

    if recovered > 0:
        db.commit()

    return recovered


def get_publish_stats(db: Session) -> dict:
    """获取定时发布状态统计。"""
    stats = {}
    for status in ["pending", "dispatched", "published", "failed", "cancelled"]:
        count = (
            db.query(func.count(ScheduledPublish.id))
            .filter(ScheduledPublish.status == status)
            .scalar()
            or 0
        )
        stats[status] = count
    return stats
