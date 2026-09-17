# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Legacy APIResponse ↔ UAC 契约桥接（仅 BFF 层使用，不泄漏到 domain）"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi.responses import JSONResponse

logger = logging.getLogger("uj-admin.bff.bridge")


def unwrap_api_envelope(result: Any) -> dict[str, Any]:
    """将 auth 路由返回的 JSONResponse / APIResponse 统一为 {code, message, data}。"""
    if isinstance(result, JSONResponse):
        return json.loads(result.body.decode())
    if hasattr(result, "model_dump"):
        return result.model_dump()
    return result if isinstance(result, dict) else {}


def to_vben_token_pair(token_data: Any) -> dict[str, Any]:
    """内部 snake_case TokenResponse → Vben authStore 驼峰字段。"""
    if hasattr(token_data, "model_dump"):
        raw = token_data.model_dump()
    elif isinstance(token_data, dict):
        raw = token_data
    else:
        raw = {}
    return {
        "accessToken": raw.get("access_token") or raw.get("accessToken"),
        "refreshToken": raw.get("refresh_token") or raw.get("refreshToken"),
        "tokenType": raw.get("token_type") or raw.get("tokenType") or "bearer",
        "expiresIn": raw.get("expires_in") or raw.get("expiresIn"),
        "user": raw.get("user"),
    }


def forward_success_or_legacy(result: Any, transform_data: Any = None) -> Any:
    """成功则包装 UAC 数据，保留 Cookie；失败则原样返回 legacy 响应。"""
    try:
        payload = unwrap_api_envelope(result)
        logger.debug("forward_success_or_legacy: code=%s data_keys=%s", payload.get("code"), list((payload.get("data") or {}).keys()))
        if payload.get("code") != 0:
            return result
        data = payload.get("data")
        if transform_data is not None:
            data = transform_data(data)

        # 如果原始结果已经是 JSONResponse（含 Set-Cookie），直接修改 body 保留 cookies
        if isinstance(result, JSONResponse):
            new_body = {"code": 0, "message": "success", "data": data}
            # 直接修改原始响应的 body，保留所有 Set-Cookie 头
            result.body = json.dumps(new_body).encode("utf-8")
            result.status_code = 200
            return result

        # Legacy APIResponse fallback (no cookies to preserve)
        from app.core.response import success_response
        return success_response(data=data)
    except Exception as exc:
        logger.error("forward_success_or_legacy failed: %s", exc, exc_info=True)
        raise
