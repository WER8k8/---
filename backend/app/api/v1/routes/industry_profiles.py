# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Industry Profile 行业参数包管理面 API（修正设计稿 模块2 / 去行业化收口）。

端点（完整前缀 = /api + /v1 + ROUTE_PREFIX="/industry-profiles"）：
- GET    /industry-profiles                        列表（登录）
- GET    /industry-profiles/{code}                 详情（登录；query version?）
- POST   /industry-profiles/{code}/versions        新建版本（平台管理员；draft）
- POST   /industry-profiles/{code}/activate        激活版本（平台管理员）
- GET    /industry-profiles/tenants/{tenant_id}    查询租户生效参数包
- PUT    /industry-profiles/tenants/{tenant_id}    绑定租户参数包（仅 active）

⚠ 路径修订（Lead 裁定 2026-09-27）：租户绑定端点收敛到本文件命名空间下
  （`/industry-profiles/tenants/{tenant_id}`），**不再**占用顶层 `/tenants/` 命名空间
  （后者归 `routes/tenants.py`，避免一个特性跨两文件/两命名空间并埋遮蔽风险）。
  仍遵守「一个文件只有一个 router = APIRouter()」。
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.core.tenant_access import is_platform_admin
from app.models.industry_profile import IndustryProfile
from app.models.tenant import UserTenant
from app.models.user import User
from app.services import industry_profile_service as ips

ROUTE_PREFIX = "/industry-profiles"
ROUTE_TAGS = ["行业参数包"]

router = APIRouter(tags=["行业参数包"])

# 本租户内可改「行业绑定」的成员角色（UserTenant.role；本仓无独立租户管理员角色表，
# 复用既有 UserTenant.role 列）。平台管理员判据统一走 SSOT：app.core.tenant_access.is_platform_admin
_TENANT_ADMIN_ROLES = ("admin", "tenant_admin", "owner")


def _ensure_tenant_access(tenant_id: str, user: User, db: Session) -> bool:
    """照 boq_import.py：UserTenant 有效归属或平台管理员（app.core.tenant_access.is_platform_admin）。"""
    link = (
        db.query(UserTenant)
        .filter(
            UserTenant.tenant_id == str(tenant_id),
            UserTenant.user_id == str(user.id),
            UserTenant.is_active.is_(True),
        )
        .first()
    )
    return bool(link) or is_platform_admin(user)


def _tenant_membership_role(db: Session, tenant_id: str, user: User) -> Optional[str]:
    link = (
        db.query(UserTenant)
        .filter(
            UserTenant.tenant_id == str(tenant_id),
            UserTenant.user_id == str(user.id),
            UserTenant.is_active.is_(True),
        )
        .first()
    )
    return str(link.role) if (link is not None and link.role) else None


def _profile_brief(p: IndustryProfile) -> dict[str, Any]:
    return {
        "code": p.code,
        "name": p.name,
        "version": p.version,
        "status": p.status,
        "unit_system": p.unit_system,
    }


# ---------- 全局 Profile：列表 / 详情 ----------


@router.get("")
def list_industry_profiles(
    status: Optional[str] = Query(None, description="按状态过滤：draft/active/retired"),
    code: Optional[str] = Query(None, description="按行业 code 过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """行业参数包列表（全局配置，多租户共享，不含租户私有数据）。"""
    items = ips.list_profiles(db, code=code, status=status)
    return success_response(data={"items": [_profile_brief(p) for p in items]})


@router.get("/{code}")
def get_industry_profile(
    code: str,
    version: Optional[int] = Query(None, ge=1, description="指定版本；不传取 active 最大版本"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """行业参数包详情（version 不传 → active 最大版本）。"""
    profile = ips.get_profile(db, code, version)
    if profile is None:
        return error_response(404, "行业参数包不存在")
    data = _profile_brief(profile)
    data.update(
        {
            "currency_defaults": profile.currency_defaults,
            "incoterm_defaults": profile.incoterm_defaults,
            "boq_rules": profile.boq_rules,
        }
    )
    return success_response(data=data)


# ---------- 全局 Profile：新建版本 / 激活（仅平台管理员） ----------


@router.post("/{code}/versions", status_code=201)
def create_industry_profile_version(
    code: str,
    body: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """新建行业参数包版本（默认 status=draft：新建 ≠ 生效）。仅平台管理员（`admin` / `super_admin`，见 app.core.tenant_access.is_platform_admin）。"""
    if not is_platform_admin(current_user):
        return error_response(403, "需要平台管理员权限")
    payload = body or {}
    name = str(payload.get("name") or "").strip()
    if not name:
        return error_response(400, "缺少 name")
    if len(name) > 120:
        return error_response(400, "name 过长（上限 120 字符）")
    boq_rules = payload.get("boq_rules")
    if boq_rules is None:
        boq_rules = {}
    if not isinstance(boq_rules, dict):
        return error_response(400, "boq_rules 必须为对象")
    unit_system = str(payload.get("unit_system") or "metric")
    if len(unit_system) > 30:
        return error_response(400, "unit_system 过长（上限 30 字符）")
    base_version = payload.get("base_version")
    if base_version is not None and (
        isinstance(base_version, bool) or not isinstance(base_version, int) or base_version < 1
    ):
        return error_response(400, "base_version 必须为正整数")
    try:
        profile = ips.create_profile_version(
            db,
            code=code,
            name=name,
            boq_rules=boq_rules,
            actor=str(current_user.id),
            unit_system=unit_system,
            base_version=base_version,
        )
    except ValueError as exc:
        return error_response(400, str(exc))
    return success_response(
        data={"code": profile.code, "version": profile.version, "status": profile.status},
        message="版本已创建（draft）",
    )


@router.post("/{code}/activate")
def activate_industry_profile(
    code: str,
    body: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """激活指定版本（同一事务内 retire 同 code 其它 active）。仅平台管理员（`admin` / `super_admin`，见 app.core.tenant_access.is_platform_admin）。"""
    if not is_platform_admin(current_user):
        return error_response(403, "需要平台管理员权限")
    version = (body or {}).get("version")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        return error_response(400, "version 必须为正整数")
    try:
        profile = ips.activate_profile(db, code, version, actor=str(current_user.id))
    except LookupError:
        return error_response(404, "版本不存在")
    except ips.ProfileConflictError as exc:
        return error_response(409, str(exc))
    retired = [
        p.version
        for p in db.query(IndustryProfile)
        .filter(IndustryProfile.code == code, IndustryProfile.status == "retired")
        .all()
    ]
    return success_response(
        data={
            "code": profile.code,
            "version": profile.version,
            "status": profile.status,
            "retired": sorted(retired),
        },
        message="已激活",
    )


# ---------- 租户绑定 ----------


@router.get("/tenants/{tenant_id}")
def get_tenant_industry_profile(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询租户生效的行业参数包（含来源：tenant 显式绑定 / default 全局回落）。"""
    if not _ensure_tenant_access(tenant_id, current_user, db):
        return error_response(404, "租户不存在或无权访问")
    explicit = ips.get_tenant_profile_code(db, tenant_id)
    profile = ips.resolve_profile_for_tenant(db, tenant_id)
    if profile is None:
        return error_response(404, "行业参数包不存在")
    source = "tenant" if (explicit and profile.code == explicit) else "default"
    return success_response(
        data={
            "effective_code": profile.code,
            "source": source,
            "profile": {
                "code": profile.code,
                "version": profile.version,
                "status": profile.status,
            },
        }
    )


@router.put("/tenants/{tenant_id}")
def set_tenant_industry_profile(
    tenant_id: str,
    body: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """绑定/清除租户生效行业参数包（仅允许绑 active）。code=null 清除绑定。

    权限：跨租户一律 404（不泄露存在性）；本租户内非管理员改绑定 → 403。
    平台管理员（`admin` / `super_admin`，见 app.core.tenant_access.is_platform_admin）不受租户角色限制。
    """
    if not _ensure_tenant_access(tenant_id, current_user, db):
        return error_response(404, "租户不存在或无权访问")
    if not is_platform_admin(current_user):
        role = _tenant_membership_role(db, tenant_id, current_user)
        if role not in _TENANT_ADMIN_ROLES:
            return error_response(403, "需要租户管理员权限")
    payload = body or {}
    if "code" not in payload:
        return error_response(400, "缺少 code（传 code:null 可清除绑定）")
    code = payload.get("code")
    if code is not None and not isinstance(code, str):
        return error_response(400, "code 必须为字符串或 null")
    if isinstance(code, str) and len(code) > 60:
        return error_response(400, "code 过长（上限 60 字符）")
    try:
        written = ips.set_tenant_profile_code(db, tenant_id, code, actor=str(current_user.id))
    except LookupError:
        return error_response(404, "租户不存在或无权访问")
    except ValueError as exc:
        return error_response(400, str(exc))
    return success_response(
        data={"tenant_id": str(tenant_id), "industry_profile_code": written},
        message="已更新租户行业参数包绑定",
    )
