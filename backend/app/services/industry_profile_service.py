# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Industry Profile 服务（修正设计稿 模块2）。

- get_active_profile(db, code)：取 status=active 且版本最大的参数包。
- boq_overrides(profile)：从 boq_rules 提取核价引擎可消费的参数覆盖包
  （material_base_prices / material_densities / surface_fees / edge_fees /
    grade_multipliers / moq_tiers / material_tokens / default_material），
  未提供的键回落引擎内置默认。
- seed_default_building_materials(db)：幂等播种 code="building_materials" v1
  （boq_rules 与引擎内置默认一致，保证行为零漂移）。

解析链（读路径，fail-safe）：
- resolve_profile_for_tenant / resolve_boq_overrides_for_tenant / get_tenant_profile_code。
  优先级（高→低）：① 调用方显式参数 → ② 租户 settings['industry_profile_code']
  的 active → ③ 全局默认 building_materials active → ④ None（引擎内置 fallback）。
  任何一步失败（坏 JSON / code 不存在 / DB 抖动）都**静默回落**，绝不 raise。

管理面（写路径，需校验）：
- set_tenant_profile_code / list_profiles / get_profile / create_profile_version /
  activate_profile。

存储（零迁移）：租户选定的行业 code 存 `Tenant.settings`（Text/JSON 字符串）的
`industry_profile_code` 键——复用既有列，无需迁移（先例见 api/v1/seo/llms_txt.py:21）。

验收（设计稿 2.6）：仅新增一个非建材 Profile（不改核心代码）即可完成
产品 → 网站 → 内容 → SEO → 匹配 → Quote 主链。
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.industry_profile import IndustryProfile
from app.models.tenant import Tenant

logger = logging.getLogger(__name__)

# 租户 settings JSON 中承载「生效行业 code」的键（复用既有列，零迁移）
_TENANT_PROFILE_KEY = "industry_profile_code"
# 全局默认行业包 code（迁移 131 已播种 active）
_DEFAULT_PROFILE_CODE = "building_materials"

# boq_rules 中引擎/管道可消费的覆盖键白名单
_DICT_OVERRIDE_KEYS = (
    "material_base_prices",
    "material_densities",
    "surface_fees",
    "edge_fees",
    "grade_multipliers",
    "material_tokens",
)


class ProfileConflictError(Exception):
    """Profile 状态冲突（如激活一个已 retired 的版本）→ 路由转 409。"""


def get_active_profile(db: Session, code: str) -> Optional[IndustryProfile]:
    """status=active 且版本号最大的参数包；无则 None（调用方回落引擎默认）。"""
    rows = (
        db.query(IndustryProfile)
        .filter(IndustryProfile.code == code, IndustryProfile.status == "active")
        .order_by(IndustryProfile.version.desc())
        .all()
    )
    return rows[0] if rows else None


def boq_overrides(profile: Optional[IndustryProfile]) -> dict[str, Any]:
    """提取 boq_rules 中引擎/管道可消费的覆盖键（白名单，未知键忽略）。

    既有 6 键（material_base_prices / material_densities / surface_fees /
    edge_fees / grade_multipliers / moq_tiers）+ 模块2 新增 2 键
    （material_tokens：dict[str, list[str]]、default_material：str）。
    未提供则不出现 → 管道/计算器回落硬编码默认（零漂移）。
    """
    if profile is None:
        return {}
    rules = profile.boq_rules if isinstance(profile.boq_rules, dict) else {}
    out: dict[str, Any] = {}
    for key in _DICT_OVERRIDE_KEYS:
        val = rules.get(key)
        if isinstance(val, dict) and val:
            out[key] = val
    moq = rules.get("moq_tiers")
    if isinstance(moq, list) and moq:
        out["moq_tiers"] = moq
    default_material = rules.get("default_material")
    if isinstance(default_material, str) and default_material:
        out["default_material"] = default_material
    return out


def _load_tenant_settings(tenant: Optional[Tenant]) -> dict[str, Any]:
    """读 Tenant.settings（Text/JSON）；坏 JSON / 非 dict → {}（不抛）。"""
    if tenant is None or not tenant.settings:
        return {}
    try:
        data = json.loads(tenant.settings)
    except (json.JSONDecodeError, TypeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def get_tenant_profile_code(db: Session, tenant_id: str) -> Optional[str]:
    """仅读 Tenant.settings['industry_profile_code']（不解析 active），供管理面展示来源。"""
    try:
        tenant = db.query(Tenant).filter(Tenant.id == str(tenant_id)).first()
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取租户 %s settings 失败：%s", tenant_id, exc)
        return None
    code = _load_tenant_settings(tenant).get(_TENANT_PROFILE_KEY)
    return code if isinstance(code, str) and code.strip() else None


def resolve_profile_for_tenant(db: Session, tenant_id: str) -> Optional[IndustryProfile]:
    """解析租户生效的 Profile（读路径，fail-safe，绝不 raise）。

    优先级：租户 settings['industry_profile_code'] 的 active → 全局默认
    building_materials active → None。任何异常/未找到 → 下一级回落。
    """
    code = get_tenant_profile_code(db, tenant_id)
    if code:
        try:
            profile = get_active_profile(db, code)
            if profile is not None:
                return profile
        except Exception as exc:  # noqa: BLE001
            logger.warning("按租户 code=%s 解析 Profile 失败，回落默认：%s", code, exc)
    try:
        return get_active_profile(db, _DEFAULT_PROFILE_CODE)
    except Exception as exc:  # noqa: BLE001
        logger.warning("回落默认 Profile(%s) 失败：%s", _DEFAULT_PROFILE_CODE, exc)
        return None


def resolve_boq_overrides_for_tenant(db: Session, tenant_id: str) -> dict[str, Any]:
    """= boq_overrides(resolve_profile_for_tenant(db, tenant_id))。未配置 → {}（零漂移）。"""
    try:
        return boq_overrides(resolve_profile_for_tenant(db, tenant_id))
    except Exception as exc:  # noqa: BLE001
        logger.warning("解析租户 %s BOQ 覆盖失败，回落空覆盖：%s", tenant_id, exc)
        return {}


def set_tenant_profile_code(
    db: Session, tenant_id: str, code: Optional[str], *, actor: str
) -> Optional[str]:
    """写 Tenant.settings['industry_profile_code']（只改这一个键，不整体替换）。

    code=None（或空串）→ 清除绑定。code 非空时**必须**存在对应 active Profile，
    否则 raise ValueError（→ 路由转 400）。返回写入后的 code。
    复用「复用 Tenant.settings，无需迁移」先例。
    """
    tenant = db.query(Tenant).filter(Tenant.id == str(tenant_id)).first()
    if tenant is None:
        raise LookupError("租户不存在")

    normalized: Optional[str] = None
    if code is not None:
        normalized = str(code).strip() or None
    if normalized is not None and get_active_profile(db, normalized) is None:
        raise ValueError("该行业参数包不存在或未激活")

    settings = _load_tenant_settings(tenant)
    if normalized is None:
        settings.pop(_TENANT_PROFILE_KEY, None)
    else:
        settings[_TENANT_PROFILE_KEY] = normalized
    # 只改本键后回写整段 JSON（churn / ai_traffic 等共用 settings 列，禁止整体替换）
    tenant.settings = json.dumps(settings, ensure_ascii=False)
    db.add(tenant)
    db.commit()
    logger.info("租户 %s 行业绑定更新为 %s（actor=%s）", tenant_id, normalized, actor)
    return normalized


def list_profiles(
    db: Session, *, code: Optional[str] = None, status: Optional[str] = None
) -> list[IndustryProfile]:
    """行业参数包列表（可按 code / status 过滤）。"""
    query = db.query(IndustryProfile)
    if code:
        query = query.filter(IndustryProfile.code == code)
    if status:
        query = query.filter(IndustryProfile.status == status)
    return query.order_by(IndustryProfile.code.asc(), IndustryProfile.version.desc()).all()


def get_profile(db: Session, code: str, version: Optional[int] = None) -> Optional[IndustryProfile]:
    """version=None → 该 code 的 active 最大版本；指定 version → 精确取行。"""
    query = db.query(IndustryProfile).filter(IndustryProfile.code == code)
    if version is None:
        query = query.filter(IndustryProfile.status == "active").order_by(
            IndustryProfile.version.desc()
        )
    else:
        query = query.filter(IndustryProfile.version == version)
    return query.first()


def create_profile_version(
    db: Session,
    *,
    code: str,
    name: str,
    boq_rules: dict,
    actor: str,
    unit_system: str = "metric",
    base_version: Optional[int] = None,
    **fields: Any,
) -> IndustryProfile:
    """新建版本，status='draft'（默认锁定：新建 ≠ 生效）。version = max(同 code) + 1。"""
    code = str(code or "").strip()
    if not code:
        raise ValueError("code 不能为空")
    max_version = (
        db.query(func.max(IndustryProfile.version))
        .filter(IndustryProfile.code == code)
        .scalar()
    )
    version = int(max_version or 0) + 1
    profile = IndustryProfile(
        code=code,
        name=(str(name).strip() if name else code),
        version=version,
        status="draft",
        unit_system=unit_system or "metric",
        boq_rules=boq_rules if isinstance(boq_rules, dict) else {},
        **fields,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    logger.info(
        "新建行业包 %s v%s（draft，actor=%s，base_version=%s）",
        code, version, actor, base_version,
    )
    return profile


def activate_profile(db: Session, code: str, version: int, *, actor: str) -> IndustryProfile:
    """激活：同一事务内先把同 code 其它 active → 'retired'，再把本行 → 'active'。

    version 不存在 → raise LookupError（→ 404）；本行已 retired → raise
    ProfileConflictError（→ 409）。严禁出现同 code 两个 active。
    """
    row = (
        db.query(IndustryProfile)
        .filter(IndustryProfile.code == code, IndustryProfile.version == version)
        .first()
    )
    if row is None:
        raise LookupError("版本不存在")
    if row.status == "retired":
        raise ProfileConflictError("该版本已 retired，不可再激活，请新建版本")

    others = (
        db.query(IndustryProfile)
        .filter(
            IndustryProfile.code == code,
            IndustryProfile.status == "active",
            IndustryProfile.version != version,
        )
        .all()
    )
    for other in others:
        other.status = "retired"
        db.add(other)
    row.status = "active"
    db.add(row)
    db.commit()  # 同一事务：retire 与 activate 一起落库
    db.refresh(row)
    logger.info("激活行业包 %s v%s（同 code 其它 active 已 retire，actor=%s）", code, version, actor)
    return row


def seed_default_building_materials(db: Session) -> Optional[IndustryProfile]:
    """幂等播种建材默认 Profile v1（active）。已存在（任意状态）则返回既有行。

    boq_rules 复用 boq_calculator 的模块级常量（同一真源，避免副本漂移）。
    """
    from app.services.boq_calculator import (
        _DEFAULT_MOQ_TIERS,
        _EDGE_FEES,
        _GRADE_MULTIPLIER,
        _MATERIAL_BASE_PRICES,
        _MATERIAL_DENSITY,
        _SURFACE_FEES,
    )

    existing = (
        db.query(IndustryProfile)
        .filter(IndustryProfile.code == "building_materials")
        .order_by(IndustryProfile.version.desc())
        .first()
    )
    if existing is not None:
        return existing

    profile = IndustryProfile(
        code="building_materials",
        name="建材（默认行业包）",
        version=1,
        status="active",
        unit_system="metric",
        currency_defaults={"base": "USD"},
        incoterm_defaults=["FOB", "CIF", "DDP"],
        boq_rules={
            "material_base_prices": dict(_MATERIAL_BASE_PRICES),
            "material_densities": dict(_MATERIAL_DENSITY),
            "surface_fees": dict(_SURFACE_FEES),
            "edge_fees": dict(_EDGE_FEES),
            "grade_multipliers": dict(_GRADE_MULTIPLIER),
            "moq_tiers": [dict(tier) for tier in _DEFAULT_MOQ_TIERS],
        },
        ui_labels={"unit_sqm": "平方米"},
    )
    db.add(profile)
    db.commit()
    return profile
