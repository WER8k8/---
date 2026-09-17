# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""租户团队 RBAC 快照 — 角色权限矩阵（ROLE_PERMISSIONS + 超管 DB 角色）。"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.permissions import MODULES, ROLE_PERMISSIONS, Role, get_role_label
from app.models.admin import AdminRole


_TENANT_FACING_ROLES = (
    Role.TENANT_ADMIN,
    Role.EDITOR,
    Role.SALES,
    Role.VIEWER,
    Role.L3,
)


def build_team_rbac_snapshot(db: Session | None = None) -> dict[str, Any]:
    """build_team_rbac_snapshot。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    roles: list[dict[str, Any]] = []
    for role in _TENANT_FACING_ROLES:
        perms = ROLE_PERMISSIONS.get(role, {})
        modules = {
            mod: acts for mod, acts in perms.items() if acts and mod in MODULES
        }
        roles.append(
            {
                "role": role.value,
                "label": get_role_label(role.value),
                "scope": _role_scope_summary(role.value),
                "modules": modules,
            }
        )

    custom_roles: list[dict[str, Any]] = []
    if db is not None:
        for row in db.query(AdminRole).order_by(AdminRole.sort_order).limit(50).all():
            if row.is_system:
                continue
            custom_roles.append(
                {
                    "role_id": str(row.id),
                    "name": row.name,
                    "description": row.description or "",
                    "permission_count": len(row.permissions or []),
                }
            )

    return {
        "mode": "tenant_rbac_matrix",
        "roles": roles,
        "custom_admin_roles": custom_roles,
        "manage_api": "/api/v1/users",
        "super_admin_permissions_api": "/api/v1/super-admin/permissions/roles",
        "note": "路由层已支持 ROLE_PERMISSIONS；超管可配置 AdminRole 权限码。",
    }


def _role_scope_summary(role: str) -> str:
    """_role_scope_summary。

    参数说明：
    :param role: 参数 role
    :return: 返回处理结果。
    """
    mapping = {
        "tenant_admin": "全租户配置、内容与发布",
        "editor": "内容与 SEO 编辑发布",
        "sales": "询盘跟进、开发信与导出",
        "viewer": "只读浏览",
        "l3": "区域运营与询盘处理",
    }
    return mapping.get(role, role)
