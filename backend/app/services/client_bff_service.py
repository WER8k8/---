# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""租户 Client 壳 BFF 聚合（T-ARCH-2）。"""

from __future__ import annotations

import json
import os
from typing import Any

from sqlalchemy.orm import Session

from app.models.content import PublishTask
from app.models.inquiry import Inquiry
from app.models.tenant import Tenant, UserTenant
from app.models.user import User
from app.services.bff_cache_service import bff_cache_key, cached_bff
from app.services.im_locale_service import list_supported_languages
from app.services.onboarding_chain_service import (
    build_chain_status,
    resolve_client_site_url,
)
from app.services.traffic_analytics_service import (
    TrafficAnalyticsService,
    resolve_tenant_id,
)


def resolve_tenant_for_user(db: Session, user: User) -> Tenant | None:
    """resolve_tenant_for_user。

    参数说明：
    :param db: 参数 db
    :param user: 参数 user
    :return: 返回处理结果。
    """
    link = (
        db.query(UserTenant)
        .filter(UserTenant.user_id == user.id, UserTenant.is_active.is_(True))
        .first()
    )
    if not link:
        if user.role in ("admin", "super_admin"):
            return None
        return None
    tenant = db.query(Tenant).filter(Tenant.id == link.tenant_id).first()
    if not tenant or not tenant.is_active:
        return None
    return tenant


def _parse_settings(raw: Any) -> dict[str, Any]:
    """_parse_settings。

    参数说明：
    :param raw: 参数 raw
    :return: 返回处理结果。
    """
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw) if isinstance(raw, str) else {}
    except json.JSONDecodeError:
        return {}


def _publish_queue_summary(db: Session, tenant_id: str) -> dict[str, int]:
    """_publish_queue_summary。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    base = db.query(PublishTask).filter(PublishTask.tenant_id == tenant_id)
    return {
        "pending": int(base.filter(PublishTask.status == "pending").count()),
        "processing": int(base.filter(PublishTask.status == "processing").count()),
        "failed": int(base.filter(PublishTask.status == "failed").count()),
    }


def build_client_bootstrap(db: Session, user: User) -> dict[str, Any]:
    """build_client_bootstrap。

    参数说明：
    :param db: 参数 db
    :param user: 参数 user
    :return: 返回处理结果。
    """
    tenant = resolve_tenant_for_user(db, user)
    tid = str(tenant.id) if tenant else resolve_tenant_id(db, user=user)
    cache_key = bff_cache_key("client", "bootstrap", tid or str(user.id))
    def _build() -> dict[str, Any]:
        """_build。
        :return: 返回处理结果。
        """
        traffic_summary: dict[str, Any] = {}
        top_clicks: list[dict[str, Any]] = []
        if tid:
            board = TrafficAnalyticsService(db).build_board(
                period="7d", tenant_id=tid, scope="tenant"
            )
            traffic_summary = board.get("summary") or {}
            top_clicks = (board.get("top_clicks") or [])[:5]

        inq_stats = {"pending": 0, "total": 0}
        publish_queue = {"pending": 0, "processing": 0, "failed": 0}
        if tid:
            base = db.query(Inquiry).filter(Inquiry.is_active, Inquiry.tenant_id == tid)
            inq_stats = {
                "total": base.count(),
                "pending": base.filter(Inquiry.status == "pending").count(),
            }
            publish_queue = _publish_queue_summary(db, tid)

        settings = _parse_settings(tenant.settings if tenant else None)
        onboarding = build_chain_status(tenant, db) if tenant else {"chain_step": "hermes"}
        return {
            "user": {
                "id": str(user.id),
                "username": user.username,
                "role": user.role,
            },
            "tenant": {
                "id": tid,
                "name": tenant.name if tenant else None,
                "domain": tenant.domain if tenant else None,
                "status": tenant.status if tenant else None,
            }
            if tenant
            else None,
            "site_url": resolve_client_site_url(tenant) if tenant else "",
            "inquiries": inq_stats,
            "publish_queue": publish_queue,
            "traffic": traffic_summary,
            "top_clicks": top_clicks,
            "im_languages": list_supported_languages(),
            "onboarding": {
                "chain_step": onboarding.get("chain_step"),
                "wizard_completed": onboarding.get("wizard_completed"),
                "site_built": onboarding.get("site_built"),
            },
            "app_shell": {
                "app_name": "出海计",
                "min_version": "1.0.0",
                "current_version": os.getenv("CHUHAIJI_APP_VERSION", "1.0.0"),
                "tabs": ["assistant", "today", "publish", "profile"],
            },
            "feature_flags": {
                "copilot_enabled": settings.get("copilot_enabled", True),
                "traffic_board": True,
                "unified_publish": True,
            },
            "api_hints": {
                "traffic_board": "/api/v1/analytics/traffic-board",
                "app_home": "/api/v1/app/v1/home",
                "im_resolve": "/api/v1/im-routing/channels",
                "dashboard": "/api/v1/client/dashboard",
            },
        }

    return cached_bff(cache_key, ttl_sec=60, builder=_build)
