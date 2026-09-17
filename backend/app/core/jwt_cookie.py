# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""JWT HttpOnly Cookie 工具 — FIX-22: 安全升级，Token 不再暴露给 JavaScript。

生产环境 Cookie 属性：
  - access_token:  HttpOnly, Secure, SameSite=Lax,  Path=/         (expires=token_expiry)
  - refresh_token: HttpOnly, Secure, SameSite=Strict, Path=/api/v1/auth/refresh
  - user_info:     HttpOnly, SameSite=Lax, Path=/  (前端通过 bffUserInfo API 获取)

开发环境:
  - Secure=False (允许 HTTP localhost)
  - Domain 不设（默认当前域）
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi.responses import JSONResponse, Response

from app.core.config import settings
from app.models.user import User


def _cookie_opts(
    http_only: bool = True,
    path: str = "/",
    max_age_seconds: int = 0,
    same_site: str = "lax",
) -> dict:
    """构建 Cookie 通用属性。"""
    opts: dict = {
        "httponly": http_only,
        "samesite": same_site,
        "secure": settings.JWT_COOKIE_SECURE,
        "path": path,
    }
    if max_age_seconds > 0:
        opts["max_age"] = max_age_seconds
    if settings.JWT_COOKIE_DOMAIN:
        opts["domain"] = settings.JWT_COOKIE_DOMAIN
    return opts


def set_auth_cookies(
    response: JSONResponse,
    access_token: str,
    refresh_token: str,
    user: User,
) -> None:
    """登录/刷新成功后设置 HttpOnly Cookie。

    - access_token:  HttpOnly, SameSite=Lax, Path=/
    - refresh_token: HttpOnly, SameSite=Strict, Path=/api/v1/auth/refresh
    - user_info:     HttpOnly, SameSite=Lax, Path=/ (前端通过 bffUserInfo API 获取)
    """
    access_max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    refresh_max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
    # Access Token Cookie
    response.set_cookie(
        key=settings.JWT_COOKIE_NAME,
        value=access_token,
        **_cookie_opts(
            http_only=True,
            path=settings.JWT_COOKIE_PATH,
            max_age_seconds=access_max_age,
            same_site=settings.JWT_COOKIE_SAMESITE,
        ),
    )
    # Refresh Token Cookie（仅 refresh 端点可见）
    response.set_cookie(
        key=settings.JWT_REFRESH_COOKIE_NAME,
        value=refresh_token,
        **_cookie_opts(
            http_only=True,
            path=settings.JWT_REFRESH_COOKIE_PATH,
            max_age_seconds=refresh_max_age,
            same_site="strict",
        ),
    )
    # SECURITY: User Info Cookie 设为 HttpOnly，防止 XSS 泄露
    # 前端通过 bffUserInfo API 获取用户信息
    user_info = json.dumps({
        "id": str(user.id),
        "username": user.username,
        "role": user.role,
        "home_path": resolve_home_path_for_role(user.role),
    })
    response.set_cookie(
        key=settings.JWT_USER_INFO_COOKIE_NAME,
        value=user_info,
        **_cookie_opts(
            http_only=True,
            path=settings.JWT_COOKIE_PATH,
            max_age_seconds=access_max_age,
            same_site=settings.JWT_COOKIE_SAMESITE,
        ),
    )


def clear_auth_cookies(response: JSONResponse) -> None:
    """登出时清除所有 Auth Cookie。

    除当前配置外，同时删除历史 Domain 变体（localhost / 127.0.0.1）：
    早期部署曾以 Domain 属性下发 cookie，仅按 host-only 删除会残留
    域 cookie，导致"登出后刷新接口仍复活会话"。
    """
    domain_variants: list[Optional[str]] = [settings.JWT_COOKIE_DOMAIN or None, "localhost", "127.0.0.1"]
    for name, path in [
        (settings.JWT_COOKIE_NAME, settings.JWT_COOKIE_PATH),
        (settings.JWT_REFRESH_COOKIE_NAME, settings.JWT_REFRESH_COOKIE_PATH),
        (settings.JWT_USER_INFO_COOKIE_NAME, settings.JWT_COOKIE_PATH),
    ]:
        # host-only（无 Domain）删除
        response.delete_cookie(
            key=name,
            path=path,
            secure=settings.JWT_COOKIE_SECURE,
            httponly=True,
            samesite=settings.JWT_COOKIE_SAMESITE,
        )
        # 历史域 cookie 变体删除（去重）
        seen: set[str] = set()
        for domain in domain_variants:
            if not domain or domain in seen:
                continue
            seen.add(domain)
            response.delete_cookie(
                key=name,
                path=path,
                domain=domain,
                secure=settings.JWT_COOKIE_SECURE,
                httponly=True,
                samesite=settings.JWT_COOKIE_SAMESITE,
            )


def _pick_latest_valid_cookie(request, name: str) -> Optional[str]:
    """同名 cookie 存在多份（历史 Domain/Path 变体残留）时，选 exp 最新的有效 token。

    浏览器对重复 cookie 的发送顺序随 path/创建时间变化，而 Starlette
    request.cookies 取最后一个值——若残留的已撤销 token 恰好排最后，
    请求会随机 401（"浏览中会话被踢"）。按 exp 取最新可中和该竞态。
    """
    header = request.headers.get("cookie", "")
    values: list[str] = []
    for part in header.split(";"):
        k, _, v = part.strip().partition("=")
        if k == name and v:
            values.append(v)
    if len(values) <= 1:
        return request.cookies.get(name)
    from app.core.jwt_key_rotation import jwt_key_rotation_service
    best: Optional[str] = None
    best_exp = -1.0
    for v in values:
        try:
            payload = jwt_key_rotation_service.decode_token(v)
        except Exception:
            continue
        if not payload:
            continue
        try:
            exp = float(payload.get("exp") or 0)
        except (TypeError, ValueError):
            continue
        if exp >= best_exp:
            best, best_exp = v, exp
    return best or values[-1]


def extract_token_from_cookie(request) -> Optional[str]:
    """从 Cookie 中提取 access_token（HttpOnly Cookie 方案）。

    优先从 Authorization Header 读取（兼容旧客户端），
    否则从 Cookie 读取。
    """
    # 优先：Authorization Header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]

    # 回退：HttpOnly Cookie（多份重复时取最新有效）
    return _pick_latest_valid_cookie(request, settings.JWT_COOKIE_NAME)


def extract_refresh_token_from_cookie(request) -> Optional[str]:
    """从 Cookie 中提取 refresh_token。"""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]

    return _pick_latest_valid_cookie(request, settings.JWT_REFRESH_COOKIE_NAME)


def resolve_home_path_for_role(role: str) -> str:
    """角色 → 默认首页路径。"""
    home_map = {
        "admin": "/admin",
        "super_admin": "/admin",
        "tenant_admin": "/client/today",
        "editor": "/client/today",
        "agent": "/agent/performance",
        "sales": "/agent/performance",
        "l2": "/agent/performance",
        "l3": "/agent/performance",
    }
    return home_map.get(role, "/client/today")