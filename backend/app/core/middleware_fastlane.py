# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""中间件快速通道 — 探针/静态/大响应体跳过昂贵逻辑。

1300+ 路由不会线性拖慢单次请求；主要开销在：
- 多层 BaseHTTPMiddleware 串行
- Unify/BrandGuard 读完整 response body 再 json.loads
- 租户 Host 解析 + DB
- WAF / 限流 / 性能采样
"""

from __future__ import annotations

import os

# 探针、文档、静态 — 跳过响应体解析类中间件
PROBE_OR_STATIC_PREFIXES: tuple[str, ...] = (
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/static",
    "/uploads",
    "/favicon.ico",
)

def is_probe_or_static(path: str) -> bool:
    """is_probe_or_static。

    参数说明：
    :param path: 参数 path
    :return: 返回处理结果。
    """
    if not path:
        return False
    if path == "/":
        return True
    if path in {"/api/v1/health", "/api/v1/health/"}:
        return True
    return any(path == p or path.startswith(p + "/") for p in PROBE_OR_STATIC_PREFIXES)


def body_peek_is_enveloped(body: bytes) -> bool:
    """已含 code 字段的 JSON — 透传即可，无需 json.loads 全量解析。"""
    if not body:
        return False
    head = body.lstrip()[:48]
    return head.startswith(b'{"code"') or head.startswith(b'{ "code"')


def skip_response_body_rewrite(path: str, content_length: int | None) -> bool:
    """大响应 / 静态 / 探针 — 跳过 BrandGuard/Unify body 重写。"""
    if is_probe_or_static(path):
        return True
    max_bytes = int(os.getenv("MIDDLEWARE_MAX_BODY_REWRITE_BYTES", "262144"))
    if content_length is not None and content_length > max_bytes:
        return True
    return False


def perf_sample_enabled() -> bool:
    """性能中间件采样：生产可设 PERF_MIDDLEWARE_SAMPLE_RATE=0.1 降开销。"""
    rate = float(os.getenv("PERF_MIDDLEWARE_SAMPLE_RATE", "1.0"))
    if rate >= 1.0:
        return True
    if rate <= 0:
        return False
    import random
    return random.random() < rate
