# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""创始人专属调试门禁：超管 + 微信唯一（优先）或开发令牌 + 可选 IP。"""

from __future__ import annotations

import ipaddress
import secrets

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.services.founder_wechat_service import (
    founder_wechat_configured,
    user_is_founder,
)

# 延迟导入避免循环依赖
def _log_founder_event(db, user, request, action: str, detail: dict | None = None):
    """_log_founder_event。

    参数说明：
    :param db: 参数 db
    :param user: 参数 user
    :param request: 参数 request
    :param action: 参数 action
    :param detail: 参数 detail
    :return: 返回处理结果。
    """
    from app.services.security_event_service import log_security_event
    log_security_event(
        db,
        action=action,
        user=user,
        detail=detail or {},
        request=request,
    )


def _parse_allowed_ips(raw: str) -> list:
    """_parse_allowed_ips。

    参数说明：
    :param raw: 参数 raw
    :return: 返回处理结果。
    """
    out = []
    for part in (raw or "").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            if "/" in part:
                out.append(ipaddress.ip_network(part, strict=False))
            else:
                out.append(ipaddress.ip_address(part))
        except ValueError:
            continue
    return out


def _client_ip(request: Request) -> str:
    """_client_ip。

    参数说明：
    :param request: 参数 request
    :return: 返回处理结果。
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return ""


def _ip_allowed(client: str, allowed) -> bool:
    """_ip_allowed。

    参数说明：
    :param client: 参数 client
    :param allowed: 参数 allowed
    :return: 返回处理结果。
    """
    if not allowed:
        return True
    try:
        addr = ipaddress.ip_address(client)
    except ValueError:
        return False
    for item in allowed:
        if isinstance(item, (ipaddress.IPv4Network, ipaddress.IPv6Network)):
            if addr in item:
                return True
        elif addr == item:
            return True
    return False


def _check_ip(request: Request) -> None:
    """_check_ip。

    参数说明：
    :param request: 参数 request
    :return: 返回处理结果。
    """
    allowed_ips = _parse_allowed_ips(
        getattr(settings, "FOUNDER_DEBUG_IPS", "") or ""
    )
    client = _client_ip(request)
    if allowed_ips and not _ip_allowed(client, allowed_ips):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"当前 IP ({client}) 不在创始人调试白名单",
        )


def require_super_admin(user: User | None) -> None:
    """require_super_admin。

    参数说明：
    :param user: 参数 user
    :return: 返回处理结果。
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
        )
    if (user.role or "") not in ("super_admin", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅超级管理员可访问创始人调试接口",
        )


def require_founder_debug(
    request: Request,
    user: User,
    db: Session,
    *,
    token_header: str = "X-Founder-Debug-Token",
) -> None:
    """校验：超管 +（创始人微信 或 仅开发令牌）+ 可选 IP。"""
    require_super_admin(user)
    _check_ip(request)
    if founder_wechat_configured():
        if not user_is_founder(db, user):
            key = (
                getattr(settings, "FOUNDER_WECHAT_BIND_KEY", "")
                or getattr(settings, "FOUNDER_WECHAT_OPENID", "")
                or ""
            ).strip()
            hint = f"请使用创始人账号（微信已绑定 {key or '见配置'}）登录"
            from app.services.security_event_service import ACTION_FOUNDER_DENIED
            _log_founder_event(
                db,
                user,
                request,
                ACTION_FOUNDER_DENIED,
                {"reason": "not_founder", "username": user.username},
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=hint,
            )
        from app.services.security_event_service import ACTION_FOUNDER_ACCESS
        _log_founder_event(
            db,
            user,
            request,
            ACTION_FOUNDER_ACCESS,
            {"path": str(request.url.path), "gate": "wechat"},
        )
        return

    expected = (getattr(settings, "FOUNDER_DEBUG_TOKEN", None) or "").strip()
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="未配置 FOUNDER_WECHAT_OPENID 或 FOUNDER_DEBUG_TOKEN，创始人入口已关闭",
        )
    provided = (request.headers.get(token_header) or "").strip()
    if not secrets.compare_digest(provided, expected):
        from app.services.security_event_service import ACTION_FOUNDER_DENIED
        _log_founder_event(
            db,
            user,
            request,
            ACTION_FOUNDER_DENIED,
            {"reason": "bad_token"},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="创始人调试令牌无效（生产请配置 FOUNDER_WECHAT_OPENID）",
        )
    from app.services.security_event_service import ACTION_FOUNDER_ACCESS
    _log_founder_event(
        db,
        user,
        request,
        ACTION_FOUNDER_ACCESS,
        {"path": str(request.url.path), "gate": "token"},
    )


def founder_debug_configured() -> bool:
    """founder_debug_configured。
    :return: 返回处理结果。
    """
    token = (getattr(settings, "FOUNDER_DEBUG_TOKEN", None) or "").strip()
    return founder_wechat_configured() or bool(token)


def founder_gate_mode() -> str:
    """founder_gate_mode。
    :return: 返回处理结果。
    """
    if founder_wechat_configured():
        return "wechat"
    if (getattr(settings, "FOUNDER_DEBUG_TOKEN", None) or "").strip():
        return "token"
    return "none"
