# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""谷歌 Search Console 真值回收 API — 生成式引擎（AI Overviews/Discovery）曝光。"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.models.user import User
from app.services.google_search_console_service import GSCService

ROUTE_PREFIX = ""
ROUTE_TAGS = ["谷歌SearchConsole"]
router = APIRouter()


@router.get("/gsc/status")
async def gsc_status(current_user: User = Depends(get_current_user)):
    """GSC 凭证是否已配置（未配置时 get_performance 走 no_fake_delivery 门控）。"""
    return success_response(
        data={
            "configured": GSCService.configured(),
            "has_api_key": bool(GSCService._api_key()),
        },
    )


@router.get("/gsc/performance")
async def gsc_performance(
    site_url: str = Query(..., description="已关联 GSC 的站点（如 example.com）"),
    days: int = Query(28, ge=1, le=90),
    keyword: Optional[str] = Query(None, description="可选：统计该关键词在 GSC query 维度下的命中行数"),
    current_user: User = Depends(get_current_user),
):
    """回收 Performance 真值（含 AI Overviews / Discovery 曝光，未提供专用维度时如实置 0）。"""
    result = await GSCService.get_performance(site_url, days, keyword=keyword)
    if not result["success"]:
        return error_response(503, result.get("message", "GSC 回收失败"))
    return success_response(data=result["data"], message=result.get("message"))
