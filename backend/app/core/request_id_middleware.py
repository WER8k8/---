# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""请求 ID / trace_id 贯穿中间件（审计 CLOSE-09）。

- 生成或透传 X-Request-ID，写入 contextvars（线程/异步任务间自动透传）
- 通过 logging.Filter 把当前 trace_id 注入每条日志 record
- 响应头回写 X-Request-ID，供前端/网关串联一次请求
- 顺带把根 logger 处理器格式升级为包含 trace_id，保证日志可检索

用法：在 main.py 中以「最外层」方式注册（最后 add_middleware）：
    from app.core.request_id_middleware import RequestIdMiddleware
    app.add_middleware(RequestIdMiddleware)
"""

from __future__ import annotations

import contextvars
import logging
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# 当前请求 trace_id（contextvar，anyio 会自动复制到 worker 线程）
trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "trace_id", default="-"
)


class TraceIdLogFilter(logging.Filter):
    """把当前 trace_id 注入日志 record.trace_id 字段。"""
    def filter(self, record: logging.LogRecord) -> bool:
        """filter。

        参数说明：
        :param self: 参数 self
        :param record: 参数 record
        :return: 返回处理结果。
        """
        record.trace_id = trace_id_var.get("-")
        return True


_FILTER_INSTALLED = False


def _upgrade_handler_formatter(handler: logging.Handler) -> None:
    """把 handler 的 formatter 格式串升级为包含 trace_id（幂等）。"""
    fmt = getattr(handler, "formatter", None)
    if fmt is None:
        return
    try:
        current = getattr(fmt, "_fmt", None)
        if not current or "trace_id" in str(current):
            return
        fmt._fmt = f"{current} [trace_id=%(trace_id)s]"
    except Exception:  # noqa: BLE001 — 格式升级失败不影响请求
        pass


def ensure_trace_id_log_filter() -> None:
    """幂等地把 TraceIdLogFilter 挂到根 logger 全部处理器上。"""
    global _FILTER_INSTALLED
    root = logging.getLogger()
    for handler in root.handlers:
        if not any(isinstance(f, TraceIdLogFilter) for f in handler.filters):
            handler.addFilter(TraceIdLogFilter())
        _upgrade_handler_formatter(handler)
    _FILTER_INSTALLED = True


def _attach_filter_to_new_handlers() -> None:
    """兜底：请求期间动态新增的 handler 也补挂 filter/format。"""
    root = logging.getLogger()
    for handler in root.handlers:
        if not any(isinstance(f, TraceIdLogFilter) for f in handler.filters):
            handler.addFilter(TraceIdLogFilter())
        _upgrade_handler_formatter(handler)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """请求 ID 中间件：生成/透传 X-Request-ID 并注入日志上下文。"""
    async def dispatch(self, request: Request, call_next):
        """dispatch。

        参数说明：
        :param self: 参数 self
        :param request: 参数 request
        :param call_next: 参数 call_next
        :return: 返回处理结果。
        """
        request_id = request.headers.get("x-request-id") or request.headers.get(
            "x-correlation-id"
        )
        if not request_id or len(request_id) > 128:
            request_id = uuid.uuid4().hex[:16]
        token = trace_id_var.set(request_id)
        ensure_trace_id_log_filter()
        try:
            response = await call_next(request)
        finally:
            trace_id_var.reset(token)
            _attach_filter_to_new_handlers()
        response.headers["X-Request-ID"] = request_id
        return response
