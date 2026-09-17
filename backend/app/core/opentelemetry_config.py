# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""OpenTelemetry配置 - 分布式追踪 (租户隔离增强)

所有 Span 强制携带 tenant_id attribute，确保：
- 追踪数据可按租户维度过滤和分析
- 多租户环境下便于定位和排查问题
- 与日志、监控体系保持一致的租户上下文
"""

import logging
import contextvars
from typing import Any, Optional

from fastapi import FastAPI

log = logging.getLogger(__name__)

# 标准库 contextvars 降级垫片（当 opentelemetry 未装或缺少 protobuf 时确保 RLS 租户注入 100% 正常运作）
_FALLBACK_TENANT_ID: contextvars.ContextVar[str] = contextvars.ContextVar("tenant_id", default="")
_FALLBACK_TENANT_NAME: contextvars.ContextVar[str] = contextvars.ContextVar("tenant_name", default="")

try:
    from opentelemetry import context, trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import \
        OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
    _OPENTELEMETRY_AVAILABLE = True
except Exception as _otel_err:
    log.debug("OpenTelemetry optional packages not fully installed, using fallback context: %s", _otel_err)
    context = None
    trace = None
    _OPENTELEMETRY_AVAILABLE = False

# 租户 context key —— 用于在请求上下文中传递 tenant_id
_TENANT_CONTEXT_KEY = "tenant_id"
_SPAN_ATTR_TENANT_ID = "tenant.id"
_SPAN_ATTR_TENANT_NAME = "tenant.name"


def set_tenant_span_attributes(
    tenant_id: str,
    tenant_name: str = "",
) -> None:
    """为当前 Span 设置租户属性。

    在请求入口（如中间件）调用此函数，将 tenant_id 注入当前 Span。
    Span 追踪数据可在 Jaeger/Tempo 等系统中按租户过滤。

    Args:
        tenant_id: 租户 UUID
        tenant_name: 租户名称（可选）

    Example:
        # 在 TenantMiddleware.dispatch 中调用:
        set_tenant_span_attributes(
            tenant_id=tenant_info["id"],
            tenant_name=tenant_info["name"],
        )

        # 在服务层调用:
        set_tenant_span_attributes(tenant_id="abc123")
    """
    # 写入 contextvars 垫片
    _FALLBACK_TENANT_ID.set(tenant_id or "")
    if tenant_name:
        _FALLBACK_TENANT_NAME.set(tenant_name)

    span = get_current_span()
    if span and hasattr(span, "is_recording") and span.is_recording():
        span.set_attribute(_SPAN_ATTR_TENANT_ID, tenant_id)
        if tenant_name:
            span.set_attribute(_SPAN_ATTR_TENANT_NAME, tenant_name)

    # 同时写入 OpenTelemetry context（若可用），供下游传播
    if context is not None:
        try:
            ctx = context.set_value(_TENANT_CONTEXT_KEY, tenant_id)
            context.attach(ctx)
        except Exception:
            pass


def get_tenant_from_context() -> str:
    """从当前 OpenTelemetry context 或 contextvars 中提取 tenant_id。

    Returns:
        当前租户 ID，如果未设置则返回空字符串
    """
    if context is not None:
        try:
            val = context.get_value(_TENANT_CONTEXT_KEY)
            if val:
                return str(val)
        except Exception:
            pass
    return _FALLBACK_TENANT_ID.get() or ""


def clear_tenant_context() -> None:
    """清除当前上下文中的租户信息。"""
    _FALLBACK_TENANT_ID.set("")
    _FALLBACK_TENANT_NAME.set("")
    if context is not None:
        try:
            ctx = context.set_value(_TENANT_CONTEXT_KEY, None)
            context.attach(ctx)
        except Exception:
            pass


def setup_opentelemetry(app: FastAPI, service_name: str = "youding-backend"):
    """配置OpenTelemetry追踪（若未安装对应包则优雅降级为 noop）"""
    if not _OPENTELEMETRY_AVAILABLE:
        log.info("OpenTelemetry not enabled or dependencies missing, running in degraded tracing mode.")
        return None

    # 创建资源
    resource = Resource.create({"service.name": service_name,
                                "service.version": "1.0.0",
                                "deployment.environment": "production"})

    # 创建追踪提供者
    tracer_provider = TracerProvider(
        resource=resource,
        sampler=TraceIdRatioBased(1.0))  # 100%采样

    # 配置OTLP导出器
    otlp_exporter = OTLPSpanExporter(
        endpoint="http://jaeger:4317", insecure=True)

    # 添加批量Span处理器
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)
    # 设置全局追踪提供者
    trace.set_tracer_provider(tracer_provider)
    # 自动检测FastAPI
    FastAPIInstrumentor.instrument_app(app)
    # 检测SQLAlchemy
    try:
        from app.db.session import engine
        SQLAlchemyInstrumentor().instrument(engine=engine)
    except Exception:
        pass

    # 检测Redis
    try:
        RedisInstrumentor().instrument()
    except Exception:
        pass

    return trace.get_tracer(service_name)


def get_current_span():
    """获取当前Span"""
    if trace is not None:
        try:
            return trace.get_current_span()
        except Exception:
            return None
    return None


def add_event_to_span(event_name: str, attributes: dict = None):
    """向当前Span添加事件"""
    span = get_current_span()
    if span and span.is_recording():
        span.add_event(event_name, attributes)


def set_span_attribute(key: str, value):
    """设置Span属性"""
    span = get_current_span()
    if span and span.is_recording():
        span.set_attribute(key, value)
