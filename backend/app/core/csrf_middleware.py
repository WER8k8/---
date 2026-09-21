# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
CSRF Protection Middleware

Applies CSRF token validation to cookie-based (session) requests.
Bearer-token (API-key / JWT) flows are exempt -- they carry their
own authentication proof and are not vulnerable to simple CSRF.

Flow:
  1. GET / HEAD / OPTIONS / TRACE  =>  generate a CSRF token, set it
     as a cookie AND return it in the X-CSRF-Token response header.
  2. POST / PUT / PATCH / DELETE   =>  read the token from the
     X-CSRF-Token request header (or ``_csrf`` form field) and
     compare it against the value stored in the ``csrf_token`` cookie.
     If they do not match, return 403.
"""

import logging

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.security_tools import generate_csrf_token, validate_csrf_token

logger = logging.getLogger("uj-admin.csrf")

# Paths that are always public (no CSRF check needed).
_PUBLIC_PREFIXES: tuple[str, ...] = ("/health", "/docs", "/openapi.json", "/redoc",
                                    "/uploads", "/static", "/favicon")

# Paths that already use Bearer/JWT exclusively -- skip CSRF.
_API_EXEMPT_PREFIXES: tuple[str, ...] = (
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/send-email-code",
    "/api/v1/auth/login-by-email",
    "/api/v1/auth/third-party-login",
    "/api/v1/auth/refresh",
    "/api/v1/admin-bff/auth/login",
    "/api/v1/admin-bff/auth/refresh",
    "/api/v1/admin-bff/auth/logout",
    "/api/v1/admin-bff/logout",
    # 附属项目票据换取与核销（GoodJob / Trade AI）— 跨系统票据协议跳过 CSRF
    "/api/v1/annex",
    # 公开找产品端点（Product Finder）— 无需登录，跳过 CSRF
    "/api/v1/matching",
    # 公开 RFQ 提交端点 — 无需登录，跳过 CSRF
    "/api/v1/rfq",
    # 租户独立域上的匿名公开端点（旺财问答 / agent 可撮合出口的目录·筛货·询盘）。
    # 这一族没有 Cookie 会话可劫持：按 domain 定位租户、只写入公开线索，
    # 防滥用靠各自的限流与幂等键（见 public_agent_storefront），不靠 CSRF。
    # 同时修正既有 POST /public/tenants/{domain}/wangcai/ask 匿名调用会被 403 的问题。
    "/api/v1/public/tenants/",
    # 公开工程计算器端点 — 无需登录，跳过 CSRF
    "/api/v1/calculator",
    # 公开技术问答（基于批准知识库）— 无需登录，跳过 CSRF
    "/api/v1/technical-qna",
    # 谷歌商机大数据与 AI 拓客雷达端点 — 跳过 CSRF
    "/api/v1/google-radar",
    # 获客全链路极智升维端点 — 跳过 CSRF
    "/api/v1/acquisition-pipeline",
    # 国内获客与内贸商机中枢 — 跳过 CSRF
    "/api/v1/domestic-pipeline",
    # 公开询盘表单与谈判 API — 跳过 Cookie CSRF（走 Bearer 或无状态提交）
    "/api/v1/inquiries",
    "/api/v1/negotiation",
    "/api/v1/logistics",
    "/api/v1/orders",
    "/api/v1/marketing",
    "/api/v1/seo/indexnow",
)

_WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


_COOKIE_NAME = "csrf_token"
_COOKIE_MAX_AGE = 3600  # 1 hour


def _is_exempt(path: str) -> bool:
    """Return True if the path should skip CSRF entirely."""
    for prefix in _PUBLIC_PREFIXES:
        if path.startswith(prefix):
            return True
    return False


def _has_bearer_token(request: Request) -> bool:
    """Detect Bearer-token auth -- these requests are exempt from CSRF."""
    auth = request.headers.get("authorization", "")
    return auth.lower().startswith("bearer ")


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    Double-Submit Cookie CSRF Protection.

    - Safe methods (GET/HEAD/OPTIONS): set a random ``csrf_token`` cookie.
    - Unsafe methods (POST/PUT/PATCH/DELETE):
        * Skip if the request carries a Bearer token.
        * Otherwise require the ``X-CSRF-Token`` header to match the cookie.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        """dispatch。

        参数说明：
        :param self: 参数 self
        :param request: 参数 request
        :param call_next: 参数 call_next
        :return: 返回处理结果。
        """
        path = request.url.path
        # Exempt public/static paths
        if _is_exempt(path):
            return await call_next(request)

        # Bearer-token auth is exempt
        if _has_bearer_token(request):
            return await call_next(request)

        # For write methods, validate the CSRF token from cookie-based flows
        if request.method in _WRITE_METHODS:
            # Skip CSRF for login/register (they set the session, chicken-and-egg)
            for exempt_prefix in _API_EXEMPT_PREFIXES:
                if path.startswith(exempt_prefix):
                    return await call_next(request)

            cookie_token = request.cookies.get(_COOKIE_NAME, "")
            header_token = (
                request.headers.get("X-CSRF-Token", "")
                or request.headers.get("X-CSRFToken", "")
                or request.headers.get("x-csrf-token", "")
            )
            # Also check form body fallback
            if not header_token:
                try:
                    body = await request.form()
                    header_token = str(body.get("_csrf", ""))
                except Exception:
                    pass

            if not cookie_token or not header_token:
                return JSONResponse(
                    status_code=403,
                    content={
                        "code": 403,
                        "message": "CSRF token missing. Refresh the page and try again.",
                    },
                )

            if not validate_csrf_token(header_token, cookie_token):
                logger.warning(
                    "CSRF token mismatch: path=%s ip=%s",
                    path,
                    request.client.host if request.client else "unknown",
                )
                return JSONResponse(
                    status_code=403,
                    content={
                        "code": 403,
                        "message": "CSRF token invalid. Refresh the page and try again.",
                    },
                )

        # Process the request
        response = await call_next(request)
        # On safe methods, issue/refresh the CSRF cookie
        if request.method in ("GET", "HEAD", "OPTIONS"):
            token = generate_csrf_token()
            # Set cookie with httponly=True to prevent XSS from reading the token.
            # The token is also sent via the X-CSRF-Token response header so
            # legitimate JS can read it from the header instead of the cookie.
            response.set_cookie(
                key=_COOKIE_NAME,
                value=token,
                max_age=_COOKIE_MAX_AGE,
                httponly=True,
                samesite="strict",
                secure=settings.ENVIRONMENT == "production",
            )
            # Also expose the token in a response header
            response.headers["X-CSRF-Token"] = token

        return response
