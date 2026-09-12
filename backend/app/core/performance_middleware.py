"""性能监控中间件 - 自动追踪API请求性能"""

import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.middleware_fastlane import is_probe_or_static, perf_sample_enabled
from app.services.performance_monitor import PerformanceMetric, PerformanceMonitor
from app.api.v1.metrics import record_request, record_error


class PerformanceMiddleware(BaseHTTPMiddleware):
    """性能监控中间件 - 自动记录所有API请求的性能指标"""
    def __init__(self, app, monitor: Optional[PerformanceMonitor] = None):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param app: 参数 app
        :param monitor: 参数 monitor
        :return: 返回处理结果。
        """
        super().__init__(app)
        self.monitor = monitor or PerformanceMonitor()

    async def dispatch(self, request: Request, call_next) -> Response:
        """dispatch。

        参数说明：
        :param self: 参数 self
        :param request: 参数 request
        :param call_next: 参数 call_next
        :return: 返回处理结果。
        """
        start_time = time.time()
        # 排除健康检查和静态资源
        path = request.url.path
        if is_probe_or_static(path):
            return await call_next(request)
        if not perf_sample_enabled():
            return await call_next(request)

        # 执行请求
        response = await call_next(request)
        # 计算响应时间
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        # 近似响应体大小（来自 Content-Length 头，可能为 None）
        response_size: Optional[int] = None
        content_length = response.headers.get("content-length")
        if content_length is not None:
            try:
                response_size = int(content_length)
            except (ValueError, TypeError):
                pass

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
            response_size_bytes=response_size or 0,
        )
        self.monitor.record_metric(metric)
        # 接入 Prometheus metrics（CLOSE-12：激活已有 record_request/record_error）
        try:
            record_request(request.method, path.split("?")[0], response.status_code, response_time_ms / 1000)
        except Exception:
            pass
        if response.status_code >= 500:
            try:
                record_error("server_error", path.split("?")[0])
            except Exception:
                pass

        # 添加性能头到响应
        response.headers["X-Response-Time"] = f"{response_time_ms:.2f}ms"
        response.headers["X-Request-ID"] = str(int(start_time * 1000))
        if response_size is not None:
            response.headers["X-Response-Size"] = str(response_size)

        return response
