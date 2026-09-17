# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Platform 超管壳 BFF — 首屏聚合（T-ARCH-2）。"""

from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.content import PublishTask
from app.models.inquiry import Inquiry
from app.models.tenant import Tenant
from app.models.user import User
from app.services.bff_cache_service import bff_cache_key, cached_bff
from app.services.tenant_service import TenantService


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/bff/platform", tags=["Platform BFF"])

_PLATFORM_ROLES = frozenset({"admin", "super_admin"})


@router.get("/overview")
def platform_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tab A 首屏：租户统计、队列、询盘待办（目标 <300ms）。"""
    if current_user.role not in _PLATFORM_ROLES:
        return error_response(403, "权限不足")

    key = bff_cache_key("platform", "overview", "global")
    def _build() -> dict:
        """执行 build 相关逻辑处理。
        :return: 返回处理结果。
        """
        overview = TenantService(db).get_overview()
        stats = overview.get("stats") or {}
        pending_inquiries = (
            db.query(func.count(Inquiry.id))
            .filter(Inquiry.is_active, Inquiry.status == "pending")
            .scalar()
        ) or 0
        publish_pending = (
            db.query(func.count(PublishTask.id))
            .filter(PublishTask.status.in_(("pending", "processing")))
            .scalar()
        ) or 0
        frozen_tenants = (
            db.query(func.count(Tenant.id))
            .filter(Tenant.is_active.is_(False))
            .scalar()
        ) or 0
        return {
            "tenant_stats": stats,
            "recent_tenants": [
                {
                    "id": str(t.id),
                    "name": t.name,
                    "domain": t.domain,
                    "status": t.status,
                }
                for t in (overview.get("recent_tenants") or [])[:5]
            ],
            "queues": {
                "pending_inquiries": int(pending_inquiries),
                "publish_in_progress": int(publish_pending),
            },
            "alerts": {
                "frozen_tenants": int(frozen_tenants),
            },
            "aitoearn": _build_aitoearn_admin_snapshot(),
            "backup": {
                "status": "unknown",
                "hint": "见 /api/v1/system-config/backup 或运维 cron",
            },
        }

    return success_response(data=cached_bff(key, ttl_sec=60, builder=_build))


def _build_aitoearn_admin_snapshot() -> dict:
    """执行 build_aitoearn_admin_snapshot 相关逻辑处理。
    :return: 返回处理结果。
    """
    from app.services.aitoearn_hub_service import build_aitoearn_capabilities
    cap = build_aitoearn_capabilities(tenant=None)
    return {
        "enabled": bool(cap.get("aitoearn_enabled")),
        "platform_count": int(cap.get("platform_count") or 0),
        "publish_available": bool((cap.get("modules") or {}).get("publish", {}).get("available")),
        "hint": (
            "已配置 Key，请在租户管理为各租户分配矩阵槽位"
            if cap.get("aitoearn_enabled")
            else "未配置 AITOEARN_API_KEY — Publish/Engage 不可用"
        ),
    }
