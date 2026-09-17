# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""全球出海国家场景矩阵 API 路由。"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.response import error_response, success_response
from app.services.geo.geo_matrix_landing_service import GeoMatrixLandingService, COUNTRY_PROFILES

ROUTE_PREFIX = "/geo"
ROUTE_TAGS = ["出海国家场景矩阵"]

router = APIRouter(prefix="/geo", tags=["出海国家场景矩阵"])


def _resolve_base_url(request: Request) -> str:
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or ""
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme or "https"
    if host:
        return f"{proto}://{host}".rstrip("/")
    return getattr(settings, "SITE_URL", "https://www.youdingjiancai.com").rstrip("/")


@router.get("/solutions")
def list_country_solutions(db: Session = Depends(get_db)):
    """获取所有出海战区与国家场景列表。"""
    svc = GeoMatrixLandingService(db)
    countries = svc.list_supported_countries()
    return success_response(data=countries)


@router.get("/solutions/{country_code}")
def get_country_profile(country_code: str):
    """获取特定国家的出海工程痛点与港口档案。"""
    profile = COUNTRY_PROFILES.get(country_code.lower())
    if not profile:
        raise HTTPException(status_code=404, detail="Country profile not found")
    return success_response(data=profile)


@router.get("/solutions/{country_code}/{product_slug}")
def get_country_product_landing(
    country_code: str,
    product_slug: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """获取针对特定国家与产品的矩阵落地页全量数据包。"""
    base_url = _resolve_base_url(request)
    svc = GeoMatrixLandingService(db)
    bundle = svc.build_country_landing_bundle(country_code, product_slug, base_url=base_url)
    if not bundle:
        raise HTTPException(status_code=404, detail="Country landing page not found for this product")
    return success_response(data=bundle)
