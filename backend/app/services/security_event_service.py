# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""成果保护：高价值安全事件写入 operation_logs（供鉴定与追溯）。"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.user import OperationLog, User


# resource_type 固定，便于超管/创始人筛选
SECURITY_RESOURCE = "security_event"

ACTION_FOUNDER_ACCESS = "FOUNDER_ACCESS"
ACTION_FOUNDER_DENIED = "FOUNDER_DENIED"
ACTION_DATA_EXPORT = "DATA_EXPORT"
ACTION_DATA_EXPORT_DENIED = "DATA_EXPORT_DENIED"
ACTION_AUTH_SENSITIVE = "AUTH_SENSITIVE"


def _client_ip(request: Optional[Request]) -> str:
    """_client_ip。

    参数说明：
    :param request: 参数 request
    :return: 返回处理结果。
    """
    if not request:
        return ""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return ""


def log_security_event(
    db: Session,
    *,
    action: str,
    user: Optional[User] = None,
    user_id: Optional[str] = None,
    detail: Optional[dict[str, Any]] = None,
    request: Optional[Request] = None,
    resource_id: Optional[str] = None,
) -> OperationLog:
    """log_security_event。

    参数说明：
    :param db: 参数 db
    :param action: 参数 action
    :param user: 参数 user
    :param user_id: 参数 user_id
    :param detail: 参数 detail
    :param request: 参数 request
    :param resource_id: 参数 resource_id
    :return: 返回处理结果。
    """
    uid = user_id or (str(user.id) if user else None)
    payload = detail or {}
    if request:
        payload.setdefault("path", str(request.url.path))
        payload.setdefault("method", request.method)
    row = OperationLog(
        id=str(uuid.uuid4()),
        user_id=uid,
        action=action,
        resource_type=SECURITY_RESOURCE,
        resource_id=resource_id or payload.get("export_kind"),
        detail=json.dumps(payload, ensure_ascii=False)[:8000],
        ip_address=_client_ip(request) or None,
        created_at=datetime.now(timezone.utc),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_security_events(
    db: Session,
    *,
    limit: int = 50,
    action: Optional[str] = None,
) -> list[dict[str, Any]]:
    """list_security_events。

    参数说明：
    :param db: 参数 db
    :param limit: 参数 limit
    :param action: 参数 action
    :return: 返回处理结果。
    """
    q = (
        db.query(OperationLog)
        .filter(OperationLog.resource_type == SECURITY_RESOURCE)
        .order_by(OperationLog.created_at.desc())
    )
    if action:
        q = q.filter(OperationLog.action == action)
    rows = q.limit(min(limit, 200)).all()
    out = []
    for r in rows:
        try:
            detail = json.loads(r.detail) if r.detail else {}
        except json.JSONDecodeError:
            detail = {"raw": r.detail}
        out.append(
            {
                "id": str(r.id),
                "action": r.action,
                "user_id": str(r.user_id) if r.user_id else None,
                "resource_id": r.resource_id,
                "ip_address": r.ip_address,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "detail": detail,
            }
        )
    return out


def protection_summary(db: Session) -> dict[str, Any]:
    """第三方鉴定用摘要（无源码）。"""
    from app.core.config import settings
    from app.services.founder_wechat_service import (
        expected_founder_wechat_provider_id,
        founder_bind_key_display,
        founder_wechat_configured,
    )
    exports = (
        db.query(OperationLog)
        .filter(
            OperationLog.resource_type == SECURITY_RESOURCE,
            OperationLog.action == ACTION_DATA_EXPORT,
        )
        .count()
    )
    denied = (
        db.query(OperationLog)
        .filter(
            OperationLog.resource_type == SECURITY_RESOURCE,
            OperationLog.action.in_(
                [ACTION_FOUNDER_DENIED, ACTION_DATA_EXPORT_DENIED]
            ),
        )
        .count()
    )
    founder_hits = (
        db.query(OperationLog)
        .filter(
            OperationLog.resource_type == SECURITY_RESOURCE,
            OperationLog.action == ACTION_FOUNDER_ACCESS,
        )
        .count()
    )
    return {
        "founder_wechat_configured": founder_wechat_configured(),
        "founder_wechat_locked": founder_bind_key_display(),
        "expected_wechat_provider_id": expected_founder_wechat_provider_id() or None,
        "export_platform_founder_only": _export_founder_only(),
        "environment": settings.ENVIRONMENT,
        "stats": {
            "data_exports_logged": exports,
            "access_denied_logged": denied,
            "founder_ops_logged": founder_hits,
        },
        "claims": [
            "访客无法获取服务端源码，仅使用业务接口",
            "创始人运维入口与指定微信绑定",
            "全站数据导出行为留痕，平台级导出仅创始人",
            "国密 SM3/SM4 可用于敏感配置密封",
        ],
    }


def _export_founder_only() -> bool:
    """_export_founder_only。
    :return: 返回处理结果。
    """
    from app.core.config import settings
    raw = getattr(settings, "EXPORT_PLATFORM_FOUNDER_ONLY", True)
    if isinstance(raw, str):
        return raw.lower() in ("1", "true", "yes")
    return bool(raw)
