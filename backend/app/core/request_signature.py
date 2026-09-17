# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""API 请求签名 + 防重放中间件 — FIX-29: 安全增强

防重放策略：
  - X-Request-Timestamp: 请求时间戳（允许 ±5 分钟窗口）
  - X-Request-Nonce: 一次性随机数（Redis 存储，5 分钟过期）
  - X-Request-Signature: HMAC-SHA256( timestamp + nonce + body_hash, secret )

签名算法：
  signature = HMAC-SHA256(timestamp + ":" + nonce + ":" + body_hash, api_secret)

仅对写操作（POST/PUT/PATCH/DELETE）强制签名验证，读操作（GET）可选。
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
import uuid
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings

log = logging.getLogger(__name__)

# 时间窗口（秒）：允许的时钟偏差
_NONCE_WINDOW_SEC = 300  # 5 分钟
_NONCE_EXPIRE_SEC = 600  # 10 分钟（nonce 过期时间）

# 不需要签名的路径（白名单）
_SKIP_SIGNATURE_PATHS = {
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/api/v1/auth/logout",
    "/api/v1/auth/email-login",
    "/api/v1/auth/oauth-login",
    "/api/v1/health",
    "/api/v1/docs",
    "/api/v1/openapi.json",
    "/api/v1/public/",
    "/api/v1/lead-generation/track-open/",
    "/api/v1/lead-generation/track-click/",
    "/api/v1/tenants/",
    "/api/v1/admin-bff/login",
    "/api/v1/admin-bff/refresh",
    "/api/v1/admin-bff/logout",
    "/api/v1/admin-bff/auth/login",
    "/api/v1/admin-bff/auth/refresh",
    "/api/v1/marketing/events",
    "/api/v1/seo/indexnow/submit",
}


def _compute_body_hash(body: bytes) -> str:
    """计算请求体 SHA256 哈希。"""
    if not body:
        return hashlib.sha256(b"").hexdigest()
    return hashlib.sha256(body).hexdigest()


def _verify_signature(
    timestamp: str,
    nonce: str,
    body_hash: str,
    signature: str,
    secret: str,
) -> bool:
    """验证 HMAC-SHA256 签名。"""
    message = f"{timestamp}:{nonce}:{body_hash}"
    expected = hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def _is_nonce_used(nonce: str) -> bool:
    """检查 nonce 是否已使用（Redis 存储）。"""
    from app.core.cache import get_cache, redis_available, set_cache
    from datetime import timedelta
    if not redis_available():
        # Redis 不可用时允许通过（降级）
        return False

    key = f"nonce:{nonce}"
    if get_cache(key):
        return True
    set_cache(key, "1", expire=timedelta(seconds=_NONCE_EXPIRE_SEC))
    return False


class RequestSignatureMiddleware(BaseHTTPMiddleware):
    """API 请求签名验证中间件。

    仅对 POST/PUT/PATCH/DELETE 请求验证签名。
    GET 请求跳过（但可配置强制验证）。
    """
    async def dispatch(self, request: Request, call_next):
        """dispatch。

        参数说明：
        :param self: 参数 self
        :param request: 参数 request
        :param call_next: 参数 call_next
        :return: 返回处理结果。
        """
        # 跳过签名验证的路径
        path = request.url.path
        for skip_path in _SKIP_SIGNATURE_PATHS:
            if path.startswith(skip_path):
                return await call_next(request)

        # 仅对写操作验证签名
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return await call_next(request)

        # 获取签名头
        timestamp = request.headers.get("X-Request-Timestamp")
        nonce = request.headers.get("X-Request-Nonce")
        signature = request.headers.get("X-Request-Signature")
        # 如果缺少签名头，降级允许（开发环境或未启用）
        if not all([timestamp, nonce, signature]):
            if settings.is_production():
                log.warning(
                    "缺少签名头: path=%s method=%s client=%s",
                    path, request.method, request.client.host if request.client else "unknown",
                )
                return JSONResponse(
                    status_code=401,
                    content={"code": 401, "message": "缺少请求签名头"},
                )
            return await call_next(request)

        # 验证时间戳窗口
        try:
            ts = float(timestamp)
            now = time.time()
            if abs(now - ts) > _NONCE_WINDOW_SEC:
                return JSONResponse(
                    status_code=401,
                    content={"code": 401, "message": "请求时间戳过期"},
                )
        except (ValueError, TypeError):
            return JSONResponse(
                status_code=401,
                content={"code": 401, "message": "无效的时间戳格式"},
            )

        # 验证 nonce 不重复
        if _is_nonce_used(nonce):
            return JSONResponse(
                status_code=401,
                content={"code": 401, "message": "请求已被重放"},
            )

        # 计算请求体哈希
        body = await request.body()
        body_hash = _compute_body_hash(body)
        # 验证签名 - SECURITY: 必须配置 SECRET_KEY，禁止使用默认值
        if not settings.SECRET_KEY:
            log.error("SECRET_KEY 未配置，无法验证签名")
            return JSONResponse(
                status_code=500,
                content={"code": 500, "message": "服务器配置错误"},
            )
        api_secret = settings.SECRET_KEY
        if not _verify_signature(timestamp, nonce, body_hash, signature, api_secret):
            log.warning(
                "签名验证失败: path=%s method=%s client=%s",
                path, request.method, request.client.host if request.client else "unknown",
            )
            return JSONResponse(
                status_code=401,
                content={"code": 401, "message": "签名验证失败"},
            )

        return await call_next(request)


def generate_signed_headers(
    body: bytes = b"",
    secret: Optional[str] = None,
) -> dict[str, str]:
    """生成签名请求头（用于客户端/测试）。

    Args:
        body: 请求体
        secret: API 密钥（默认使用 settings.SECRET_KEY）

    Returns:
        包含 X-Request-* 头的字典

    Raises:
        RuntimeError: 如果 secret 和 settings.SECRET_KEY 都未设置
    """
    # SECURITY: 必须提供密钥，禁止使用默认弱密钥
    secret = secret or settings.SECRET_KEY
    if not secret:
        raise RuntimeError("SECRET_KEY 未配置，无法生成签名")
    timestamp = str(int(time.time()))
    nonce = uuid.uuid4().hex[:16]
    body_hash = _compute_body_hash(body)
    signature = hmac.new(
        secret.encode("utf-8"),
        f"{timestamp}:{nonce}:{body_hash}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return {
        "X-Request-Timestamp": timestamp,
        "X-Request-Nonce": nonce,
        "X-Request-Signature": signature,
    }