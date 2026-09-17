# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Onboarding 全链：注册 → Hermes 建站 → 旺财预览 → 发布首篇。"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING

from sqlalchemy.orm import Session

from app.models.content import PlatformAccount
from app.models.tenant import Tenant
from app.services.onboarding_progress_service import (
    _tenant_has_site,
    build_onboarding_roadmap,
    build_sales_channel_substeps,
    refresh_onboarding_checklist,
)
from app.services.onboarding_publish_service import create_onboarding_first_publish
from app.services.tenant_product_context import resolve_tenant_product_hint
from app.services.tenant_wangcai_service import ask_wangcai_for_tenant
from app.services.wangcai_trade_service import suggested_prompts

if TYPE_CHECKING:
    from app.models.user import User

CHAIN_STEPS = ("welcome", "hermes", "im_contacts", "wangcai", "publish", "done")


def _utcnow() -> datetime:
    """_utcnow。
    :return: 返回处理结果。
    """
    return datetime.now(timezone.utc)


def _safe_settings(raw: str | None) -> dict[str, Any]:
    """_safe_settings。

    参数说明：
    :param raw: 参数 raw
    :return: 返回处理结果。
    """
    if not raw:
        return {}
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def _save_onboarding(tenant: Tenant, onboarding: dict[str, Any]) -> None:
    """_save_onboarding。

    参数说明：
    :param tenant: 参数 tenant
    :param onboarding: 参数 onboarding
    :return: 返回处理结果。
    """
    settings = _safe_settings(tenant.settings)
    settings["onboarding"] = onboarding
    tenant.settings = json.dumps(settings, ensure_ascii=False)
    tenant.updated_at = _utcnow()


def _primary_product(tenant: Tenant) -> str:
    """_primary_product。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    return resolve_tenant_product_hint(tenant) or tenant.name or "建材产品"


def tenant_site_urls(tenant: Tenant) -> dict[str, str]:
    """tenant_site_urls。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    domain = (tenant.domain or "").strip()
    primary = os.getenv("SAAS_PRIMARY_DOMAIN", "youding-saas.com").strip() or "youding-saas.com"
    if not domain:
        return {"production": "", "dev": ""}
    return {
        "production": f"https://{domain}.{primary}",
        "dev": f"http://127.0.0.1:3000/tenant?__tenant={domain}&lpro=1",
    }


def resolve_client_site_url(tenant: Tenant) -> str:
    """租户「我的网站」链接：开发环境走本地 Nuxt 预览，生产走 SaaS 子域。"""
    urls = tenant_site_urls(tenant)
    env = (os.getenv("ENVIRONMENT") or "development").strip().lower()
    if env in ("development", "dev", "local", "test"):
        dev_url = urls.get("dev") or ""
        lan_host = (os.getenv("YOUDING_DEV_LAN_HOST") or os.getenv("YOUDING_NUXT_PUBLIC_HOST") or "").strip()
        if lan_host and dev_url:
            domain = (tenant.domain or "").strip()
            if domain:
                return (
                    f"http://{lan_host}:3000/tenant?"
                    f"__tenant={domain}&lpro=1"
                )
        return dev_url or urls.get("production") or ""
    return urls.get("production") or urls.get("dev") or ""


def resolve_chain_step(tenant: Tenant, db: Session) -> str:
    """resolve_chain_step。

    参数说明：
    :param tenant: 参数 tenant
    :param db: 参数 db
    :return: 返回处理结果。
    """
    settings = _safe_settings(tenant.settings)
    onboarding = settings.get("onboarding") if isinstance(settings.get("onboarding"), dict) else {}
    if onboarding.get("wizard_completed"):
        return "done"
    if not _tenant_has_site(tenant):
        return "hermes"
    if not onboarding.get("im_contacts_done"):
        return "im_contacts"
    if not onboarding.get("wangcai_preview_done"):
        return "wangcai"
    if not onboarding.get("first_publish_done"):
        return "publish"
    return "review"


def build_chain_status(tenant: Tenant, db: Session) -> dict[str, Any]:
    """build_chain_status。

    参数说明：
    :param tenant: 参数 tenant
    :param db: 参数 db
    :return: 返回处理结果。
    """
    settings = _safe_settings(tenant.settings)
    onboarding = settings.get("onboarding") if isinstance(settings.get("onboarding"), dict) else {}
    product = _primary_product(tenant)
    step = resolve_chain_step(tenant, db)
    urls = tenant_site_urls(tenant)
    return {
        "chain_step": step,
        "chain_steps": list(CHAIN_STEPS),
        "site_built": _tenant_has_site(tenant),
        "im_contacts_done": bool(onboarding.get("im_contacts_done")),
        "im_contacts": onboarding.get("im_contacts") if isinstance(onboarding.get("im_contacts"), dict) else {},
        "wangcai_preview_done": bool(onboarding.get("wangcai_preview_done")),
        "first_publish_done": bool(onboarding.get("first_publish_done")),
        "wizard_completed": bool(onboarding.get("wizard_completed")),
        "primary_product": product,
        "tenant_domain": tenant.domain or "",
        "site_preview_url": urls["production"],
        "site_preview_dev_url": urls["dev"],
        "wangcai_prompts": [
            {"id": p["id"], "label": p.get("label_zh") or p.get("label_en") or p["id"]}
            for p in suggested_prompts(product)
        ],
        "first_publish_draft_id": onboarding.get("first_publish_content_id"),
        "first_platform_bound": bool(onboarding.get("first_platform_bound")),
        "sales_channel_steps": build_sales_channel_substeps(db, tenant),
        "sales_channel_framework_step": 5,
        "checklist": refresh_onboarding_checklist(
            db,
            tenant,
            onboarding.get("checklist") if isinstance(onboarding.get("checklist"), list) else None,
        ),
        "onboarding_roadmap": build_onboarding_roadmap(
            db,
            tenant,
            onboarding.get("checklist") if isinstance(onboarding.get("checklist"), list) else None,
        ),
    }


def run_wangcai_preview(
    db: Session,
    tenant: Tenant,
    *,
    message: str | None = None,
) -> dict[str, Any]:
    """run_wangcai_preview。

    参数说明：
    :param db: 参数 db
    :param tenant: 参数 tenant
    :param message: 参数 message
    :return: 返回处理结果。
    """
    product = _primary_product(tenant)
    text = (message or "").strip() or f"{product} 哪些国家好卖？蓝海市场"
    result = ask_wangcai_for_tenant(
        db,
        tenant,
        text,
        source="onboarding_chain",
        product_hint_override=product,
    )
    tid = str(tenant.id)
    row = db.query(Tenant).filter(Tenant.id == tid).first()
    if not row:
        return {**result, "product_hint": product, "chain_step": "wangcai"}

    settings = _safe_settings(row.settings)
    onboarding = settings.get("onboarding") if isinstance(settings.get("onboarding"), dict) else {}
    onboarding["wangcai_preview_done"] = True
    onboarding["wangcai_preview_at"] = _utcnow().isoformat()
    onboarding["wangcai_preview_intent"] = result.get("intent")
    tool = result.get("tool_result") or {}
    recs = tool.get("recommendations") or []
    if recs and isinstance(recs[0], dict):
        onboarding["wangcai_top_market"] = recs[0]
    settings["onboarding"] = onboarding
    row.settings = json.dumps(settings, ensure_ascii=False)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return {
        **result,
        "product_hint": product,
        "chain_step": resolve_chain_step(row, db),
    }


def _first_publish_body(product: str, company: str) -> str:
    """_first_publish_body。

    参数说明：
    :param product: 参数 product
    :param company: 参数 company
    :return: 返回处理结果。
    """
    return (
        f"{company} — Professional {product} for export\n\n"
        f"We supply {product} to importers and distributors worldwide.\n"
        f"- Stable quality with export documentation support\n"
        f"- Flexible MOQ for pilot orders\n"
        f"- Reply within 24 hours\n\n"
        f"Ask 旺财 on our website for market fit and customs tips."
    )


def create_first_publish(
    db: Session,
    tenant: Tenant,
    user: User,
) -> dict[str, Any]:
    """create_first_publish。

    参数说明：
    :param db: 参数 db
    :param tenant: 参数 tenant
    :param user: 参数 user
    :return: 返回处理结果。
    """
    tid = str(tenant.id)
    row = db.query(Tenant).filter(Tenant.id == tid).first()
    if not row:
        return {"error": "tenant_not_found"}

    settings = _safe_settings(row.settings)
    onboarding = settings.get("onboarding") if isinstance(settings.get("onboarding"), dict) else {}
    if onboarding.get("first_publish_done"):
        draft = onboarding.get("first_publish_draft") or {}
        return {
            "already_done": True,
            "content_id": onboarding.get("first_publish_content_id"),
            "task_id": onboarding.get("first_publish_task_id"),
            "title": draft.get("title"),
            "preview": (draft.get("body") or "")[:280],
            "chain_step": resolve_chain_step(row, db),
        }

    product = _primary_product(row)
    company = row.name or "Our company"
    body = _first_publish_body(product, company)
    title = f"{product} export intro"
    top_market = None
    wc_intent = onboarding.get("wangcai_preview_intent")
    if wc_intent:
        top_market = onboarding.get("wangcai_top_market") if isinstance(
            onboarding.get("wangcai_top_market"), dict
        ) else None

    publish_result = create_onboarding_first_publish(
        db,
        row,
        title=title,
        body=body,
        product=product,
        top_market=top_market,
    )
    account = (
        db.query(PlatformAccount)
        .filter(
            PlatformAccount.tenant_id == tid,
            PlatformAccount.is_active.is_(True),
        )
        .order_by(PlatformAccount.created_at.asc())
        .first()
    )
    platform_name = publish_result.get("platform_account") or (
        account.account_name if account else None
    )
    onboarding["first_publish_done"] = True
    onboarding["first_publish_at"] = _utcnow().isoformat()
    onboarding["first_publish_content_id"] = publish_result.get("content_id")
    onboarding["first_publish_task_id"] = publish_result.get("task_id")
    onboarding["first_publish_draft"] = {
        "title": title,
        "body": body,
        "product": product,
        "platform_account_id": str(account.id) if account else None,
    }
    settings["onboarding"] = onboarding
    row.settings = json.dumps(settings, ensure_ascii=False)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    note = (
        "首篇已入队，可在发布队列查看"
        if publish_result.get("queued")
        else "首篇内容已创建；绑定平台后将自动入队"
    )
    return {
        "already_done": False,
        "content_id": publish_result.get("content_id"),
        "task_id": publish_result.get("task_id"),
        "platform_account": platform_name,
        "title": title,
        "preview": publish_result.get("preview") or body[:280],
        "chain_step": resolve_chain_step(row, db),
        "queued": publish_result.get("queued"),
        "note": note,
    }
