"""租户端 BFF — 首屏聚合（T-ARCH-2）。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.client_bff_service import build_client_bootstrap, resolve_tenant_for_user


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/bff/client", tags=["租户端BFF"])


@router.get("/bootstrap")
def client_bootstrap(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """首屏聚合：用户、租户、询盘/发布摘要、流量、开通步骤（≤3 类核心请求合一）。"""
    if current_user.role not in ("admin", "super_admin"):
        tenant = resolve_tenant_for_user(db, current_user)
        if tenant is None:
            return error_response(403, "未关联租户")

    data = build_client_bootstrap(db, current_user)
    return success_response(data=data)


@router.get("/dashboard")
def client_dashboard_bff(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """四支柱卡片轻量聚合（缓存 45s）。"""
    from app.services.bff_cache_service import bff_cache_key, cached_bff
    from app.services.client_bff_service import resolve_tenant_for_user
    tenant = resolve_tenant_for_user(db, current_user)
    if not tenant:
        return error_response(403, "未关联租户")
    tid = str(tenant.id)
    key = bff_cache_key("client", "dashboard", tid)
    def _build() -> dict[str, Any]:
        """
        处理 _build 相关业务逻辑。

        :return: 返回 dict[str, Any] 类型的结果。
        """
        boot = build_client_bootstrap(db, current_user)
        return {
            "tenant_id": tid,
            "inquiries": boot.get("inquiries") or {},
            "publish_queue": boot.get("publish_queue") or {},
            "traffic": boot.get("traffic") or {},
            "onboarding": boot.get("onboarding") or {},
            "site_url": boot.get("site_url") or "",
        }

    return success_response(data=cached_bff(key, ttl_sec=45, builder=_build))
