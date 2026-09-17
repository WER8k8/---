# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
from enum import Enum


class Role(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    TENANT_ADMIN = "tenant_admin"
    EDITOR = "editor"
    SALES = "sales"
    VIEWER = "viewer"
    L2 = "l2"  # 大区/总代(省代)
    L3 = "l3"  # 区域运营


MODULES = [
    "products",
    "cases",
    "content",
    "inquiries",
    "seo",
    "analytics",
    "users",
    "settings",
    "ab_test",
    "ai_config",
    "news",
    "compliance",
    "system",
    # FIX-28: 新增获客引擎模块
    "lead_generation",
    "email_outreach",
    "prospect_management",
]


ALL_ACTIONS = [
    "create",
    "read",
    "update",
    "delete",
    "publish",
    "export",
    "batch",
    "ai_optimize",
    "optimize",
    "switch",
    "audit",
]


ROLE_PERMISSIONS = {
    Role.SUPER_ADMIN: {module: ALL_ACTIONS.copy() for module in MODULES},
    Role.ADMIN: {
        "products": ["create", "read", "update", "delete", "publish"],
        "cases": ["create", "read", "update", "delete", "publish"],
        "content": ["create", "read", "update", "delete", "publish"],
        "inquiries": ["read", "update", "delete", "export"],
        "seo": ["read", "update", "batch", "ai_optimize", "optimize"],
        "analytics": ["read"],
        "users": [],
        "settings": [],
        "ab_test": ["create", "read", "update"],
        "ai_config": ["read"],
        "news": ["create", "read", "update", "delete", "publish"],
        "compliance": ["read"],
        "system": [],
    },
    Role.TENANT_ADMIN: {
        "products": ["create", "read", "update", "delete", "publish"],
        "cases": ["create", "read", "update", "delete", "publish"],
        "content": ["create", "read", "update", "delete", "publish"],
        "inquiries": ["read", "update", "export"],
        "seo": ["read", "update", "batch", "ai_optimize", "optimize"],
        "analytics": ["read"],
        "users": ["read"],
        "settings": ["read"],
        "ab_test": ["create", "read", "update"],
        "ai_config": ["read"],
        "news": ["read"],
        "compliance": ["read"],
        "system": [],
    },
    Role.EDITOR: {
        "products": ["create", "read", "update", "publish"],
        "cases": ["create", "read", "update", "publish"],
        "content": ["create", "read", "update", "publish"],
        "inquiries": ["read"],
        "seo": ["read", "update", "ai_optimize"],
        "analytics": ["read"],
        "users": [],
        "settings": [],
        "ab_test": ["create", "read", "update"],
        "ai_config": ["read"],
        "news": ["create", "read", "update", "publish"],
        "compliance": [],
        "system": [],
    },
    Role.SALES: {
        "products": ["read"],
        "cases": ["read"],
        "content": ["read"],
        "inquiries": ["read", "update", "export"],
        "seo": ["read"],
        "analytics": ["read"],
        "users": [],
        "settings": [],
        "ai_config": ["read"],
        "news": ["read"],
        "compliance": [],
        "system": [],
        "lead_generation": ["create", "read", "update", "export"],
        "email_outreach": ["create", "read", "update", "delete"],
        "prospect_management": ["create", "read", "update", "delete"],
    },
    Role.VIEWER: {
        "products": ["read"],
        "cases": ["read"],
        "content": ["read"],
        "inquiries": [],
        "seo": [],
        "analytics": [],
        "users": [],
        "settings": [],
        "ai_config": ["read"],
        "news": ["read"],
        "compliance": [],
        "system": [],
        "lead_generation": ["read"],
        "email_outreach": [],
        "prospect_management": ["read"],
    },
    Role.L2: {
        "products": ["create", "read", "update", "delete"],
        "cases": ["create", "read", "update", "delete"],
        "content": ["create", "read", "update", "delete"],
        "inquiries": ["create", "read", "update", "delete"],
        "seo": ["create", "read", "update", "delete"],
        "analytics": ["create", "read", "update", "delete"],
        "users": ["read"],
        "settings": ["read", "update"],
        "ab_test": ["create", "read", "update", "delete"],
        "news": ["create", "read", "update", "delete"],
        "ai_config": ["read"],
        "compliance": [],
        "system": [],
        "lead_generation": ["create", "read", "update", "export"],
        "email_outreach": ["create", "read", "update"],
        "prospect_management": ["create", "read", "update"],
    },
    Role.L3: {
        "products": ["create", "read", "update", "delete"],
        "cases": ["read"],
        "content": ["read"],
        "inquiries": ["create", "read", "update", "delete"],
        "seo": ["create", "read", "update", "delete"],
        "analytics": ["read"],
        "users": [],
        "settings": ["read", "update"],
        "ab_test": [],
        "news": ["read"],
        "ai_config": ["read"],
        "compliance": [],
        "system": [],
        "lead_generation": ["create", "read", "update"],
        "email_outreach": ["create", "read"],
        "prospect_management": ["create", "read", "update"],
    },
}


def has_permission(role: str, resource: str, action: str) -> bool:
    """检查角色是否有某个资源的操作权限。

    H-04 权限统一: 优先数据库 AdminRole → 回退 Role 枚举
    """
    if role == Role.SUPER_ADMIN:
        return True

    # 先：数据库驱动权限码
    try:
        from app.core.admin_auth import check_permission_code
        perm_code = f"{resource}:{action}"
        if check_permission_code(role, perm_code):
            return True
    except Exception:
        # 数据库查询失败时记录告警，回退到内存权限表而非静默放行
        import logging as _logging
        _logging.getLogger("uj-admin.permissions").warning(
            "数据库权限查询失败 (role=%s, perm=%s)，回退到内存权限表",
            role, perm_code,
        )

    # 回退：角色枚举权限
    role_enum = Role(role) if role in [r.value for r in Role] else Role.VIEWER
    perms = ROLE_PERMISSIONS.get(role_enum, {})
    resource_perms = perms.get(resource, [])
    return action in resource_perms


def get_role_label(role: str) -> str:
    """get_role_label。

    参数说明：
    :param role: 参数 role
    :return: 返回处理结果。
    """
    labels = {
        "super_admin": "超级管理员",
        "admin": "管理员",
        "tenant_admin": "租户管理员",
        "editor": "编辑",
        "sales": "销售",
        "viewer": "访客",
        "l2": "大区总代(省代)",
        "l3": "区域运营",
    }
    return labels.get(role, role)


def is_super_admin(role: str) -> bool:
    """is_super_admin。

    参数说明：
    :param role: 参数 role
    :return: 返回处理结果。
    """
    return role == Role.SUPER_ADMIN


def get_module_list() -> list:
    """get_module_list。
    :return: 返回处理结果。
    """
    return MODULES


# ── FIX-28: API 端点级权限装饰器 ──

from functools import wraps
from typing import Callable, Optional

from fastapi import HTTPException, status


def require_permission(resource: str, action: str = "read"):
    """API 端点权限装饰器。

    用法:
        @router.get("/leads")
        @require_permission("lead_generation", "read")
        async def get_leads(...):
            ...

    检查逻辑:
        1. 从参数中提取 current_user
        2. 调用 has_permission(role, resource, action)
        3. 无权限时返回 403
    """
    def decorator(func: Callable) -> Callable:
        """decorator。

        参数说明：
        :param func: 参数 func
        :return: 返回处理结果。
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            """wrapper。

            参数说明：
            :param *args: 参数 *args
            :param **kwargs: 参数 **kwargs
            :return: 返回处理结果。
            """
            # 提取 current_user
            current_user = None
            for arg in args:
                if hasattr(arg, "role") and hasattr(arg, "id"):
                    current_user = arg
                    break
            if "current_user" in kwargs:
                current_user = kwargs["current_user"]

            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未认证",
                )

            role = getattr(current_user, "role", "viewer")
            if not has_permission(role, resource, action):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"权限不足: 需要 {resource}:{action}",
                )

            # 记录审计日志
            from app.core.data_classification import audit_data_access
            audit_data_access(
                user_id=str(current_user.id),
                model_name=resource,
                field_name="*",
                action=action,
                level=1,  # L1_INTERNAL
            )
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def get_module_actions(module: str) -> list:
    """get_module_actions。

    参数说明：
    :param module: 参数 module
    :return: 返回处理结果。
    """
    return ALL_ACTIONS if module in MODULES else []
