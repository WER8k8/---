# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""数据安全分级分类 — FIX-26: 数据安全分级 + 字段级敏感标签

数据分级：
  L0 - 公开：无需认证即可访问（如产品列表、案例展示）
  L1 - 内部：需要认证但非敏感（如用户名、角色）
  L2 - 敏感：需要认证 + 审批（如邮箱、手机号、联系人）
  L3 - 机密：需要严格授权 + 审计（如密码哈希、支付信息、API Key）

使用方式：
  from app.core.data_classification import DataClassification, classify_field

  @classify_field("email", DataClassification.L2_SENSITIVE)
  @classify_field("password_hash", DataClassification.L3_CONFIDENTIAL)
  class User(Base):
      ...
"""

from __future__ import annotations

import logging
from enum import IntEnum
from functools import wraps
from typing import Any, Callable, Optional

log = logging.getLogger(__name__)


class DataClassification(IntEnum):
    """数据安全分级。"""
    L0_PUBLIC = 0        # 公开：无需认证
    L1_INTERNAL = 1      # 内部：需认证
    L2_SENSITIVE = 2     # 敏感：需认证 + 审批
    L3_CONFIDENTIAL = 3  # 机密：需严格授权 + 审计


# ── 字段级分类注册表 ──

_field_classifications: dict[str, dict[str, DataClassification]] = {}


def classify_field(field_name: str, level: DataClassification):
    """装饰器：标记模型字段的数据安全级别。

    用法:
        @classify_field("email", DataClassification.L2_SENSITIVE)
        @classify_field("phone", DataClassification.L2_SENSITIVE)
        class SomeModel(Base):
            ...
    """
    def decorator(cls):
        """decorator。

        参数说明：
        :param cls: 参数 cls
        :return: 返回处理结果。
        """
        if cls.__name__ not in _field_classifications:
            _field_classifications[cls.__name__] = {}
        _field_classifications[cls.__name__][field_name] = level
        return cls
    return decorator


def get_field_level(model_class_name: str, field_name: str) -> DataClassification:
    """查询字段安全级别，默认 L1_INTERNAL。"""
    model_fields = _field_classifications.get(model_class_name, {})
    return model_fields.get(field_name, DataClassification.L1_INTERNAL)


def get_classified_fields(model_class_name: str) -> dict[str, DataClassification]:
    """获取模型的所有分类字段。"""
    return _field_classifications.get(model_class_name, {})


# ── 审计日志 ──

_audit_log: list[dict] = []  # 内存审计日志（生产环境应替换为数据库/ELK）
_MAX_AUDIT_LOG = 5000


def audit_data_access(
    user_id: str,
    model_name: str,
    field_name: str,
    action: str,  # read / write / delete
    level: DataClassification,
    ip: str = "",
    success: bool = True,
):
    """记录敏感数据访问审计日志。

    生产环境应替换为：
    - 写入数据库 audit_log 表
    - 或发送到 ELK / Kafka / Splunk
    """
    import time as _time
    from datetime import datetime, timezone
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "model": model_name,
        "field": field_name,
        "action": action,
        "level": level.name,
        "ip": ip,
        "success": success,
    }
    _audit_log.append(entry)
    if len(_audit_log) > _MAX_AUDIT_LOG:
        _audit_log[:] = _audit_log[-_MAX_AUDIT_LOG // 2:]

    if level >= DataClassification.L2_SENSITIVE:
        log.warning(
            "[AUDIT] level=%s user=%s model=%s field=%s action=%s ip=%s",
            level.name, user_id, model_name, field_name, action, ip,
        )


def get_recent_audit_logs(limit: int = 100) -> list[dict]:
    """获取最近审计日志。"""
    return _audit_log[-limit:]


# ── 最小权限守卫 ──

def requires_classification_level(required_level: DataClassification):
    """装饰器：要求当前用户具有指定数据安全级别的访问权限。

    用于 API 端点级别的数据安全控制。
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
                from fastapi import HTTPException
                raise HTTPException(status_code=401, detail="未认证")

            user_role = getattr(current_user, "role", "viewer")
            if not _can_access_level(user_role, required_level):
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=403,
                    detail=f"数据安全级别 {required_level.name} 需要更高权限",
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def _can_access_level(role: str, level: DataClassification) -> bool:
    """角色是否可访问指定数据安全级别。"""
    role_permissions = {
        "super_admin": DataClassification.L3_CONFIDENTIAL,
        "admin": DataClassification.L2_SENSITIVE,
        "tenant_admin": DataClassification.L2_SENSITIVE,
        "editor": DataClassification.L1_INTERNAL,
        "agent": DataClassification.L1_INTERNAL,
        "viewer": DataClassification.L0_PUBLIC,
    }
    max_level = role_permissions.get(role, DataClassification.L0_PUBLIC)
    return max_level >= level


# ── 数据脱敏 ──

def mask_sensitive_data(
    data: dict,
    model_name: str,
    user_role: str = "viewer",
) -> dict:
    """根据用户角色对敏感数据进行脱敏。

    L2 及以上字段对 viewer 角色脱敏：
    - email: u***@example.com
    - phone: 138****1234
    - 其他: ***
    """
    classified = get_classified_fields(model_name)
    if not classified:
        return data

    max_level = {
        "super_admin": DataClassification.L3_CONFIDENTIAL,
        "admin": DataClassification.L2_SENSITIVE,
        "tenant_admin": DataClassification.L2_SENSITIVE,
        "editor": DataClassification.L1_INTERNAL,
        "agent": DataClassification.L1_INTERNAL,
        "viewer": DataClassification.L0_PUBLIC,
    }.get(user_role, DataClassification.L0_PUBLIC)
    result = dict(data)
    for field_name, level in classified.items():
        if level > max_level and field_name in result:
            result[field_name] = _mask_value(result[field_name], field_name)

    return result


def _mask_value(value: Any, field_name: str) -> str:
    """对单个值进行脱敏。"""
    if value is None:
        return None
    s = str(value)
    if "@" in s and "." in s:
        # 邮箱脱敏
        parts = s.split("@")
        if len(parts) == 2:
            return f"{parts[0][0]}***@{parts[1]}"
    if field_name in ("phone", "mobile", "tel"):
        # 手机号脱敏
        if len(s) >= 7:
            return s[:3] + "****" + s[-4:]
    if len(s) > 4:
        return s[:2] + "***" + s[-2:]
    return "***"