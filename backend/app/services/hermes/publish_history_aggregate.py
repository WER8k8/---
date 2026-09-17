# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""超管统一发布历史：SEO 图文 + 视频矩阵。"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import Session

from app.models.content import PublishTask
from app.models.media_factory import MediaRenderTask

logger = logging.getLogger(__name__)


def list_unified_publish_history(
    db: Session,
    *,
    limit: int = 30,
) -> dict[str, Any]:
    """list_unified_publish_history。

    参数说明：
    :param db: 参数 db
    :param limit: 参数 limit
    :return: 返回处理结果。
    """
    seo_rows: list[PublishTask] = []
    video_rows: list[MediaRenderTask] = []
    try:
        seo_rows = (
            db.query(PublishTask)
            .filter(PublishTask.published_url.isnot(None))
            .order_by(PublishTask.updated_at.desc())
            .limit(limit)
            .all()
        )
    except (OperationalError, ProgrammingError) as exc:
        logger.warning("publish_tasks schema not ready: %s", exc)
        db.rollback()
    try:
        video_rows = (
            db.query(MediaRenderTask)
            .order_by(MediaRenderTask.updated_at.desc())
            .limit(limit)
            .all()
        )
    except (OperationalError, ProgrammingError) as exc:
        logger.warning("media_render_tasks query failed: %s", exc)
        db.rollback()

    items: list[dict[str, Any]] = []
    for t in seo_rows:
        title = getattr(t, "title", None) or t.published_url or ""
        items.append(
            {
                "channel": "seo_matrix",
                "id": str(t.id),
                "title": title[:120],
                "status": t.status,
                "url": t.published_url,
                "platform": getattr(t, "platform_id", None),
                "updated_at": t.updated_at.isoformat() if t.updated_at else None,
            }
        )
    for v in video_rows:
        items.append(
            {
                "channel": "video_matrix",
                "id": str(v.id),
                "title": (v.title or v.task_type or "视频任务")[:120],
                "status": v.status,
                "url": v.result_url or v.cloud_play_url or v.edited_result_url,
                "platform": v.task_type,
                "updated_at": v.updated_at.isoformat() if v.updated_at else None,
            }
        )

    items.sort(key=lambda x: x.get("updated_at") or "", reverse=True)
    return {"items": items[:limit], "total": len(items[:limit])}
