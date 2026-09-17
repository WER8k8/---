# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""UB-06：租户可见 API 响应统一品牌脱敏。"""

from __future__ import annotations

import json

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.middleware_fastlane import is_probe_or_static, skip_response_body_rewrite
from app.services.hermes.brand_guard import sanitize_public_data

_BRAND_GUARD_PREFIXES = (
    "/api/v1/ubrain",
    "/api/v1/wangcai",
    "/api/v1/hermes/flywheel",
    "/api/v1/hermes/plugins",
    "/api/v1/client",
    "/api/v1/bff/client",
    "/api/v1/app",
)

_SKIP_PREFIXES = (
    "/api/v1/hermes/ops",
    "/api/v1/hermes/patrol",
    "/api/v1/hermes/plugins/catalog",
)


class BrandGuardResponseMiddleware(BaseHTTPMiddleware):
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

        response = await call_next(request)
        if response.status_code != 200:
            return response
        if not any(path.startswith(p) for p in _BRAND_GUARD_PREFIXES):
            return response
        if any(path.startswith(p) for p in _SKIP_PREFIXES):
            return response
        ct = response.headers.get("content-type") or ""
        if "application/json" not in ct:
            return response

        cl: int | None = None
        if response.headers.get("content-length"):
            try:
                cl = int(response.headers["content-length"])
            except (ValueError, TypeError):
                cl = None
        if skip_response_body_rewrite(path, cl):
            return response

        body = b"".join([chunk async for chunk in response.body_iterator])
        if not body:
            return response
        try:
            payload = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return Response(content=body, status_code=response.status_code, headers=dict(response.headers))

        if isinstance(payload, dict):
            if "data" in payload:
                payload["data"] = sanitize_public_data(payload["data"])
            else:
                payload = sanitize_public_data(payload)
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        headers = {k: v for k, v in response.headers.items() if k.lower() not in ("content-length",)}
        return Response(content=body, status_code=response.status_code, headers=headers, media_type="application/json")
