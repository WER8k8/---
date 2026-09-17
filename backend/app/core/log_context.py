# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
import contextvars
from typing import Dict, Any, Optional

ctx_tenant_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("ctx_tenant_id", default=None)
ctx_user_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("ctx_user_id", default=None)
ctx_trace_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("ctx_trace_id", default=None)
ctx_request_path: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("ctx_request_path", default=None)

def set_log_context(tenant_id: Optional[str] = None, user_id: Optional[str] = None, trace_id: Optional[str] = None, request_path: Optional[str] = None) -> None:
    if tenant_id is not None:
        ctx_tenant_id.set(tenant_id)
    if user_id is not None:
        ctx_user_id.set(user_id)
    if trace_id is not None:
        ctx_trace_id.set(trace_id)
    if request_path is not None:
        ctx_request_path.set(request_path)

def get_log_context() -> Dict[str, Any]:
    return {
        "tenant_id": ctx_tenant_id.get(),
        "user_id": ctx_user_id.get(),
        "trace_id": ctx_trace_id.get(),
        "request_path": ctx_request_path.get(),
    }

def clear_log_context() -> None:
    ctx_tenant_id.set(None)
    ctx_user_id.set(None)
    ctx_trace_id.set(None)
    ctx_request_path.set(None)
