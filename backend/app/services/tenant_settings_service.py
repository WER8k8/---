"""租户 settings JSON 解析（P1-05 等）。"""

from __future__ import annotations

import json
from typing import Any

from app.models.tenant import Tenant


def parse_tenant_settings(tenant: Tenant | None) -> dict[str, Any]:
    """parse_tenant_settings。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    if not tenant or not tenant.settings:
        return {}
    try:
        data = json.loads(tenant.settings)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def hide_hub_backlink(tenant: Tenant | None) -> bool:
    """租户独立站默认隐藏指向总站枢纽的友链。"""
    cfg = parse_tenant_settings(tenant)
    if "hide_hub_backlink" in cfg:
        return bool(cfg.get("hide_hub_backlink"))
    return True


def set_tenant_setting(tenant: Tenant, key: str, value: Any) -> dict[str, Any]:
    """set_tenant_setting。

    参数说明：
    :param tenant: 参数 tenant
    :param key: 参数 key
    :param value: 参数 value
    :return: 返回处理结果。
    """
    cfg = parse_tenant_settings(tenant)
    cfg[key] = value
    tenant.settings = json.dumps(cfg, ensure_ascii=False)
    return cfg
