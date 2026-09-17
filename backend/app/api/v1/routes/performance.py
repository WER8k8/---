# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""性能优化 API — FIX-66~69

- 异步消息总线
- CDN 配置管理
- Nginx 配置生成
- 可观测性（追踪/指标/健康）
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, Query

from app.core.security import get_current_user
from app.core.response import success_response
from app.services.ubrain.performance_optimization_service import (
    async_message_bus,
    cloudflare_cdn_service,
    nginx_config_generator,
    observability_service,
    AsyncMessage,
    MessagePriority,
    CDNCacheConfig,
)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""
ROUTE_TAGS = ["性能优化"]

router = APIRouter(prefix="/performance", tags=["性能优化"])


# ═══════════════════════════════════════════════════════════
# FIX-66: 异步消息总线
# ═══════════════════════════════════════════════════════════

@router.post("/message-bus/publish")
async def publish_message(
    topic: str = Body(..., description="消息主题"),
    payload: dict[str, Any] = Body(..., description="消息载荷"),
    priority: int = Body(2, ge=0, le=3, description="优先级 0=Critical 1=High 2=Normal 3=Low"),
    correlation_id: str = Body("", description="关联追踪ID"),
    current_user=Depends(get_current_user),
):
    """发布异步消息。"""
    message = AsyncMessage(
        topic=topic,
        payload=payload,
        priority=MessagePriority(priority),
        correlation_id=correlation_id,
    )
    await async_message_bus.publish(message)
    return success_response(data={
        "message_id": message.message_id,
        "topic": topic,
        "published": True,
    })


@router.get("/message-bus/stats")
def message_bus_stats(current_user=Depends(get_current_user)):
    """消息总线统计。"""
    return success_response(data=async_message_bus.get_stats())


@router.post("/message-bus/process")
async def process_message_queue(
    batch_size: int = Body(100, ge=1, le=1000),
    current_user=Depends(get_current_user),
):
    """处理消息队列。"""
    processed = await async_message_bus.process_queue(batch_size=batch_size)
    return success_response(data={"processed": processed})


# ═══════════════════════════════════════════════════════════
# FIX-67: Cloudflare CDN
# ═══════════════════════════════════════════════════════════

@router.post("/cdn/cache-rules")
def generate_cache_rules(
    configs: list[dict] = Body(..., description="缓存配置列表 [{path, ttl, edge_ttl, browser_ttl}]"),
    current_user=Depends(get_current_user),
):
    """生成 Cloudflare 缓存规则。"""
    cdn_configs = [CDNCacheConfig(**c) for c in configs]
    rules = cloudflare_cdn_service.generate_cache_rules(cdn_configs)
    return success_response(data={"rules": rules})


@router.get("/cdn/page-rules")
def get_page_rules(current_user=Depends(get_current_user)):
    """获取常用 Page Rules。"""
    rules = cloudflare_cdn_service.generate_page_rules()
    return success_response(data={"page_rules": rules})


@router.post("/cdn/purge")
def purge_cache(
    urls: list[str] = Body(None, description="要清除的URL列表，空则全部清除"),
    current_user=Depends(get_current_user),
):
    """生成缓存清除请求。"""
    if not cloudflare_cdn_service.is_configured():
        return success_response(data={"error": "Cloudflare CDN 未配置"})
    request = cloudflare_cdn_service.purge_cache_request(urls)
    return success_response(data={"purge_request": request})


@router.get("/cdn/status")
def cdn_status(current_user=Depends(get_current_user)):
    """CDN 服务状态。"""
    return success_response(data={
        "configured": cloudflare_cdn_service.is_configured(),
    })


# ═══════════════════════════════════════════════════════════
# FIX-68: Nginx 配置生成
# ═══════════════════════════════════════════════════════════

@router.post("/nginx/config")
def generate_nginx_config(
    domain: str = Body(..., description="域名"),
    upstream: str = Body(..., description="上游地址如 http://127.0.0.1:8001"),
    cache_path: str = Body("/var/cache/nginx", description="缓存路径"),
    current_user=Depends(get_current_user),
):
    """生成完整 Nginx 配置（含 Brotli + 微缓存 + 静态缓存 + HTTP/3）。"""
    config = nginx_config_generator.generate_full_config(domain, upstream, cache_path)
    return success_response(data={
        "domain": domain,
        "config": config,
    })


@router.get("/nginx/brotli")
def get_brotli_config(current_user=Depends(get_current_user)):
    """获取 Brotli 压缩配置片段。"""
    return success_response(data={"config": nginx_config_generator.generate_brotli_config()})


@router.get("/nginx/micro-cache")
def get_micro_cache_config(
    cache_path: str = Query("/var/cache/nginx", description="缓存路径"),
    current_user=Depends(get_current_user),
):
    """获取微缓存配置片段。"""
    return success_response(data={"config": nginx_config_generator.generate_micro_cache_config(cache_path)})


# ═══════════════════════════════════════════════════════════
# FIX-69: 可观测性
# ═══════════════════════════════════════════════════════════

@router.post("/observability/trace/start")
def start_trace(
    operation: str = Body(..., description="操作名称"),
    trace_id: str = Body("", description="追踪ID（空则自动生成）"),
    parent_span_id: str = Body("", description="父跨度ID"),
    current_user=Depends(get_current_user),
):
    """开始追踪跨度。"""
    span_id = observability_service.start_span(operation, trace_id, parent_span_id)
    return success_response(data={"span_id": span_id, "trace_id": trace_id or "auto"})


@router.post("/observability/trace/end")
def end_trace(
    span_id: str = Body(..., description="跨度ID"),
    tags: dict[str, Any] = Body(None, description="标签"),
    current_user=Depends(get_current_user),
):
    """结束追踪跨度。"""
    span = observability_service.end_span(span_id, tags)
    return success_response(data={
        "span_id": span_id,
        "duration_ms": span.duration_ms() if span else None,
    })


@router.get("/observability/trace/{trace_id}")
def get_trace(
    trace_id: str,
    current_user=Depends(get_current_user),
):
    """获取追踪链。"""
    spans = observability_service.get_trace(trace_id)
    return success_response(data={"trace_id": trace_id, "spans": spans})


@router.post("/observability/metric")
def record_metric(
    name: str = Body(..., description="指标名称"),
    value: float = Body(..., description="指标值"),
    current_user=Depends(get_current_user),
):
    """记录性能指标。"""
    observability_service.record_metric(name, value)
    return success_response(data={"recorded": True, "name": name, "value": value})


@router.get("/observability/metric/{name}")
def get_metric(
    name: str,
    last_n: int = Query(100, ge=1, le=10000),
    current_user=Depends(get_current_user),
):
    """获取指标数据。"""
    points = observability_service.get_metrics(name, last_n)
    return success_response(data={"name": name, "points": points})


@router.get("/observability/health")
def observability_health(current_user=Depends(get_current_user)):
    """可观测性健康检查。"""
    return success_response(data=observability_service.get_health())


@router.get("/observability/summary")
def performance_summary(current_user=Depends(get_current_user)):
    """性能摘要。"""
    return success_response(data=observability_service.get_performance_summary())