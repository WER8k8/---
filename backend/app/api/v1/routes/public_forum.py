"""公开站 — 租户论坛嵌入配置（iframe）。"""

from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.cache import async_cache_decorator
from app.core.config import settings
from app.core.response import error_response, success_response
from app.db.session import get_db
from app.services.forum_sidecar_service import get_tenant_forum_config
from app.services.media_tenant_traffic_service import get_tenant_by_domain


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/public"

router = APIRouter(tags=["公开-论坛嵌入"])


@router.get("/tenants/{domain}/forum-embed")
@async_cache_decorator(expire=timedelta(minutes=10), key_prefix="forum:embed")
async def public_forum_embed(domain: str, db: Session = Depends(get_db)):
    """处理 GET /tenants/{domain}/forum-embed 请求，public相关资源。
    
    :param domain: 域名
    :param db: 数据库会话
    :return: 返回处理结果。
    """
    tenant = get_tenant_by_domain(db, domain)
    if not tenant:
        return error_response(404, "站点不存在")
    cfg = get_tenant_forum_config(tenant, api_base=settings.API_V1_PREFIX)
    if not cfg.get("enabled") or not cfg.get("iframe_src"):
        return success_response(
            data={"enabled": False, "iframe_src": None},
            message="租户未开启买家问答",
        )
    return success_response(
        data={
            "enabled": True,
            "iframe_src": cfg["iframe_src"],
            "title_zh": "买家问答",
            "title_en": "Buyer Q&A",
            "honest_note": cfg.get("honest_note"),
        }
    )
