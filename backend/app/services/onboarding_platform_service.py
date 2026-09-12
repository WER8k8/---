"""开户向导 — 首个平台绑定（内嵌 OAuth/Cookie，不跳转菜单）。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.content import Platform, PlatformAccount
from app.models.tenant import Tenant


def _safe_settings(raw: str | None) -> dict:
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


def get_first_platform_slot(db: Session, tenant: Tenant) -> dict[str, Any]:
    """返回向导内应绑定的第一个平台位。"""
    tid = str(tenant.id)
    account = (
        db.query(PlatformAccount)
        .filter(
            PlatformAccount.tenant_id == tid,
            PlatformAccount.is_active.is_(True),
        )
        .order_by(PlatformAccount.created_at.asc())
        .first()
    )
    if account:
        plat = db.query(Platform).filter(Platform.id == account.platform_id).first()
        return {
            "account_id": str(account.id),
            "platform_id": str(account.platform_id),
            "platform_name": plat.name if plat else account.account_name,
            "region": getattr(account, "region", None) or (plat.region if plat else "cn"),
            "login_status": account.login_status or "logged_out",
            "bound": (account.login_status or "") == "logged_in",
            "connect_hint": "填写 Cookie 或 OAuth Token 完成绑定",
        }

    onboarding = _safe_settings(tenant.settings).get("onboarding") or {}
    slots = onboarding.get("platforms") if isinstance(onboarding.get("platforms"), list) else []
    if slots:
        slot = slots[0] if isinstance(slots[0], dict) else {}
        return {
            "account_id": None,
            "platform_id": slot.get("platform_id"),
            "platform_name": slot.get("platform_name"),
            "region": slot.get("region") or "cn",
            "login_status": "logged_out",
            "bound": False,
            "connect_hint": slot.get("connect_hint") or "绑定后即可自动发布首篇",
        }

    return {
        "account_id": None,
        "platform_id": None,
        "platform_name": None,
        "bound": False,
        "need_select": True,
        "connect_hint": "注册时未选平台；可在此填写平台名称与凭证",
    }


def bind_first_platform(
    db: Session,
    tenant: Tenant,
    *,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """bind_first_platform。

    参数说明：
    :param db: 参数 db
    :param tenant: 参数 tenant
    :param payload: 参数 payload
    :return: 返回处理结果。
    """
    from app.services.platform_account_service import upsert_bound_account
    from app.services.platform_catalog import resolve_or_create_platform_by_name
    from app.services.platform_sync_service import (
        SOURCE_CONNECT,
        apply_account_provision_defaults,
        sync_customer_platform_to_admin,
    )
    tenant_id = str(tenant.id)
    platform_id = str(payload.get("platform_id") or payload.get("platform") or "").strip()
    platform_name = str(payload.get("platform_name") or "").strip()
    platform = None
    if platform_id:
        platform = db.query(Platform).filter(Platform.id == platform_id).first()
    if not platform and platform_name:
        platform = resolve_or_create_platform_by_name(
            db,
            platform_name,
            region=str(payload.get("region") or "cn"),
            content_type=str(payload.get("content_type") or "article"),
        )
    if not platform:
        return {"ok": False, "error": "platform_required"}

    apply_account_provision_defaults(payload, platform, tenant_id=tenant_id, db=db)
    account, created = upsert_bound_account(
        db,
        tenant_id=tenant_id,
        platform=platform,
        payload=payload,
    )
    sync_customer_platform_to_admin(
        db,
        tenant_id=tenant_id,
        platform=platform,
        source=SOURCE_CONNECT,
        is_new_platform=created,
        nurture_rules=payload.get("nurture"),
        browser_profile_id=payload.get("browser_profile_id"),
    )
    settings = _safe_settings(tenant.settings)
    onboarding = settings.get("onboarding") if isinstance(settings.get("onboarding"), dict) else {}
    onboarding["first_platform_bound"] = True
    onboarding["first_platform_bound_at"] = datetime.now(timezone.utc).isoformat()
    settings["onboarding"] = onboarding
    tenant.settings = json.dumps(settings, ensure_ascii=False)
    db.add(tenant)
    db.commit()
    db.refresh(account)
    queued_task_id = None
    content_id = onboarding.get("first_publish_content_id")
    if content_id and not onboarding.get("first_publish_task_id"):
        from app.services.onboarding_publish_service import queue_publish_for_content
        queued = queue_publish_for_content(db, tenant, content_id=str(content_id))
        if queued.get("task_id"):
            queued_task_id = queued["task_id"]
            onboarding["first_publish_task_id"] = queued_task_id
            settings["onboarding"] = onboarding
            tenant.settings = json.dumps(settings, ensure_ascii=False)
            db.commit()

    return {
        "ok": True,
        "account_id": str(account.id),
        "platform_id": str(platform.id),
        "platform_name": platform.name,
        "login_status": account.login_status,
        "created": created,
        "queued_task_id": queued_task_id,
    }
