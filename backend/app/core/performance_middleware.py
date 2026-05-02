"""性能监控中间件 - 自动追踪API请求性能"""

import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.services.performance_monitor import PerformanceMonitor, PerformanceMetric


class PerformanceMiddleware(BaseHTTPMiddleware):
    """性能监控中间件 - 自动记录所有API请求的性能指标"""
    
    def __init__(self, app, monitor: Optional[PerformanceMonitor] = None):
        super().__init__(app)
        self.monitor = monitor or PerformanceMonitor()
    
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        
        # 排除健康检查和静态资源
        path = request.url.path
        if path.startswith("/health") or path.startswith("/static") or path.startswith("/uploads"):
            return await call_next(request)
        
        # 执行请求
        response = await call_next(request)
        
        # 计算响应时间
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        
        # 获取用户ID (如果已认证)
        user_id = None
        try:
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                # 这里可以解析JWT token获取user_id
                # 简化处理，暂时不解析
                pass
        except Exception:
            pass
        
        # 记录性能指标
        metric = PerformanceMetric(
            endpoint=path.split("?")[0],  # 移除查询参数
            method=request.method,
            response_time_ms=response_time_ms,
            status_code=response.status_code,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
        )
        
        self.monitor.record_metric(metric)
        
        # 添加性能头到响应
        response.headers["X-Response-Time"] = f"{response_time_ms:.2f}ms"
        response.headers["X-Request-ID"] = str(int(start_time * 1000))
        
        return response
