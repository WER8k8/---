# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""生产路径出站 JSON 假交付扫描中间件。"""

from __future__ import annotations

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.no_fake_delivery import is_production_environment
from app.core.no_fake_delivery_guard import scan_response_bytes, should_scan_path

logger = logging.getLogger("no_fake_delivery")


class NoFakeDeliveryResponseMiddleware(BaseHTTPMiddleware):
    """生产环境：拦截含未门控 mock/演示信号的 200 JSON 响应。"""
    async def dispatch(self, request: Request, call_next):
        """dispatch。

        参数说明：
        :param self: 参数 self
        :param request: 参数 request
        :param call_next: 参数 call_next
        :return: 返回处理结果。
        """
        response = await call_next(request)
        if not is_production_environment():
            return response

        path = request.url.path
        if not should_scan_path(path):
            return response
        if response.status_code != 200:
            return response

        ct = (response.headers.get("content-type") or "").lower()
        if "application/json" not in ct:
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        if not body:
            return self._rebuild(response, body)

        violations = scan_response_bytes(body, request_path=path)
        if violations:
            logger.error(
                "FAKE_DELIVERY_BLOCKED path=%s violations=%s",
                path,
                violations[:5],
            )
            return JSONResponse(
                status_code=503,
                content={
                    "code": 503,
                    "message": "生产路径拒绝假交付响应",
                    "data": {
                        "error_code": "FAKE_DELIVERY_BLOCKED",
                        "violations": violations,
                        "path": path,
                    },
                },
            )

        return self._rebuild(response, body)

    @staticmethod
    def _rebuild(response: Response, body: bytes) -> Response:
        """_rebuild。

        参数说明：
        :param response: 参数 response
        :param body: 参数 body
        :return: 返回处理结果。
        """
        headers = dict(response.headers)
        headers.pop("content-length", None)
        return Response(
            content=body,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type,
        )
