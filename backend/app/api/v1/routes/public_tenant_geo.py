# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""公开 API — 租户 llms.txt / GEO 统一评分 / AI 搜索探针。"""

from datetime import timedelta

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.core.cache import async_cache_decorator
from app.core.response import error_response, success_response
from app.db.session import get_db
from app.services.media_tenant_traffic_service import get_tenant_by_domain
from app.services.tenant_llms_txt_service import build_tenant_llms_txt
from app.services.unified_geo_score_service import build_unified_geo_score


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/public"

router = APIRouter(tags=["公开-租户GEO"])


@router.get("/tenants/{domain}/llms.txt", response_class=PlainTextResponse)
async def tenant_llms_txt(
    domain: str,
    language: str = Query("en", min_length=2, max_length=5),
    db: Session = Depends(get_db),
):
    """处理 GET /tenants/{domain}/llms.txt 请求，tenant相关资源。
    
    :param domain: 域名
    :param language: 参数 language
    :param db: 数据库会话
    :return: 返回处理结果。
    """
    tenant = get_tenant_by_domain(db, domain)
    if not tenant:
        return PlainTextResponse("Tenant not found\n", status_code=404)
    body = build_tenant_llms_txt(tenant, full=False, language=language)
    return PlainTextResponse(body, media_type="text/plain; charset=utf-8")


@router.get("/tenants/{domain}/llms-full.txt", response_class=PlainTextResponse)
async def tenant_llms_full_txt(
    domain: str,
    language: str = Query("en", min_length=2, max_length=5),
    db: Session = Depends(get_db),
):
    """处理 GET /tenants/{domain}/llms-full.txt 请求，tenant相关资源。
    
    :param domain: 域名
    :param language: 参数 language
    :param db: 数据库会话
    :return: 返回处理结果。
    """
    tenant = get_tenant_by_domain(db, domain)
    if not tenant:
        return PlainTextResponse("Tenant not found\n", status_code=404)
    body = build_tenant_llms_txt(tenant, full=True, language=language)
    return PlainTextResponse(body, media_type="text/plain; charset=utf-8")


@router.get("/tenants/{domain}/geo-score")
@async_cache_decorator(expire=timedelta(minutes=10), key_prefix="geo:score")
async def tenant_geo_score(
    domain: str,
    include_probes: bool = Query(True, description="是否调用 LLM/AI Search 探针（需 Key）"),
    db: Session = Depends(get_db),
):
    """处理 GET /tenants/{domain}/geo-score 请求，tenant相关资源。
    
    :param domain: 域名
    :param include_probes: 参数 include_probes
    :param db: 数据库会话
    :return: 返回处理结果。
    """
    tenant = get_tenant_by_domain(db, domain)
    if not tenant:
        return error_response(404, "站点不存在")
    payload = await build_unified_geo_score(db, domain=domain, include_probes=include_probes)
    return success_response(data=payload)


@router.get("/tenants/{domain}/ai-search-probes")
@async_cache_decorator(expire=timedelta(minutes=30), key_prefix="geo:probes")
async def tenant_ai_search_probes(
    domain: str,
    keyword: str | None = Query(None, max_length=120),
    db: Session = Depends(get_db),
):
    """处理 GET /tenants/{domain}/ai-search-probes 请求，tenant相关资源。
    
    :param domain: 域名
    :param keyword: 参数 keyword
    :param db: 数据库会话
    :return: 返回处理结果。
    """
    from app.services.ai_search_probe_service import run_ai_search_probes
    from app.services.tenant_product_context import resolve_tenant_product_hint
    tenant = get_tenant_by_domain(db, domain)
    if not tenant:
        return error_response(404, "站点不存在")
    brand = tenant.name or domain
    settings_raw = tenant.settings or "{}"
    try:
        import json
        settings = json.loads(settings_raw)
        brand = (settings.get("brand") or {}).get("company_name") or brand
    except (json.JSONDecodeError, TypeError, Exception):
        pass
    data = await run_ai_search_probes(keyword=kw, brand_name=str(brand), product_category=kw)
    return success_response(data=data)
