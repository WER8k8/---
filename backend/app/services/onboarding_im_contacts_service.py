# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""开户指引 — 即时通讯联系方式写入官网 contact 页（挂件读取，非旺财 Trade Q&A）。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.services.site_content_bridge import sync_site_content_to_brand

IM_FIELD_KEYS = ("whatsapp", "wechat", "qq", "telegram", "line", "phone", "email")

GUIDE_IM_TOOLS: list[dict[str, str]] = [
    {"key": "whatsapp", "label": "WhatsApp", "hint": "海外客户第一选择 · 挂件一键跳转聊天", "priority": "1"},
    {"key": "wechat", "label": "微信", "hint": "国内/华人客户 · 挂件一键复制微信号", "priority": "2"},
    {"key": "qq", "label": "QQ", "hint": "国内客户常用 · 挂件一键复制 QQ 号", "priority": "3"},
    {"key": "telegram", "label": "Telegram", "hint": "俄语区/中东常用", "priority": "4"},
    {"key": "line", "label": "LINE", "hint": "日本/泰国/台湾市场", "priority": "5"},
    {"key": "phone", "label": "电话", "hint": "国际格式如 +86-138xxxx", "priority": "6"},
    {"key": "email", "label": "邮箱", "hint": "外贸开发信与正式报价", "priority": "7"},
]


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


def _contact_from_tenant(tenant: Tenant) -> dict[str, str]:
    """_contact_from_tenant。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    settings = _safe_settings(tenant.settings)
    brand = settings.get("brand") if isinstance(settings.get("brand"), dict) else {}
    site = brand.get("site_content") if isinstance(brand.get("site_content"), dict) else {}
    pages = site.get("pages") if isinstance(site.get("pages"), dict) else {}
    contact = pages.get("contact") if isinstance(pages.get("contact"), dict) else {}
    out: dict[str, str] = {}
    for key in IM_FIELD_KEYS:
        out[key] = str(contact.get(key) or "").strip()
    if not out["email"]:
        out["email"] = str(settings.get("onboarding", {}).get("contact_email") or tenant.contact_email or "").strip()
    return out


def get_im_contacts_status(tenant: Tenant) -> dict[str, Any]:
    """get_im_contacts_status。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    settings = _safe_settings(tenant.settings)
    onboarding = settings.get("onboarding") if isinstance(settings.get("onboarding"), dict) else {}
    contacts = _contact_from_tenant(tenant)
    has_primary = bool(contacts.get("whatsapp") or contacts.get("wechat") or contacts.get("qq"))
    return {
        "im_contacts_done": bool(onboarding.get("im_contacts_done")),
        "contacts": contacts,
        "has_primary_im": has_primary,
        "guide_tools": GUIDE_IM_TOOLS,
        "note": "客户官网旺财挂件只展示联系方式；Trade Q&A 智能顾问逻辑不变",
    }


def save_im_contacts(
    db: Session,
    tenant: Tenant,
    payload: dict[str, Any],
    *,
    mark_done: bool = True,
) -> dict[str, Any]:
    """save_im_contacts。

    参数说明：
    :param db: 参数 db
    :param tenant: 参数 tenant
    :param payload: 参数 payload
    :param mark_done: 参数 mark_done
    :return: 返回处理结果。
    """
    tid = str(tenant.id)
    row = db.query(Tenant).filter(Tenant.id == tid).first()
    if not row:
        return {"ok": False, "error": "tenant_not_found"}

    settings = _safe_settings(row.settings)
    brand = settings.get("brand") if isinstance(settings.get("brand"), dict) else {}
    site = brand.get("site_content") if isinstance(brand.get("site_content"), dict) else {}
    if not site:
        site = {"brand": {"name": row.name or ""}, "pages": {}, "theme": {}, "footer": {}}

    pages = site.get("pages") if isinstance(site.get("pages"), dict) else {}
    contact = pages.get("contact") if isinstance(pages.get("contact"), dict) else {}
    patch = {k: str(payload.get(k) or "").strip() for k in IM_FIELD_KEYS}
    contact.update({k: v for k, v in patch.items() if v or contact.get(k)})
    for k, v in patch.items():
        if v:
            contact[k] = v

    pages["contact"] = contact
    site["pages"] = pages
    brand["site_content"] = site
    settings["brand"] = sync_site_content_to_brand(brand, site)
    onboarding = settings.get("onboarding") if isinstance(settings.get("onboarding"), dict) else {}
    if mark_done:
        onboarding["im_contacts_done"] = True
        onboarding["im_contacts_at"] = datetime.now(timezone.utc).isoformat()
        sales = onboarding.get("sales_channels") if isinstance(onboarding.get("sales_channels"), dict) else {}
        sales = {**sales, "inbound_configured": True}
        onboarding["sales_channels"] = sales
    onboarding["im_contacts"] = {k: contact.get(k, "") for k in IM_FIELD_KEYS}
    settings["onboarding"] = onboarding
    row.settings = json.dumps(settings, ensure_ascii=False)
    row.updated_at = datetime.now(timezone.utc)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {
        "ok": True,
        "contacts": _contact_from_tenant(row),
        "im_contacts_done": bool(onboarding.get("im_contacts_done")),
        "has_primary_im": bool(contact.get("whatsapp") or contact.get("wechat") or contact.get("qq")),
    }
