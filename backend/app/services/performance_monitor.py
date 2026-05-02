"""性能监控服务 - 追踪API响应时间和系统性能指标"""

import time
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, field

from app.core.logging_config import AppLogger

logger = AppLogger("performance_monitor")


@dataclass
class PerformanceMetric:
    """性能指标数据类"""
    endpoint: str
    method: str
    response_time_ms: float
    status_code: int
    timestamp: datetime
    user_id: Optional[str] = None
    request_size_bytes: int = 0
    response_size_bytes: int = 0


class PerformanceMonitor:
    """性能监控器 - 收集和聚合性能指标"""
    
    def __init__(self):
        self.metrics: List[PerformanceMetric] = []
        self.slow_queries: List[Dict[str, Any]] = []
        self.endpoint_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'count': 0,
            'total_time': 0.0,
            'min_time': float('inf'),
            'max_time': 0.0,
            'avg_time': 0.0,
            'p95_time': 0.0,
            'p99_time': 0.0,
            'error_count': 0,
        })
        self.SLOW_THRESHOLD_MS = 500  # 慢查询阈值 (毫秒)
        self.MAX_METRICS_COUNT = 10000  # 最大保留指标数量
    
    def record_metric(self, metric: PerformanceMetric):
        """记录性能指标"""
        self.metrics.append(metric)
        
        # 限制内存使用
        if len(self.metrics) > self.MAX_METRICS_COUNT:
            self.metrics = self.metrics[-self.MAX_METRICS_COUNT:]
        
        # 更新端点统计
        key = f"{metric.method} {metric.endpoint}"
        stats = self.endpoint_stats[key]
        stats['count'] += 1
        stats['total_time'] += metric.response_time_ms
        stats['min_time'] = min(stats['min_time'], metric.response_time_ms)
        stats['max_time'] = max(stats['max_time'], metric.response_time_ms)
        stats['avg_time'] = stats['total_time'] / stats['count']
        
        if metric.status_code >= 400:
            stats['error_count'] += 1
        
        # 检测慢查询
        if metric.response_time_ms > self.SLOW_THRESHOLD_MS:
            slow_query = {
                'endpoint': metric.endpoint,
                'method': metric.method,
                'response_time_ms': metric.response_time_ms,
                'timestamp': metric.timestamp.isoformat(),
                'status_code': metric.status_code,
            }
            self.slow_queries.append(slow_query)
            
            # 限制慢查询记录数量
            if len(self.slow_queries) > 1000:
                self.slow_queries = self.slow_queries[-1000:]
            
            logger.warning(
                f"Slow query detected: {metric.method} {metric.endpoint} "
                f"took {metric.response_time_ms:.2f}ms"
            )
    
    def calculate_percentile(self, times: List[float], percentile: float) -> float:
        """计算百分位数"""
        if not times:
            return 0.0
        sorted_times = sorted(times)
        index = int(len(sorted_times) * percentile / 100)
        index = min(index, len(sorted_times) - 1)
        return sorted_times[index]
    
    def update_percentiles(self):
        """更新P95和P99指标"""
        for key, stats in self.endpoint_stats.items():
            # 获取该端点的所有响应时间
            times = [
                m.response_time_ms 
                for m in self.metrics 
                if f"{m.method} {m.endpoint}" == key
            ]
            if times:
                stats['p95_time'] = self.calculate_percentile(times, 95)
                stats['p99_time'] = self.calculate_percentile(times, 99)
    
    def get_endpoint_stats(self, limit: int = 20) -> Dict[str, Any]:
        """获取端点性能统计"""
        self.update_percentiles()
        
        # 按平均响应时间排序
        sorted_endpoints = sorted(
            self.endpoint_stats.items(),
            key=lambda x: x[1]['avg_time'],
            reverse=True
        )[:limit]
        
        return {
            'total_requests': sum(s['count'] for s in self.endpoint_stats.values()),
            'total_errors': sum(s['error_count'] for s in self.endpoint_stats.values()),
            'error_rate': round(
                sum(s['error_count'] for s in self.endpoint_stats.values()) / 
                max(sum(s['count'] for s in self.endpoint_stats.values()), 1) * 100,
                2
            ),
            'endpoints': [
                {
                    'endpoint': endpoint,
                    **stats,
                    'min_time': round(stats['min_time'], 2) if stats['min_time'] != float('inf') else 0,
                    'max_time': round(stats['max_time'], 2),
                    'avg_time': round(stats['avg_time'], 2),
                    'p95_time': round(stats['p95_time'], 2),
                    'p99_time': round(stats['p99_time'], 2),
                }
                for endpoint, stats in sorted_endpoints
            ],
            'slow_queries_count': len(self.slow_queries),
            'recent_slow_queries': self.slow_queries[-10:],
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        stats = self.get_endpoint_stats()
        
        # 判断健康状态
        health_status = "healthy"
        issues = []
        
        if stats['error_rate'] > 5:
            health_status = "degraded"
            issues.append(f"错误率过高: {stats['error_rate']}%")
        
        if stats['slow_queries_count'] > 100:
            health_status = "degraded"
            issues.append(f"慢查询过多: {stats['slow_queries_count']}个")
        
        # 检查P99响应时间
        slow_endpoints = [
            ep for ep in stats['endpoints']
            if ep['p99_time'] > 1000  # P99 > 1秒
        ]
        if slow_endpoints:
            health_status = "warning"
            issues.append(f"{len(slow_endpoints)}个端点P99响应时间超过1秒")
        
        return {
            'status': health_status,
            'issues': issues,
            'metrics': stats,
            'timestamp': datetime.utcnow().isoformat(),
        }
    
    def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """生成性能报告"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        recent_metrics = [
            m for m in self.metrics
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return {
                'period_hours': hours,
                'total_requests': 0,
                'message': 'No metrics available for the specified period',
            }
        
        response_times = [m.response_time_ms for m in recent_metrics]
        
        return {
            'period_hours': hours,
            'total_requests': len(recent_metrics),
            'avg_response_time_ms': round(sum(response_times) / len(response_times), 2),
            'min_response_time_ms': round(min(response_times), 2),
            'max_response_time_ms': round(max(response_times), 2),
            'p95_response_time_ms': round(self.calculate_percentile(response_times, 95), 2),
            'p99_response_time_ms': round(self.calculate_percentile(response_times, 99), 2),
            'error_count': sum(1 for m in recent_metrics if m.status_code >= 400),
            'error_rate': round(
                sum(1 for m in recent_metrics if m.status_code >= 400) / 
                len(recent_metrics) * 100,
                2
            ),
            'requests_per_minute': round(len(recent_metrics) / (hours * 60), 2),
            'top_slow_endpoints': self.get_endpoint_stats(limit=5)['endpoints'][:5],
        }


# 全局性能监控实例
performance_monitor = PerformanceMonitor()
