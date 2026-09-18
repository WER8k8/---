# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""租户级 AI 场景模型覆盖（存于 tenant.settings.ai_scenario_overrides）。"""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import case
from sqlalchemy.orm import Session

from app.models.tenant import Tenant, UserTenant
from app.models.user import User
from app.services.nvidia_scenario_service import (
    PRODUCT_SCENARIOS,
    build_scenario_switch_payload,
    get_platform_scenario_mappings,
)

logger = logging.getLogger(__name__)

SETTINGS_KEY = "ai_scenario_overrides"

# 租户可覆盖的场景（视频类需平台 Cosmos 能力，仍允许选模型 ID）
TENANT_ALLOWED_SCENARIOS = frozenset(
    {
        "inference",
        "article",
        "article_to_video_script",
        "article_to_video_render",
    }
)


def _safe_settings(raw: str | None) -> dict[str, Any]:
    """_safe_settings。

    参数说明：
    :param raw: 参数 raw
    :return: 返回处理结果。
    """
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def read_tenant_overrides(tenant: Tenant) -> dict[str, str]:
    """read_tenant_overrides。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    settings = _safe_settings(tenant.settings)
    raw = settings.get(SETTINGS_KEY, {})
    if not isinstance(raw, dict):
        return {}
    return {
        k: str(v).strip()
        for k, v in raw.items()
        if k in TENANT_ALLOWED_SCENARIOS and str(v).strip()
    }


def write_tenant_overrides(db: Session, tenant: Tenant, overrides: dict[str, str]) -> dict[str, str]:
    """write_tenant_overrides。

    参数说明：
    :param db: 参数 db
    :param tenant: 参数 tenant
    :param overrides: 参数 overrides
    :return: 返回处理结果。
    """
    cleaned: dict[str, str] = {}
    for key, value in (overrides or {}).items():
        if key not in TENANT_ALLOWED_SCENARIOS:
            continue
        model = str(value or "").strip()
        if model:
            cleaned[key] = model

    settings = _safe_settings(tenant.settings)
    settings[SETTINGS_KEY] = cleaned
    tenant.settings = json.dumps(settings, ensure_ascii=False)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return read_tenant_overrides(tenant)


def merge_tenant_scenario_mappings(
    db: Session,
    tenant_id: str | None,
    platform_mappings: dict[str, str] | None = None,
) -> dict[str, str]:
    """merge_tenant_scenario_mappings。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param platform_mappings: 参数 platform_mappings
    :return: 返回处理结果。
    """
    base = dict(platform_mappings or get_platform_scenario_mappings(db))
    if not tenant_id:
        return base

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return base

    merged = dict(base)
    for key, model in read_tenant_overrides(tenant).items():
        merged[key] = model
    return merged


def get_effective_scenario_mappings(
    db: Session,
    tenant_id: str | None = None,
) -> dict[str, str]:
    """get_effective_scenario_mappings。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    return merge_tenant_scenario_mappings(db, tenant_id)


def resolve_tenant_id_for_user(
    db: Session,
    user: User,
    explicit_tenant_id: str | None = None,
) -> str | None:
    """resolve_tenant_id_for_user。

    参数说明：
    :param db: 参数 db
    :param user: 参数 user
    :param explicit_tenant_id: 参数 explicit_tenant_id
    :return: 返回处理结果。
    """
    if explicit_tenant_id:
        return explicit_tenant_id
    if user.role in ("super_admin", "admin"):
        return None
    # ADR-002 单一真源：本函数是用户→租户归属的唯一解析入口，
    # UserTenant 无 primary/is_default 列，故在解析器内加稳定排序键保证确定性：
    #   1) 租户内 role='admin' 的绑定优先于成员/运营类角色（主账号优先）
    #   2) 同角色按 created_at 早者优先（最早加入的租户）
    #   3) 同 created_at 按 tenant_id 字典序兜底（消除同秒插入并列）
    # 不引入 users.tenant_id 第二真源，避免与 user_tenants 关联表双源漂移。
    admin_role_key = case(
        (UserTenant.role == "admin", 0),
        else_=1,
    )
    link = (
        db.query(UserTenant)
        .filter(UserTenant.user_id == user.id, UserTenant.is_active.is_(True))
        .order_by(
            admin_role_key.asc(),
            UserTenant.created_at.asc(),
            UserTenant.tenant_id.asc(),
        )
        .first()
    )
    return str(link.tenant_id) if link else None


def build_tenant_scenario_payload(db: Session, tenant: Tenant) -> dict[str, Any]:
    """build_tenant_scenario_payload。

    参数说明：
    :param db: 参数 db
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    platform = get_platform_scenario_mappings(db)
    overrides = read_tenant_overrides(tenant)
    effective = merge_tenant_scenario_mappings(db, str(tenant.id), platform)
    catalog = build_scenario_switch_payload(db)
    allowed_rows = []
    for group in catalog.get("groups", []):
        for sc in group.get("scenarios", []):
            if sc.get("id") in TENANT_ALLOWED_SCENARIOS:
                allowed_rows.append(
                    {
                        "id": sc["id"],
                        "label": sc.get("label"),
                        "description": sc.get("description"),
                        "platform_model": platform.get(sc["id"]),
                        "override_model": overrides.get(sc["id"]),
                        "effective_model": effective.get(sc["id"]),
                        "candidates": sc.get("candidates", []),
                    }
                )

    return {
        "tenant_id": str(tenant.id),
        "tenant_name": tenant.name,
        "allowed_scenarios": sorted(TENANT_ALLOWED_SCENARIOS),
        "platform_mappings": platform,
        "overrides": overrides,
        "effective_mappings": effective,
        "scenarios": allowed_rows,
    }
