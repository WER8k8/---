# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""数据导出门禁：平台级导出仅创始人 + 全量留痕。"""

from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.services.founder_wechat_service import user_is_founder
from app.services.security_event_service import (
    ACTION_DATA_EXPORT,
    ACTION_DATA_EXPORT_DENIED,
    log_security_event,
)


def _export_founder_only() -> bool:
    """_export_founder_only。
    :return: 返回处理结果。
    """
    raw = getattr(settings, "EXPORT_PLATFORM_FOUNDER_ONLY", True)
    if isinstance(raw, str):
        return raw.lower() in ("1", "true", "yes")
    return bool(raw)


def assert_export_allowed(
    db: Session,
    user: User,
    request: Optional[Request],
    *,
    export_kind: str,
    scope: str = "tenant",
    row_count: int = 0,
    extra: Optional[dict] = None,
) -> None:
    """
    scope:
      - tenant: 租户内导出（租户管理员/销售等按既有角色）
      - platform: 全平台/超管视角导出，默认仅创始人
    """
    role = (user.role or "").lower()
    detail = {
        "export_kind": export_kind,
        "scope": scope,
        "row_count": row_count,
        "role": role,
        **(extra or {}),
    }
    if scope == "platform" and _export_founder_only():
        if not user_is_founder(db, user):
            log_security_event(
                db,
                action=ACTION_DATA_EXPORT_DENIED,
                user=user,
                detail={**detail, "reason": "platform_export_founder_only"},
                request=request,
                resource_id=export_kind,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="全平台数据导出仅创始人账号可执行（防成果拷贝）",
            )

    if scope == "tenant":
        allowed_roles = {
            "super_admin",
            "admin",
            "tenant_admin",
            "sales",
            "editor",
        }
        if role not in allowed_roles:
            log_security_event(
                db,
                action=ACTION_DATA_EXPORT_DENIED,
                user=user,
                detail={**detail, "reason": "role_not_allowed"},
                request=request,
                resource_id=export_kind,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权导出该数据",
            )

    log_security_event(
        db,
        action=ACTION_DATA_EXPORT,
        user=user,
        detail=detail,
        request=request,
        resource_id=export_kind,
    )
