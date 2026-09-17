# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Google Merchant Center (GMC) Product Feed API 路由。"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.services.marketing.gmc_feed_service import GmcFeedService

ROUTE_PREFIX = "/marketing"
ROUTE_TAGS = ["谷歌营销中心(GMC)"]

router = APIRouter(prefix="/marketing", tags=["谷歌营销中心(GMC)"])


def _resolve_base_url(request: Request) -> str:
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or ""
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme or "https"
    if host:
        return f"{proto}://{host}".rstrip("/")
    return getattr(settings, "SITE_URL", "https://www.youdingjiancai.com").rstrip("/")


@router.get("/gmc-feed.xml")
async def get_gmc_feed(
    request: Request,
    tenant_id: Optional[str] = Query(None, description="租户ID过滤，支持多租户独立站 GMC 专属 Feed"),
    db: Session = Depends(get_db),
):
    """返回符合 Google Merchant Center 规范的标准 RSS 2.0 XML 商品数据流。"""
    base_url = _resolve_base_url(request)
    service = GmcFeedService(db)
    xml_content = service.generate_feed_xml(base_url, tenant_id=tenant_id)

    return Response(
        content=xml_content,
        media_type="application/xml; charset=utf-8",
        headers={"Cache-Control": "public, max-age=3600, s-maxage=7200"},
    )
