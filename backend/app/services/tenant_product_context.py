# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""租户主营产品上下文 — 注册 / Hermes / 旺财 / 蓝海 单一来源。"""

from __future__ import annotations

import json
from typing import Any

from app.models.tenant import Tenant

WANGCAI_ENGINE = "ask_wangcai_v1"


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


def resolve_tenant_product_hint(tenant: Tenant | None) -> str | None:
    """resolve_tenant_product_hint。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    if not tenant:
        return None
    settings = _safe_settings(tenant.settings)
    onboarding = settings.get("onboarding") if isinstance(settings.get("onboarding"), dict) else {}
    hint = str(onboarding.get("primary_product") or "").strip()
    if hint:
        return hint
    brand = settings.get("brand") if isinstance(settings.get("brand"), dict) else {}
    site_title = str(brand.get("site_title") or "").strip()
    if site_title:
        return site_title
    name = str(tenant.name or "").strip()
    return name or None


def set_tenant_primary_product(db, tenant: Tenant, product: str) -> str:
    """写入 onboarding.primary_product（Hermes / 注册 / autopilot 共用）。"""
    product = (product or "").strip()
    if not product:
        return resolve_tenant_product_hint(tenant) or ""
    settings = _safe_settings(tenant.settings)
    onboarding = settings.get("onboarding") if isinstance(settings.get("onboarding"), dict) else {}
    onboarding["primary_product"] = product
    settings["onboarding"] = onboarding
    tenant.settings = json.dumps(settings, ensure_ascii=False)
    db.add(tenant)
    db.flush()
    return product
