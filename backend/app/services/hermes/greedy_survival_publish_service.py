# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""摸金校尉 L4 审核通过 → ContentMaster + PublishTask 真发。"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.content_master import ContentMaster
from app.models.tenant import Tenant
from app.services.hermes.greedy_avatar_constitution import assert_greedy_action

logger = logging.getLogger("uj-admin.greedy_survival_publish")

# 逻辑渠道 → 矩阵平台名（platform_rank_registry 同源）
_CHANNEL_PLATFORMS_CN: dict[str, list[str]] = {
    "website_embed": ["微信公众号", "知乎"],
    "independent_landing": ["微信公众号", "1688"],
    "linkedin_carousel": ["LinkedIn"],
    "linkedin_video": ["LinkedIn"],
    "email_nurture": ["微信公众号"],
    "enterprise_outbound_attachment": ["LinkedIn", "Alibaba.com"],
}

_CHANNEL_PLATFORMS_GLOBAL: dict[str, list[str]] = {
    "website_embed": ["LinkedIn", "Alibaba.com"],
    "independent_landing": ["LinkedIn", "Alibaba.com"],
    "linkedin_carousel": ["LinkedIn"],
    "linkedin_video": ["LinkedIn"],
    "email_nurture": ["LinkedIn"],
    "enterprise_outbound_attachment": ["LinkedIn", "Alibaba.com"],
}


def channels_to_platform_names(channels: list[str] | None, *, locale: str = "global") -> list[str]:
    """channels_to_platform_names。

    参数说明：
    :param channels: 参数 channels
    :param locale: 参数 locale
    :return: 返回处理结果。
    """
    locale_key = "cn" if str(locale or "").lower().startswith("zh") else "global"
    mapping = _CHANNEL_PLATFORMS_CN if locale_key == "cn" else _CHANNEL_PLATFORMS_GLOBAL
    names: list[str] = []
    for ch in channels or []:
        for plat in mapping.get(str(ch), []):
            if plat not in names:
                names.append(plat)
    if not names:
        from app.services.ubrain.matrix_publish_service import default_platform_names
        names = default_platform_names(locale=locale, limit=3)
    return names[:8]


def resolve_greedy_publish_tenant_id(db: Session) -> str | None:
    """resolve_greedy_publish_tenant_id。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    configured = (getattr(settings, "HERMES_GREEDY_PUBLISH_TENANT_ID", None) or "").strip()
    if configured:
        exists = db.query(Tenant.id).filter(Tenant.id == configured, Tenant.is_active.is_(True)).first()
        return configured if exists else None
    from app.services.hermes.greedy_production_readiness_service import resolve_bootstrap_tenant_id_from_store
    cached = resolve_bootstrap_tenant_id_from_store()
    if cached and db.query(Tenant.id).filter(Tenant.id == cached, Tenant.is_active.is_(True)).first():
        return cached
    row = (
        db.query(Tenant)
        .filter(Tenant.domain == "platform-survival.ops", Tenant.is_active.is_(True))
        .first()
    )
    if row:
        return str(row.id)
    row = (
        db.query(Tenant)
        .filter(Tenant.is_active.is_(True))
        .order_by(Tenant.created_at.asc())
        .first()
    )
    return str(row.id) if row else None


def create_survival_content_master(db: Session, *, tenant_id: str, item: dict[str, Any]) -> str:
    """为审核通过条目创建专用 ContentMaster（不复用旧草稿）。"""
    sku = str(item.get("sku") or "survival_brief")
    title = str(item.get("title") or item.get("label") or f"[survival] {sku}")[:200]
    body = str(item.get("body") or item.get("greedy_summary") or "")[:12000]
    if not body.strip():
        body = f"B2B survival monetization — {sku}. {item.get('cta') or 'Contact for demo.'}"

    master = ContentMaster(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        title=title,
        body=body,
        content_type="article",
        status="ready",
    )
    db.add(master)
    db.commit()
    return str(master.id)


def execute_survival_l4_publish(
    db: Session,
    item: dict[str, Any],
    *,
    user_id: str | None = None,
) -> dict[str, Any]:
    """审核通过后：bootstrap 平台/账号 → 创建 PublishTask。"""
    assert_greedy_action("publish_survival_marketing")
    tenant_id = resolve_greedy_publish_tenant_id(db)
    if not tenant_id:
        return {
            "status": "failed",
            "error": "no_publish_tenant",
            "next_step": "配置 HERMES_GREEDY_PUBLISH_TENANT_ID 或确保存在活跃租户",
        }

    locale = str(item.get("locale") or "global")
    platform_names = channels_to_platform_names(list(item.get("publish_channels") or []), locale=locale)
    master_id = create_survival_content_master(db, tenant_id=tenant_id, item=item)
    message = str(item.get("body") or item.get("title") or "")
    ctx: dict[str, Any] = {
        "locale": locale,
        "platforms": platform_names,
        "human_confirmed": True,
        "auto_bootstrap": True,
        "content_source": "greedy_l4_manual_approve",
        "content_master_id": master_id,
        "fallback_master_id": master_id,
        "product_hint": item.get("sku"),
        "cta": item.get("cta"),
        "scope": "platform_survival_marketing",
        "sku": item.get("sku"),
    }
    from app.services.ubrain.matrix_publish_service import execute_matrix_publish
    result = execute_matrix_publish(
        db,
        tenant_id=tenant_id,
        message=message,
        context=ctx,
        user_id=user_id,
    )
    result["tenant_id"] = tenant_id
    result["content_master_id"] = master_id
    result["platform_names"] = platform_names
    return result


def list_survival_publish_tasks(db: Session, *, limit: int = 20) -> dict[str, Any]:
    """列出摸金 L4 审核后创建的 PublishTask。"""
    assert_greedy_action("read_probe")
    from app.models.content import Platform, PublishTask
    from app.models.content_master import ContentMaster
    cap = max(1, min(int(limit), 50))
    tenant_id = resolve_greedy_publish_tenant_id(db)
    q = (
        db.query(PublishTask, ContentMaster, Platform)
        .outerjoin(ContentMaster, PublishTask.content_master_id == ContentMaster.id)
        .outerjoin(Platform, PublishTask.platform_id == Platform.id)
        .order_by(PublishTask.created_at.desc())
    )
    if tenant_id:
        q = q.filter(PublishTask.tenant_id == tenant_id)
    else:
        q = q.filter(ContentMaster.title.ilike("%survival%"))

    rows = q.limit(cap).all()
    items: list[dict[str, Any]] = []
    for task, master, plat in rows:
        title = (master.title if master else None) or ""
        items.append(
            {
                "id": str(task.id),
                "status": task.status,
                "platform_name": plat.name if plat else None,
                "title": title[:120] or str(task.id)[:8],
                "published_url": task.published_url,
                "error_message": (task.error_message or "")[:200] or None,
                "retry_count": task.retry_count,
                "tenant_id": task.tenant_id,
                "content_master_id": task.content_master_id,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            }
        )
    return {"items": items[:cap], "total": len(items[:cap]), "tenant_id": tenant_id}
