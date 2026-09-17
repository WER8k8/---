# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""租户侧访问控制 — ROLE_PERMISSIONS + 超管 DB 权限码 + 路由守卫。"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.admin_auth import get_user_permission_codes
from app.core.database import get_db
from app.core.permissions import has_permission
from app.core.response import error_response
from app.core.security import get_current_user
from app.models.tenant import Tenant, UserTenant
from app.models.user import User

_ADMIN_ROLES = frozenset({"admin", "super_admin", "tenant_admin"})
_PLATFORM_ADMIN_ROLES = frozenset({"admin", "super_admin"})
# 省代 / 区域代理 / 销售 — 渠道身份，不绑定租户（ROLE-SHELL-LOCK-01）
_CHANNEL_ROLES = frozenset({"l2", "l3", "agent", "sales"})


def user_has_module_permission(user: User, resource: str, action: str) -> bool:
    """user_has_module_permission。

    参数说明：
    :param user: 参数 user
    :param resource: 参数 resource
    :param action: 参数 action
    :return: 返回处理结果。
    """
    if (user.role or "") in _PLATFORM_ADMIN_ROLES:
        return True
    return has_permission(user.role or "viewer", resource, action)


async def user_has_permission_code(user: User, db: Session, code: str) -> bool:
    """user_has_permission_code。

    参数说明：
    :param user: 参数 user
    :param db: 参数 db
    :param code: 参数 code
    :return: 返回处理结果。
    """
    if (user.role or "") == "super_admin":
        return True
    codes = await get_user_permission_codes(user, db)
    return "*:*" in codes or code in codes


def is_platform_admin(user: User) -> bool:
    """is_platform_admin。

    参数说明：
    :param user: 参数 user
    :return: 返回处理结果。
    """
    return (user.role or "") in _PLATFORM_ADMIN_ROLES


def assert_user_tenant_active(user: User, db: Session) -> None:
    """平台管理员、渠道代理跳过；租户用户须关联有效且未冻结的租户。"""
    if is_platform_admin(user):
        return
    if (user.role or "") in _CHANNEL_ROLES:
        return
    link = (
        db.query(UserTenant)
        .filter(UserTenant.user_id == user.id, UserTenant.is_active.is_(True))
        .first()
    )
    if not link:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="未关联租户",
        )
    tenant = db.query(Tenant).filter(Tenant.id == link.tenant_id).first()
    if not tenant or not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="租户已冻结",
        )
    if (tenant.status or "").lower() == "suspended":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="租户已冻结",
        )


def is_tenant_operator(user: User) -> bool:
    """is_tenant_operator。

    参数说明：
    :param user: 参数 user
    :return: 返回处理结果。
    """
    return (user.role or "") in _ADMIN_ROLES or user_has_module_permission(user, "content", "publish")


def is_tenant_staff(user: User) -> bool:
    """可访问租户后台只读/编辑类接口（非纯 viewer）。"""
    if (user.role or "") in _ADMIN_ROLES:
        return True
    if user_has_module_permission(user, "content", "read"):
        return True
    if user_has_module_permission(user, "inquiries", "read"):
        return True
    if user_has_module_permission(user, "products", "read"):
        return True
    if user_has_module_permission(user, "files", "read"):
        return True
    return False


def deny_unless_module(user: User, resource: str, action: str) -> Optional[Any]:
    """返回 error_response 或 None（通过）。"""
    if user_has_module_permission(user, resource, action):
        return None
    return error_response(403, f"缺少权限: {resource}:{action}")


def deny_unless_platform_admin(user: User) -> Optional[Any]:
    """deny_unless_platform_admin。

    参数说明：
    :param user: 参数 user
    :return: 返回处理结果。
    """
    if is_platform_admin(user):
        return None
    return error_response(403, "需要平台管理员权限")


def deny_unless_tenant_staff(user: User) -> Optional[Any]:
    """deny_unless_tenant_staff。

    参数说明：
    :param user: 参数 user
    :return: 返回处理结果。
    """
    if is_tenant_staff(user):
        return None
    return error_response(403, "权限不足")


def deny_unless_tenant_operator(user: User) -> Optional[Any]:
    """deny_unless_tenant_operator。

    参数说明：
    :param user: 参数 user
    :return: 返回处理结果。
    """
    if is_tenant_operator(user):
        return None
    return error_response(403, "需要租户运营或内容发布权限")


def require_module_permission(resource: str, action: str):
    """require_module_permission。

    参数说明：
    :param resource: 参数 resource
    :param action: 参数 action
    :return: 返回处理结果。
    """
    def checker(user: User = Depends(get_current_user)) -> User:
        """checker。

        参数说明：
        :param user: 参数 user
        :return: 返回处理结果。
        """
        if not user_has_module_permission(user, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"缺少权限: {resource}:{action}",
            )
        return user

    return Depends(checker)


def require_tenant_operator():
    """require_tenant_operator。
    :return: 返回处理结果。
    """
    def checker(user: User = Depends(get_current_user)) -> User:
        """checker。

        参数说明：
        :param user: 参数 user
        :return: 返回处理结果。
        """
        if not is_tenant_operator(user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要租户运营或内容发布权限",
            )
        return user

    return Depends(checker)


def require_tenant_staff():
    """require_tenant_staff。
    :return: 返回处理结果。
    """
    def checker(user: User = Depends(get_current_user)) -> User:
        """checker。

        参数说明：
        :param user: 参数 user
        :return: 返回处理结果。
        """
        if not is_tenant_staff(user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足",
            )
        return user

    return Depends(checker)
