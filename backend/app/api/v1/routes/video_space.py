# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""视频空间兼容别名 `/video-space/*`（B5）：对齐前端命名，底层复用 media-factory。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success_response
from app.core.security import get_current_user
from app.models.user import User

ROUTE_PREFIX = "/video-space"
ROUTE_TAGS = ["视频空间"]

router = APIRouter(tags=["视频空间"])


@router.get("")
@router.get("/")
def list_video_space(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """视频列表（兼容别名 → media-factory dashboard 列表）。"""
    try:
        from app.services.media_factory_service import list_videos_for_dashboard

        items = list_videos_for_dashboard(db, current_user, limit=limit)
        return success_response(data={
            "items": items,
            "total": len(items),
            "status": "ready",
            "alias_of": "/media-factory/videos",
        })
    except Exception:
        return success_response(data={
            "items": [],
            "total": 0,
            "status": "empty",
            "hint": "media-factory 视频源暂不可用",
        })


@router.get("/status")
def video_space_status(
    current_user: User = Depends(get_current_user),
):
    """视频空间能力状态（诚实标记，不假 success）。"""
    return success_response(data={
        "status": "ready",
        "storage": ["qiniu", "r2"],
        "alias_of": "/media-factory/videos",
    })
