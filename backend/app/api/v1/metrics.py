"""Prometheus指标导出器 - 提供系统性能指标"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter, Response
import time
import psutil
import os

router = APIRouter()

# 定义指标
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active connections'
)

DB_QUERY_DURATION = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['table', 'operation']
)

CACHE_HIT_RATE = Gauge(
    'cache_hit_rate',
    'Cache hit rate percentage'
)

ERROR_COUNT = Counter(
    'errors_total',
    'Total number of errors',
    ['type', 'endpoint']
)

# 系统指标
CPU_USAGE = Gauge('cpu_usage_percent', 'CPU usage percentage')
MEMORY_USAGE = Gauge('memory_usage_bytes', 'Memory usage in bytes', ['type'])
DISK_USAGE = Gauge('disk_usage_bytes', 'Disk usage in bytes', ['type'])
PROCESS_UPTIME = Gauge('process_uptime_seconds', 'Process uptime in seconds')

START_TIME = time.time()

@router.get("/metrics")
def metrics():
    """导出Prometheus指标"""
    # 更新系统指标
    CPU_USAGE.set(psutil.cpu_percent(interval=1))
    
    memory = psutil.virtual_memory()
    MEMORY_USAGE.labels(type='total').set(memory.total)
    MEMORY_USAGE.labels(type='used').set(memory.used)
    MEMORY_USAGE.labels(type='available').set(memory.available)
    
    disk = psutil.disk_usage('/')
    DISK_USAGE.labels(type='total').set(disk.total)
    DISK_USAGE.labels(type='used').set(disk.used)
    DISK_USAGE.labels(type='free').set(disk.free)
    
    PROCESS_UPTIME.set(time.time() - START_TIME)
    
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


def record_request(method: str, endpoint: str, status: int, duration: float):
    """记录请求指标"""
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
    REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)


def record_db_query(table: str, operation: str, duration: float):
    """记录数据库查询指标"""
    DB_QUERY_DURATION.labels(table=table, operation=operation).observe(duration)


def record_error(error_type: str, endpoint: str):
    """记录错误指标"""
    ERROR_COUNT.labels(type=error_type, endpoint=endpoint).inc()


def update_cache_hit_rate(hit_rate: float):
    """更新缓存命中率"""
    CACHE_HIT_RATE.set(hit_rate)


def update_active_connections(count: int):
    """更新活跃连接数"""
    ACTIVE_CONNECTIONS.set(count)
