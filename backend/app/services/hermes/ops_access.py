# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Hermes 运维 API 访问门控 — L0 超管专用，租户不可见。"""

from __future__ import annotations

from app.models.user import User

OPS_ADMIN_ROLES = frozenset({"admin", "super_admin"})


def is_ops_admin(user: User | None) -> bool:
    """is_ops_admin。

    参数说明：
    :param user: 参数 user
    :return: 返回处理结果。
    """
    if user is None:
        return False
    return (user.role or "") in OPS_ADMIN_ROLES


def ops_admin_forbidden_message() -> str:
    """ops_admin_forbidden_message。
    :return: 返回处理结果。
    """
    return "仅平台超管可访问 Hermes 运维接口；租户请使用副驾 UBrain。"
