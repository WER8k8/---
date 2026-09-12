"""
将 /api/v1 下「未带 code 字段」的 JSON 成功响应统一包装为 APIResponse，
与 docs/4-API接口定义.md 约定一致；已返回 { code, ... } 的响应原样透传。

排除：
- 飞书 URL 验证等需裸 JSON 的回调
- 非 200、非 application/json、附件下载
"""

from __future__ import annotations

import json

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.middleware_fastlane import body_peek_is_enveloped, skip_response_body_rewrite

# 必须返回原始 JSON，不能包一层 data
EXACT_PATH_PREFIXES: tuple[str, ...] = ("/api/v1/feishu/webhook",)

# 旧版分页：仅含 data + 分页字段、无 code，避免再包成 data: { data: [...] }
_LEGACY_PAGE_KEYS = frozenset({"data", "total", "page", "page_size"})


def _is_legacy_paginated_envelope(payload: dict) -> bool:
    """_is_legacy_paginated_envelope。

    参数说明：
    :param payload: 参数 payload
    :return: 返回处理结果。
    """
    if "code" in payload:
        return False
    keys = set(payload.keys())
    if not keys.issubset(_LEGACY_PAGE_KEYS):
        return False
    return "data" in keys and "total" in keys


class UnifyV1ApiResponseMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        """dispatch。

        参数说明：
        :param self: 参数 self
        :param request: 参数 request
        :param call_next: 参数 call_next
        :return: 返回处理结果。
        """
        response = await call_next(request)
        path = request.url.path
        if not path.startswith("/api/v1"):
            return response
        if any(path.startswith(p) for p in EXACT_PATH_PREFIXES):
            return response
        if response.status_code != 200:
            return response

        cl: int | None = None
        if response.headers.get("content-length"):
            try:
                cl = int(response.headers["content-length"])
            except (ValueError, TypeError):
                cl = None
        if skip_response_body_rewrite(path, cl):
            return response

        cd = response.headers.get("content-disposition") or ""
        if "attachment" in cd.lower():
            return response

        ct = response.headers.get("content-type") or ""
        if "application/json" not in ct:
            return response

        body = await self._read_body(response)
        if not body:
            return response

        if body_peek_is_enveloped(body):
            return self._rebuild_response(response, body, ct)

        try:
            payload = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return self._rebuild_response(response, body, ct)

        if isinstance(payload, dict) and "code" in payload:
            return self._rebuild_response(response, body, ct)

        if isinstance(payload, dict) and _is_legacy_paginated_envelope(payload):
            wrapped = {
                "code": 0,
                "message": "success",
                "data": payload.get("data"),
                "total": payload.get("total"),
                "page": payload.get("page"),
                "page_size": payload.get("page_size"),
            }
            skip = {b"content-length", b"content-type", b"transfer-encoding"}
            resp = Response(
                content=json.dumps(wrapped, ensure_ascii=False),
                status_code=200,
                media_type="application/json")
            for name, value in response.raw_headers:
                if name.lower() not in skip:
                    resp.raw_headers.append((name, value))
            return resp

        wrapped: dict = {
            "code": 0,
            "message": "success",
            "data": payload,
            "total": None,
            "page": None,
            "page_size": None,
        }
        if isinstance(payload, dict):
            if "total" in payload:
                wrapped["total"] = payload.get("total")
            if "page" in payload:
                wrapped["page"] = payload.get("page")
            if "page_size" in payload:
                wrapped["page_size"] = payload.get("page_size")

        skip = {b"content-length", b"content-type", b"transfer-encoding"}
        resp = Response(
            content=json.dumps(wrapped, ensure_ascii=False),
            status_code=200,
            media_type="application/json")
        for name, value in response.raw_headers:
            if name.lower() not in skip:
                resp.raw_headers.append((name, value))
        return resp

    @staticmethod
    async def _read_body(response: Response) -> bytes:
        """_read_body。

        参数说明：
        :param response: 参数 response
        :return: 返回处理结果。
        """
        if getattr(response, "body", None) is not None:
            b = response.body
            return b if isinstance(b, bytes) else bytes(b)
        chunks: list[bytes] = []
        async for chunk in response.body_iterator:
            chunks.append(chunk)
        return b"".join(chunks)

    @staticmethod
    def _passthrough_headers(response: Response) -> dict[str, str]:
        """_passthrough_headers。

        参数说明：
        :param response: 参数 response
        :return: 返回处理结果。
        """
        skip = {"content-length", "content-type", "transfer-encoding"}
        return {k: v for k, v in response.headers.items() if k.lower()
                not in skip}

    @staticmethod
    def _rebuild_response(
            response: Response,
            body: bytes,
            media_type: str) -> Response:
        """_rebuild_response。

        参数说明：
        :param response: 参数 response
        :param body: 参数 body
        :param media_type: 参数 media_type
        :return: 返回处理结果。
        """
        # 必须用 raw_headers 重建，否则多个 Set-Cookie 头会被合并为一个
        skip = {b"content-length", b"content-type", b"transfer-encoding"}
        resp = Response(
            content=body,
            status_code=response.status_code,
            media_type=media_type)
        for name, value in response.raw_headers:
            if name.lower() not in skip:
                resp.raw_headers.append((name, value))
        return resp