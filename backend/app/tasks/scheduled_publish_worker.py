# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""定时发布调度器 — 借鉴 AiToEarn enqueue-publishing-task scheduler。

定期扫描 scheduled_publishes 表中 pending 状态且到达发布时间的任务，
调用 video_publish_orchestrator 执行发布。
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.logging import get_logger

logger = get_logger(__name__)


async def dispatch_pending_scheduled_publishes() -> dict[str, Any]:
    """扫描并执行到期的定时发布任务。"""
    from app.services.social_nurture_service import get_pending_scheduled, mark_scheduled_dispatched, mark_scheduled_result
    from app.services.video_publish_orchestrator import publish_platform_video
    db: Session = SessionLocal()
    dispatched = 0
    succeeded = 0
    failed = 0
    try:
        pending = get_pending_scheduled(db, limit=20)
        for item in pending:
            scheduled_id = item["id"]
            platform_name = item["platform_name"]
            title = item["title"]
            logger.info("dispatching scheduled publish %s to %s: %s", scheduled_id, platform_name, title[:50])
            # 幂等抢占：仅当任务仍为 pending 时才执行发布，防止并发重复发布
            if not mark_scheduled_dispatched(db, scheduled_id=scheduled_id):
                logger.warning(
                    "scheduled publish %s was already claimed by another worker, skipping",
                    scheduled_id,
                )
                continue

            try:
                result = await publish_platform_video(
                    platform_name=platform_name,
                    video_url=item.get("video_url") or "",
                    cover_url=item.get("cover_url") or "",
                    title=title,
                    body=item.get("body") or "",
                    tags=None,
                    tenant_id=item.get("tenant_id"),
                )
                dispatched += 1
                if result.get("success"):
                    mark_scheduled_result(
                        db,
                        scheduled_id=scheduled_id,
                        success=True,
                        published_url=result.get("platform_post_url"),
                        published_post_id=result.get("platform_post_id"),
                        worker_chain=result.get("attempts"),
                    )
                    succeeded += 1
                else:
                    mark_scheduled_result(
                        db,
                        scheduled_id=scheduled_id,
                        success=False,
                        error_message=result.get("error_message", "unknown"),
                        worker_chain=result.get("attempts"),
                    )
                    failed += 1

            except Exception as exc:
                logger.error("scheduled publish %s failed: %s", scheduled_id, exc)
                mark_scheduled_result(
                    db,
                    scheduled_id=scheduled_id,
                    success=False,
                    error_message=str(exc)[:500],
                )
                failed += 1

    finally:
        db.close()

    return {
        "dispatched": dispatched,
        "succeeded": succeeded,
        "failed": failed,
    }


async def auto_advance_all_nurture_cycles() -> dict[str, Any]:
    """自动升级所有 warming 状态的养号周期。"""
    from app.models.nurture_cycle import NurtureCycle as NurtureCycleModel
    from app.services.social_nurture_service import auto_advance
    db: Session = SessionLocal()
    advanced = 0
    checked = 0
    try:
        warming_cycles = (
            db.query(NurtureCycleModel)
            .filter(NurtureCycleModel.status == "warming")
            .all()
        )
        checked = len(warming_cycles)
        for cycle in warming_cycles:
            result = auto_advance(db, cycle_id=str(cycle.id))
            if result and result.get("status") == "active":
                advanced += 1
    finally:
        db.close()

    return {"checked": checked, "advanced": advanced}


async def run_nurture_engagement_worker() -> dict[str, Any]:
    """执行养号互动任务（点赞/评论/关注）。"""
    from app.services.nurture_execution_worker import execute_pending_engagements
    return await execute_pending_engagements(limit=30)
