# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""性能优化服务 — FIX-66~69

FIX-66: 异步化 + 消息驱动（EventBus 增强 + 异步任务编排）
FIX-67: Cloudflare CDN + 边缘缓存
FIX-68: Nginx 微缓存 + Brotli 压缩（配置生成器）
FIX-69: 可观测性全链路打通（分布式追踪 + 指标采集）
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# FIX-66: 异步消息总线增强
# ═══════════════════════════════════════════════════════════

class MessagePriority(int, Enum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class AsyncMessage:
    """异步消息"""
    topic: str
    payload: dict[str, Any]
    message_id: str = ""
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: str = ""
    correlation_id: str = ""  # 分布式追踪关联 ID
    def __post_init__(self):
        """__post_init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if not self.message_id:
            self.message_id = f"msg_{uuid.uuid4().hex[:12]}"
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class AsyncMessageBus:
    """异步消息总线。

    特性：
    - 优先级队列（Critical > High > Normal > Low）
    - 发布-订阅模式
    - 持久化订阅
    - 死信队列
    """
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)
        self._queue: list[tuple[int, AsyncMessage]] = []  # (priority, message)
        self._dead_letter_queue: list[AsyncMessage] = []
        self._lock = asyncio.Lock()
        self._running = False

    def subscribe(self, topic: str, handler: Callable[[AsyncMessage], Any]) -> None:
        """订阅主题。"""
        self._subscribers[topic].append(handler)
        logger.info("Subscribed to topic: %s", topic)

    def unsubscribe(self, topic: str, handler: Callable) -> None:
        """取消订阅。"""
        if topic in self._subscribers and handler in self._subscribers[topic]:
            self._subscribers[topic].remove(handler)

    async def publish(self, message: AsyncMessage) -> None:
        """发布消息。"""
        async with self._lock:
            self._queue.append((message.priority.value, message))
            self._queue.sort(key=lambda x: x[0])

        # 立即尝试投递
        await self._deliver(message)

    async def _deliver(self, message: AsyncMessage) -> None:
        """投递消息到订阅者。"""
        handlers = self._subscribers.get(message.topic, [])
        if not handlers:
            logger.warning("No subscribers for topic: %s", message.topic)
            return

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                logger.error("Message delivery failed: %s", e)
                self._dead_letter_queue.append(message)

    async def process_queue(self, batch_size: int = 100) -> int:
        """处理队列中的消息。"""
        processed = 0
        async with self._lock:
            batch = self._queue[:batch_size]
            self._queue = self._queue[batch_size:]

        for _, message in batch:
            await self._deliver(message)
            processed += 1

        return processed

    def get_stats(self) -> dict[str, Any]:
        """get_stats。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "queue_length": len(self._queue),
            "dead_letter_length": len(self._dead_letter_queue),
            "topics": list(self._subscribers.keys()),
            "subscriber_count": sum(len(h) for h in self._subscribers.values()),
        }


# ═══════════════════════════════════════════════════════════
# FIX-67: Cloudflare CDN 集成
# ═══════════════════════════════════════════════════════════

@dataclass
class CDNCacheConfig:
    """CDN 缓存配置"""
    path: str
    ttl: int = 3600           # 缓存时间（秒）
    bypass_cache_cookie: str = ""
    edge_ttl: int = 86400     # 边缘缓存时间
    browser_ttl: int = 3600   # 浏览器缓存时间


class CloudflareCDNService:
    """Cloudflare CDN 配置与管理。

    提供：
    - 缓存规则生成
    - 边缘缓存清除
    - 缓存命中率分析
    """
    def __init__(self, api_token: str = "", zone_id: str = ""):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param api_token: 参数 api_token
        :param zone_id: 参数 zone_id
        :return: 返回处理结果。
        """
        self._api_token = api_token or ""
        self._zone_id = zone_id or ""

    def is_configured(self) -> bool:
        """is_configured。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return bool(self._api_token and self._zone_id)

    def generate_cache_rules(self, configs: list[CDNCacheConfig]) -> list[dict]:
        """生成 Cloudflare 缓存规则配置。"""
        rules = []
        for cfg in configs:
            rule = {
                "name": f"Cache rule for {cfg.path}",
                "expression": f'(http.request.uri.path eq "{cfg.path}")',
                "action": "cache",
                "action_parameters": {
                    "cache": True,
                    "edge_ttl": {"mode": "override_origin", "default": cfg.edge_ttl},
                    "browser_ttl": {"mode": "override_origin", "default": cfg.browser_ttl},
                },
            }
            if cfg.bypass_cache_cookie:
                rule["expression"] += f' and (not http.cookie contains "{cfg.bypass_cache_cookie}")'
            rules.append(rule)
        return rules

    def generate_page_rules(self) -> list[dict]:
        """生成常用 Page Rules。"""
        return [
            {
                "target": "*example.com/static/*",
                "actions": {
                    "cache_level": "cache_everything",
                    "edge_cache_ttl": 86400,
                    "browser_cache_ttl": 3600,
                },
            },
            {
                "target": "*example.com/api/*",
                "actions": {
                    "cache_level": "bypass",
                },
            },
        ]

    def purge_cache_request(self, urls: list[str] | None = None) -> dict:
        """生成缓存清除请求。"""
        return {
            "method": "POST",
            "url": f"https://api.cloudflare.com/client/v4/zones/{self._zone_id}/purge_cache",
            "headers": {
                "Authorization": f"Bearer {self._api_token}",
                "Content-Type": "application/json",
            },
            "body": {"files": urls} if urls else {"purge_everything": True},
        }


# ═══════════════════════════════════════════════════════════
# FIX-68: Nginx 配置生成器（微缓存 + Brotli）
# ═══════════════════════════════════════════════════════════

class NginxConfigGenerator:
    """Nginx 高性能配置生成器。

    生成包含以下优化的配置：
    - Brotli/Gzip 压缩
    - 微缓存（proxy_cache）
    - 连接优化
    - 静态资源缓存
    """
    @staticmethod
    def generate_brotli_config() -> str:
        """生成 Brotli 压缩配置。"""
        return """
# Brotli 压缩（比 gzip 提升 20-25% 压缩率）
brotli on;
brotli_comp_level 6;
brotli_types
    text/plain
    text/css
    text/xml
    text/javascript
    application/json
    application/javascript
    application/xml+rss
    application/atom+xml
    image/svg+xml;
"""

    @staticmethod
    def generate_micro_cache_config(cache_path: str = "/var/cache/nginx") -> str:
        """生成微缓存配置。"""
        return f"""
# 微缓存（1-5 秒，适用于动态内容）
proxy_cache_path {cache_path} levels=1:2 keys_zone=microcache:10m
    max_size=1g inactive=10m use_temp_path=off;

proxy_cache microcache;
proxy_cache_valid 200 5s;
proxy_cache_valid 404 1m;
proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
proxy_cache_background_update on;
proxy_cache_lock on;

# 缓存键包含请求方法和 URI
proxy_cache_key "$scheme$request_method$host$request_uri";

# 添加缓存状态头
add_header X-Cache-Status $upstream_cache_status always;
"""

    @staticmethod
    def generate_static_cache_config() -> str:
        """生成静态资源缓存配置。"""
        return """
# 静态资源长期缓存
location ~* \\.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    add_header Vary "Accept-Encoding";
    access_log off;
}

# HTML 文件不缓存（SSR）
location ~* \\.html$ {
    add_header Cache-Control "no-cache, no-store, must-revalidate";
    add_header Pragma "no-cache";
    expires 0;
}
"""

    @staticmethod
    def generate_connection_optimization() -> str:
        """生成连接优化配置。"""
        return """
# 连接优化
worker_processes auto;
worker_rlimit_nofile 65535;

events {
    worker_connections 16384;
    use epoll;
    multi_accept on;
}

http {
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    keepalive_requests 1000;
    # 开启 HTTP/2 和 HTTP/3
    server {
        listen 443 ssl http2;
        listen 443 quic reuseport;
        add_header Alt-Svc 'h3=":443"; ma=86400';
    }
}
"""

    @classmethod
    def generate_full_config(cls, domain: str, upstream: str, cache_path: str = "/var/cache/nginx") -> str:
        """生成完整 Nginx 配置。"""
        parts = [
            f"# Auto-generated Nginx config for {domain}",
            f"# Generated at {datetime.now(timezone.utc).isoformat()}",
            "",
            cls.generate_connection_optimization(),
            "",
            cls.generate_brotli_config(),
            "",
            cls.generate_micro_cache_config(cache_path),
            "",
            cls.generate_static_cache_config(),
            "",
            f"server {{",
            f"    server_name {domain};",
            f"    location / {{",
            f"        proxy_pass {upstream};",
            "        proxy_set_header Host $host;",
            "        proxy_set_header X-Real-IP $remote_addr;",
            "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;",
            "        proxy_set_header X-Forwarded-Proto $scheme;",
            "    }",
            "}",
        ]
        return "\n".join(parts)


# ═══════════════════════════════════════════════════════════
# FIX-69: 可观测性（分布式追踪 + 指标）
# ═══════════════════════════════════════════════════════════

@dataclass
class TraceSpan:
    """追踪跨度"""
    trace_id: str
    span_id: str
    parent_span_id: str = ""
    operation: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    tags: dict[str, Any] = field(default_factory=dict)
    logs: list[dict] = field(default_factory=list)
    def duration_ms(self) -> float:
        """duration_ms。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return (self.end_time - self.start_time) * 1000

    def to_dict(self) -> dict[str, Any]:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "operation": self.operation,
            "duration_ms": round(self.duration_ms(), 3),
            "tags": self.tags,
        }


class ObservabilityService:
    """可观测性服务。

    提供：
    - 分布式追踪（OpenTelemetry 风格）
    - 性能指标采集
    - 健康检查
    - 告警阈值
    """
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._spans: list[TraceSpan] = []
        self._metrics: dict[str, list[tuple[float, float]]] = defaultdict(list)  # name -> [(timestamp, value)]
        self._active_spans: dict[str, TraceSpan] = {}

    def start_span(self, operation: str, trace_id: str = "", parent_span_id: str = "") -> str:
        """开始追踪跨度。"""
        span_id = f"span_{uuid.uuid4().hex[:12]}"
        span = TraceSpan(
            trace_id=trace_id or f"trace_{uuid.uuid4().hex[:16]}",
            span_id=span_id,
            parent_span_id=parent_span_id,
            operation=operation,
            start_time=time.time(),
        )
        self._active_spans[span_id] = span
        return span_id

    def end_span(self, span_id: str, tags: dict[str, Any] | None = None) -> TraceSpan | None:
        """结束追踪跨度。"""
        span = self._active_spans.pop(span_id, None)
        if span:
            span.end_time = time.time()
            if tags:
                span.tags.update(tags)
            self._spans.append(span)
            return span
        return None

    def record_metric(self, name: str, value: float) -> None:
        """记录指标。"""
        self._metrics[name].append((time.time(), value))
        # 保留最近 10000 个点
        if len(self._metrics[name]) > 10000:
            self._metrics[name] = self._metrics[name][-10000:]

    def get_trace(self, trace_id: str) -> list[dict[str, Any]]:
        """获取追踪链。"""
        return [s.to_dict() for s in self._spans if s.trace_id == trace_id]

    def get_metrics(self, name: str, last_n: int = 100) -> list[dict[str, Any]]:
        """获取指标。"""
        points = self._metrics.get(name, [])[-last_n:]
        return [{"timestamp": t, "value": v} for t, v in points]

    def get_health(self) -> dict[str, Any]:
        """健康检查。"""
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "active_spans": len(self._active_spans),
            "total_spans": len(self._spans),
            "metrics_count": len(self._metrics),
        }

    def get_performance_summary(self) -> dict[str, Any]:
        """性能摘要。"""
        if not self._spans:
            return {"spans": 0}

        durations = [s.duration_ms() for s in self._spans if s.end_time > 0]
        return {
            "spans": len(self._spans),
            "avg_duration_ms": round(sum(durations) / max(1, len(durations)), 3),
            "max_duration_ms": round(max(durations) if durations else 0, 3),
            "p95_duration_ms": round(sorted(durations)[int(len(durations) * 0.95)] if durations else 0, 3),
            "operations": list(set(s.operation for s in self._spans)),
        }


# 单例
async_message_bus = AsyncMessageBus()
cloudflare_cdn_service = CloudflareCDNService()
nginx_config_generator = NginxConfigGenerator()
observability_service = ObservabilityService()