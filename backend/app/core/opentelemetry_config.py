"""OpenTelemetry配置 - 分布式追踪"""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
from fastapi import FastAPI


def setup_opentelemetry(app: FastAPI, service_name: str = "youding-backend"):
    """配置OpenTelemetry追踪"""
    
    # 创建资源
    resource = Resource.create({
        "service.name": service_name,
        "service.version": "1.0.0",
        "deployment.environment": "production"
    })
    
    # 创建追踪提供者
    tracer_provider = TracerProvider(
        resource=resource,
        sampler=TraceIdRatioBased(1.0)  # 100%采样
    )
    
    # 配置OTLP导出器
    otlp_exporter = OTLPSpanExporter(
        endpoint="http://jaeger:4317",
        insecure=True
    )
    
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
    return trace.get_current_span()


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
