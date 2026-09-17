# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""租户官网公开视频页（SEO/GEO 收录，无需登录）。"""

from datetime import timedelta

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.cache import async_cache_decorator
from app.core.response import error_response, success_response
from app.db.session import get_db
from app.services.media_tenant_traffic_service import (
    build_videos_sitemap_xml,
    get_tenant_by_domain,
    list_public_videos_for_tenant,
    public_video_page_payload,
)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/public"

router = APIRouter(tags=["公开-租户视频"])


@router.get("/tenants/{domain}/videos")
@async_cache_decorator(expire=timedelta(minutes=10), key_prefix="media:videos")
async def list_tenant_videos(domain: str, db: Session = Depends(get_db)):
    """租户站点视频列表（首页「视频中心」区块）。"""
    tenant = get_tenant_by_domain(db, domain)
    if not tenant:
        return error_response(404, "站点不存在")
    items = list_public_videos_for_tenant(db, tenant)
    return success_response(
        data={
            "tenant_domain": tenant.domain,
            "videos": items,
            "count": len(items),
        }
    )


@router.get("/tenants/{domain}/videos/{task_id}")
@async_cache_decorator(expire=timedelta(minutes=10), key_prefix="media:video")
async def get_tenant_video_page(domain: str, task_id: str, db: Session = Depends(get_db)):
    """单条视频落地页数据（VideoObject + GEO 要点 + 询盘 CTA）。"""
    tenant = get_tenant_by_domain(db, domain)
    if not tenant:
        return error_response(404, "站点不存在")
    payload = public_video_page_payload(db, tenant, task_id)
    if not payload:
        return error_response(404, "视频不存在或未发布")
    return success_response(data=payload)


@router.get("/tenants/{domain}/videos-sitemap.xml")
def tenant_videos_sitemap(domain: str, db: Session = Depends(get_db)):
    """视频 Sitemap（利于搜索引擎发现租户视频页）。"""
    tenant = get_tenant_by_domain(db, domain)
    if not tenant:
        return Response(content="", media_type="application/xml", status_code=404)
    videos = list_public_videos_for_tenant(db, tenant, limit=500)
    xml = build_videos_sitemap_xml(tenant, videos)
    return Response(content=xml, media_type="application/xml")
