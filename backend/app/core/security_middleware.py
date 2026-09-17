# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""安全中间件模块 — 路径安全 + 限流

注意：SQL注入/XSS/路径遍历/命令注入检测已统一由 WAFMiddleware (waf.py) 处理，
本模块不再重复检测，避免规则冲突和性能开销翻倍。
"""

import ipaddress
import re
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.middleware_fastlane import is_probe_or_static
from app.core.response import APIResponse

# 危险路径模式（路径遍历检测保留在SecurityMiddleware，WAF通过路径前缀白名单跳过某些请求）
DANGEROUS_PATHS = [
    r"(\.\./|\.\.)",  # 路径遍历
    r"(etc/passwd|etc/shadow|proc/self/environ)",  # 敏感文件访问
]

# Trusted proxy CIDR ranges — X-Forwarded-For is only trusted when the
# direct client IP falls within one of these networks.
_TRUSTED_PROXY_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]


def _is_trusted_proxy(ip_str: str) -> bool:
    """Return True if *ip_str* belongs to a trusted proxy network."""
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    return any(addr in net for net in _TRUSTED_PROXY_NETWORKS)


class SecurityMiddleware(BaseHTTPMiddleware):
    """安全中间件 — 路径安全检查

    SQL/XSS/命令注入检测统一由 WAFMiddleware 处理。
    本中间件仅负责路径遍历防御（WAF白名单路径仍需保护）。
    """
    async def dispatch(self, request: Request, call_next):
        """dispatch。

        参数说明：
        :param self: 参数 self
        :param request: 参数 request
        :param call_next: 参数 call_next
        :return: 返回处理结果。
        """
        path = request.url.path
        if is_probe_or_static(path):
            return await call_next(request)

        # 路径安全检查（防止路径遍历攻击穿越WAF白名单）
        if self._is_dangerous_path(path):
            return JSONResponse(
                status_code=403, content=APIResponse(
                    code=403, message="访问路径不安全").model_dump())

        return await call_next(request)

    def _is_dangerous_path(self, path: str) -> bool:
        """检查路径是否危险"""
        for pattern in DANGEROUS_PATHS:
            if re.search(pattern, path, re.IGNORECASE):
                return True
        return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""
    def __init__(
        self,
        app,
        max_requests: int = settings.RATE_LIMIT_MAX_REQUESTS,
        window_seconds: int = settings.RATE_LIMIT_WINDOW_SECONDS,
    ):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param app: 参数 app
        :param max_requests: 参数 max_requests
        :param window_seconds: 参数 window_seconds
        :return: 返回处理结果。
        """
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_counts = {}  # {ip: {"count": int, "window_start": datetime}}

    async def dispatch(self, request: Request, call_next):
        """dispatch。

        参数说明：
        :param self: 参数 self
        :param request: 参数 request
        :param call_next: 参数 call_next
        :return: 返回处理结果。
        """
        path = request.url.path
        if is_probe_or_static(path):
            return await call_next(request)

        # 仅本地请求跳过限流，生产环境全量生效
        client_host = request.client.host if request.client else None
        if client_host in ("127.0.0.1", "::1", "localhost"):
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        path = request.url.path
        # ── Redis 限流（多 worker 共享，原子计数）──
        if settings.REDIS_ENABLED:
            try:
                from app.core.cache import redis_client as _redis
                if _redis:
                    key = f"ratelimit:{client_ip}:{path}"
                    count = _redis.incr(key)
                    if count == 1:
                        _redis.expire(key, self.window_seconds)
                    if count > self.max_requests:
                        return JSONResponse(
                            status_code=429,
                            content=APIResponse(
                                code=429,
                                message="请求过于频繁，请稍后再试",
                            ).model_dump(),
                        )
                    response = await call_next(request)
                    return response
            except Exception:
                pass  # Redis 不可用时降级到内存限流

        # ── 内存限流（开发模式 / Redis 不可用时回退）──
        now = datetime.now()
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = {"count": 1, "window_start": now}
        else:
            window_start = self.request_counts[client_ip]["window_start"]
            # 检查窗口是否过期
            if now - window_start > timedelta(seconds=self.window_seconds):
                self.request_counts[client_ip] = {
                    "count": 1, "window_start": now}
            else:
                self.request_counts[client_ip]["count"] += 1

        count = self.request_counts[client_ip]["count"]
        if count > self.max_requests:
            return JSONResponse(
                status_code=429,
                content=APIResponse(
                    code=429,
                    message="请求过于频繁，请稍后再试",
                ).model_dump(),
            )

        # 清理过期记录
        self._cleanup_expired_records(now)
        response = await call_next(request)
        return response

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP

        安全说明:
        - X-Forwarded-For 仅在直接连接来自可信代理时才信任。
        - 可信代理范围: 127.0.0.1/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16.
        """
        direct_ip_str = request.client.host if request.client else None
        if direct_ip_str and _is_trusted_proxy(direct_ip_str):
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                return forwarded.split(",")[0].strip()
        if direct_ip_str:
            return direct_ip_str
        return "127.0.0.1"

    def _cleanup_expired_records(self, now: datetime):
        """清理过期的请求记录"""
        expired_ips = []
        for ip, data in self.request_counts.items():
            if now - \
                    data["window_start"] > timedelta(seconds=self.window_seconds):
                expired_ips.append(ip)

        for ip in expired_ips:
            del self.request_counts[ip]
