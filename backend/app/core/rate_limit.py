"""
API限流中间件

分层限流策略：
1. 登录接口: 5次/分钟/IP（防暴力破解）
2. 注册/验证码: 3次/分钟/IP（防短信轰炸）
3. 普通API: 100次/分钟/IP
4. 全局默认: 200次/分钟/IP

使用滑动窗口算法，支持内存和Redis两种存储后端。
"""

import time
import threading
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.response import APIResponse

_rate_limit_logger = logging.getLogger("uj-admin.rate_limit")


# ── 限流规则定义 ──────────────────────────────────────────

RateLimitRule = Tuple[int, int]  # (max_requests, window_seconds)

# 登录接口: 5次/分钟/IP
LOGIN_RATE_LIMIT: RateLimitRule = (5, 60)

# 注册/验证码接口: 3次/分钟/IP
REGISTER_RATE_LIMIT: RateLimitRule = (3, 60)

# 租户自助注册: 5次/小时/IP（防批量注册）
TENANT_REGISTER_RATE_LIMIT: RateLimitRule = (5, 3600)

# 产品浏览量递增: 100次/小时/IP（防刷浏览量）
PRODUCT_VIEW_RATE_LIMIT: RateLimitRule = (100, 3600)

# 分析埋点: 1000次/小时/IP
ANALYTICS_EVENT_RATE_LIMIT: RateLimitRule = (1000, 3600)

# 普通API: 100次/分钟/IP
API_RATE_LIMIT: RateLimitRule = (100, 60)

# 全局默认: 200次/分钟/IP
DEFAULT_RATE_LIMIT: RateLimitRule = (200, 60)

# 路径匹配规则 → 限流策略
PATH_RATE_LIMIT_MAP: Dict[str, RateLimitRule] = {
    "/api/v1/auth/login": LOGIN_RATE_LIMIT,
    "/api/v1/auth/send-email-code": REGISTER_RATE_LIMIT,
    "/api/v1/auth/login-by-email": LOGIN_RATE_LIMIT,
    "/api/v1/auth/third-party-login": LOGIN_RATE_LIMIT,
    "/api/v1/tenants/register": TENANT_REGISTER_RATE_LIMIT,
    "/api/v1/analytics/event": ANALYTICS_EVENT_RATE_LIMIT,
}

# 路径前缀匹配规则（模糊匹配）
PREFIX_RATE_LIMIT_MAP: Dict[str, RateLimitRule] = {
    "/api/v1/auth/": LOGIN_RATE_LIMIT,
}

# 路径后缀匹配规则（用于包含动态ID的路径）
SUFFIX_RATE_LIMIT_MAP: Dict[str, RateLimitRule] = {
    "/increment-view": PRODUCT_VIEW_RATE_LIMIT,
}

# ── 分级限流（Tiered Rate Limiting）────────────────────────

RATE_LIMIT_TIERS: Dict[str, RateLimitRule] = {
    "auth": (5, 60),        # login/register → 5 req/60s
    "sensitive": (10, 60),  # password reset, email verify
    "write": (30, 60),      # POST/PUT/DELETE
    "read": (200, 60),      # GET
    "public": (500, 60),    # health check, openapi
}

# 路径前缀 → 分级名称映射
TIER_PATH_PREFIX_MAP: Dict[str, str] = {
    "/api/v1/auth/": "auth",
    "/api/v1/password/": "sensitive",
    "/api/v1/email/": "sensitive",
    "/api/v1/verify/": "sensitive",
}

# 写入类 HTTP 方法
WRITE_METHODS: set = {"POST", "PUT", "PATCH", "DELETE"}

# 公开路径 — 完全跳过限流
PUBLIC_PATHS: set = {
    "/health",
    "/api/v1/health",
    "/docs",
    "/openapi.json",
    "/redoc",
}


class SlidingWindowRateLimiter:
    """
    滑动窗口限流器

    使用内存字典存储每个IP的请求时间戳列表。
    生产环境建议替换为Redis实现以获得持久化和分布式支持。
    """
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._windows: Dict[str, list] = defaultdict(list)
        self._lock = threading.Lock()

    def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> Tuple[bool, int]:
        """
        检查请求是否允许。

        Args:
            key: 限流key（通常为IP或IP+路径）
            max_requests: 窗口内最大请求数
            window_seconds: 滑动窗口时长（秒）

        Returns:
            (是否允许, 剩余请求次数)
        """
        now = time.time()
        window_start = now - window_seconds
        with self._lock:
            # 清理过期记录
            self._windows[key] = [
                ts for ts in self._windows[key] if ts > window_start
            ]
            count = len(self._windows[key])
            if count >= max_requests:
                return False, 0

            # 记录本次请求
            self._windows[key].append(now)
            remaining = max_requests - count - 1
            return True, remaining

    def get_retry_after(self, key: str, window_seconds: int) -> int:
        """获取需要等待的秒数"""
        with self._lock:
            if key not in self._windows or not self._windows[key]:
                return 0
            sorted_timestamps = sorted(self._windows[key])
            if not sorted_timestamps:
                return 0
            oldest = sorted_timestamps[0]
            retry_after = int(oldest + window_seconds - time.time())
            return max(1, retry_after)

    def cleanup(self):
        """清理所有过期记录（定期调用）"""
        now = time.time()
        all_rules = [
            LOGIN_RATE_LIMIT, REGISTER_RATE_LIMIT,
            API_RATE_LIMIT, DEFAULT_RATE_LIMIT,
        ] + list(RATE_LIMIT_TIERS.values())
        max_window = max(rule[1] for rule in all_rules)
        cutoff = now - max_window
        with self._lock:
            expired_keys = []
            for key, timestamps in self._windows.items():
                self._windows[key] = [
                    ts for ts in timestamps if ts > cutoff
                ]
                if not self._windows[key]:
                    expired_keys.append(key)
            for key in expired_keys:
                del self._windows[key]


def _is_redis_required() -> bool:
    """Return True if Redis is mandatory (production with RATE_LIMIT_REQUIRE_REDIS)."""
    return (
        settings.RATE_LIMIT_REQUIRE_REDIS
        and settings.ENVIRONMENT != "development"
    )


class RedisSlidingWindowRateLimiter:
    """
    Redis-backed 滑动窗口限流器

    使用 Redis Sorted Set 实现分布式限流，支持多实例部署。
    当 Redis 不可用时：
      - 开发环境: 自动降级到内存限流器
      - 生产环境 + RATE_LIMIT_REQUIRE_REDIS=True:
          记录 CRITICAL 日志，使用极严格默认限流（5 req/min/IP）
    """
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._redis = None
        self._fallback = SlidingWindowRateLimiter()
        self._redis_failed_logged = False
        self._init_redis()

    def _init_redis(self):
        """_init_redis。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        try:
            from app.core.database import get_redis
            self._redis = get_redis()
        except Exception:
            pass

    def _handle_redis_unavailable(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> Tuple[bool, int]:
        """Handle the case where Redis is unavailable."""
        if _is_redis_required():
            # Production without Redis: use a very restrictive limit
            restrictive_max = min(max_requests, 5)
            if not self._redis_failed_logged:
                _rate_limit_logger.critical(
                    "[RATE_LIMIT] Redis unavailable in production "
                    "(ENVIRONMENT=%s, RATE_LIMIT_REQUIRE_REDIS=true). "
                    "Rate limiting degraded to restrictive in-memory mode "
                    "(max=%d req/%ds). Fix Redis immediately!",
                    settings.ENVIRONMENT,
                    restrictive_max,
                    window_seconds,
                )
                self._redis_failed_logged = True
            return self._fallback.is_allowed(key, restrictive_max, window_seconds)
        else:
            # Development: normal fallback
            return self._fallback.is_allowed(key, max_requests, window_seconds)

    def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> Tuple[bool, int]:
        """is_allowed。

        参数说明：
        :param self: 参数 self
        :param key: 参数 key
        :param max_requests: 参数 max_requests
        :param window_seconds: 参数 window_seconds
        :return: 返回处理结果。
        """
        if not self._redis:
            return self._handle_redis_unavailable(key, max_requests, window_seconds)

        try:
            now = time.time()
            window_start = now - window_seconds
            redis_key = f"ratelimit:{key}"
            pipe = self._redis.pipeline()
            pipe.zremrangebyscore(redis_key, 0, window_start)
            pipe.zadd(redis_key, {str(now): now})
            pipe.zcard(redis_key)
            pipe.expire(redis_key, window_seconds)
            results = pipe.execute()
            count = results[2]
            if count > max_requests:
                # 移除本次添加的记录
                self._redis.zrem(redis_key, str(now))
                return False, 0

            remaining = max_requests - count
            # Reset log flag on successful Redis operation
            self._redis_failed_logged = False
            return True, remaining
        except Exception:
            # Redis 故障时根据环境决定策略
            if not self._redis:
                self._redis_failed_logged = False  # reset for next init
            return self._handle_redis_unavailable(key, max_requests, window_seconds)

    def get_retry_after(self, key: str, window_seconds: int) -> int:
        """get_retry_after。

        参数说明：
        :param self: 参数 self
        :param key: 参数 key
        :param window_seconds: 参数 window_seconds
        :return: 返回处理结果。
        """
        if not self._redis:
            return self._fallback.get_retry_after(key, window_seconds)

        try:
            redis_key = f"ratelimit:{key}"
            oldest = self._redis.zrange(redis_key, 0, 0, withscores=True)
            if oldest:
                retry_after = int(oldest[0][1] + window_seconds - time.time())
                return max(1, retry_after)
        except Exception:
            if _is_redis_required():
                _rate_limit_logger.critical(
                    "[RATE_LIMIT] Redis get_retry_after failed in production.",
                )
        return self._fallback.get_retry_after(key, window_seconds)

    def cleanup(self):
        """cleanup。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._fallback.cleanup()


# 全局限流器实例（自动选择 Redis 或内存后端）
_limiter = RedisSlidingWindowRateLimiter()


def _get_rate_limit_for_path(path: str) -> RateLimitRule:
    """根据请求路径获取对应的限流规则"""
    # 精确匹配优先
    if path in PATH_RATE_LIMIT_MAP:
        return PATH_RATE_LIMIT_MAP[path]

    # 前缀匹配
    for prefix, rule in PREFIX_RATE_LIMIT_MAP.items():
        if path.startswith(prefix):
            return rule

    # 后缀匹配（用于含动态ID的路径）
    for suffix, rule in SUFFIX_RATE_LIMIT_MAP.items():
        if path.endswith(suffix):
            return rule

    # API路径默认限流
    if path.startswith("/api/"):
        return API_RATE_LIMIT

    return DEFAULT_RATE_LIMIT


def _is_public_path(path: str) -> bool:
    """检查路径是否需要跳过限流（公开端点）"""
    return path in PUBLIC_PATHS


def _resolve_rate_limit_for_path(
    path: str,
    method: str,
    default_max: int,
    default_window: int,
) -> RateLimitRule:
    """
    根据路径和HTTP方法解析对应的分级限流规则。

    优先级：
    1. 精确路径匹配（PATH_RATE_LIMIT_MAP，现有逻辑）
    2. 前缀匹配（PREFIX_RATE_LIMIT_MAP，现有逻辑）
    3. 分级前缀匹配（TIER_PATH_PREFIX_MAP，新增）
    4. 写入方法分级（POST/PUT/PATCH/DELETE → "write" tier）
    5. /api/ 路径回退（API_RATE_LIMIT，现有逻辑）
    6. 全局默认值

    Args:
        path: 请求路径
        method: HTTP 方法
        default_max: 默认最大请求数
        default_window: 默认滑动窗口秒数

    Returns:
        (max_requests, window_seconds) 限流规则
    """
    # 1. 精确路径匹配（现有逻辑）
    if path in PATH_RATE_LIMIT_MAP:
        return PATH_RATE_LIMIT_MAP[path]

    # 2. 前缀匹配（现有逻辑）
    for prefix, rule in PREFIX_RATE_LIMIT_MAP.items():
        if path.startswith(prefix):
            return rule

    # 2b. 后缀匹配（用于含动态ID的路径）
    for suffix, rule in SUFFIX_RATE_LIMIT_MAP.items():
        if path.endswith(suffix):
            return rule

    # 3. 分级前缀匹配（新增）
    for prefix, tier_name in TIER_PATH_PREFIX_MAP.items():
        if path.startswith(prefix):
            return RATE_LIMIT_TIERS[tier_name]

    # 4. 写入方法分级（新增）
    if method in WRITE_METHODS:
        return RATE_LIMIT_TIERS["write"]

    # 5. /api/ 前缀回退（现有逻辑）
    if path.startswith("/api/"):
        return API_RATE_LIMIT

    # 6. 全局默认值
    return (default_max, default_window)


def _get_client_ip(request: Request) -> str:
    """获取客户端真实IP

    安全说明:
    - X-Forwarded-For / X-Real-IP 仅在请求来自已知代理时才信任。
      直接客户端请求（非代理）使用 request.client.host。
    - 如需信任特定代理 IP 段,可通过环境变量 TRUSTED_PROXY_CIDRS 配置。
    """
    # 直接连接的客户端（无代理场景）直接使用 client.host
    # 这是最安全的默认值,因为 X-Forwarded-For 可被攻击者伪造
    if request.client and request.client.host:
        # 检查是否是本地/已知代理
        client_host = request.client.host
        if _is_trusted_proxy_ip(client_host):
            # 来自可信代理: 尝试从 X-Forwarded-For 取原始 IP
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                return forwarded.split(",")[0].strip()
            real_ip = request.headers.get("X-Real-IP")
            if real_ip:
                return real_ip.strip()
        # 非代理或未知代理: 返回直连 IP
        return client_host

    return "unknown"


# 已知的可信代理 IP/段列表（可通过环境变量扩展）
_TRUSTED_PROXIES: list[str] = []


def _load_trusted_proxies() -> list[str]:
    """从环境变量加载可信代理列表"""
    import os
    env_val = os.getenv("TRUSTED_PROXY_CIDRS", "")
    if not env_val:
        return []
    return [p.strip() for p in env_val.split(",") if p.strip()]


def _is_trusted_proxy_ip(ip: str) -> bool:
    """检查 IP 是否来自可信代理"""
    if not _TRUSTED_PROXIES:
        # 惰性加载
        _TRUSTED_PROXIES.extend(_load_trusted_proxies())

    if not _TRUSTED_PROXIES:
        return False

    for trusted in _TRUSTED_PROXIES:
        # 支持精确 IP 或 CIDR 段
        if "/" in trusted:
            if _ip_in_cidr(ip, trusted):
                return True
        elif ip == trusted:
            return True
    return False


def _ip_in_cidr(ip: str, cidr: str) -> bool:
    """检查 IP 是否在 CIDR 段内"""
    import ipaddress
    try:
        return ipaddress.ip_address(ip) in ipaddress.ip_network(cidr, strict=False)
    except Exception:
        return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    分层限流中间件

    在开发模式（DEBUG=True）下自动跳过限流。
    使用滑动窗口算法，按路径匹配不同的限流策略。
    """
    def __init__(self, app, default_max_requests: int = None,
                 default_window_seconds: int = None):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param app: 参数 app
        :param default_max_requests: 参数 default_max_requests
        :param default_window_seconds: 参数 default_window_seconds
        :return: 返回处理结果。
        """
        super().__init__(app)
        self.default_max = (
            default_max_requests or settings.RATE_LIMIT_MAX_REQUESTS
        )
        self.default_window = (
            default_window_seconds or settings.RATE_LIMIT_WINDOW_SECONDS
        )
        self._cleanup_counter = 0

    async def dispatch(self, request: Request, call_next):
        """dispatch。

        参数说明：
        :param self: 参数 self
        :param request: 参数 request
        :param call_next: 参数 call_next
        :return: 返回处理结果。
        """
        # 开发环境放宽限流但不禁用（防止生产误配 DEBUG=true 导致限流失效）
        if settings.DEBUG and settings.ENVIRONMENT != "production":
            import logging as _logging
            _logging.getLogger("rate_limit").debug(
                "[DEV] Rate limiting relaxed (DEBUG=True, env=%s).",
                settings.ENVIRONMENT,
            )

        # 公开路径 — 完全跳过限流（/health, /docs, /openapi.json, /redoc）
        if _is_public_path(request.url.path):
            return await call_next(request)

        # 获取限流规则（分级限流：精确→前缀→分级前缀→方法→API回退→默认）
        path = request.url.path
        method = request.method
        max_requests, window_seconds = _resolve_rate_limit_for_path(
            path, method, self.default_max, self.default_window
        )
        client_ip = _get_client_ip(request)
        # 限流key = IP + 路径前缀（不同路径独立限流）
        rate_limit_key = f"{client_ip}:{path}" if path in PATH_RATE_LIMIT_MAP else client_ip
        # 检查是否允许
        allowed, remaining = _limiter.is_allowed(
            rate_limit_key, max_requests, window_seconds
        )
        if not allowed:
            retry_after = _limiter.get_retry_after(
                rate_limit_key, window_seconds
            )
            return JSONResponse(
                status_code=429,
                content=APIResponse(
                    code=429,
                    message=f"请求过于频繁，请 {retry_after} 秒后再试",
                ).model_dump(),
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + retry_after)),
                },
            )

        # 处理请求
        response = await call_next(request)
        # 添加限流头信息
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        # 定期清理（每1000次请求执行一次）
        self._cleanup_counter += 1
        if self._cleanup_counter % 1000 == 0:
            _limiter.cleanup()
            self._cleanup_counter = 0

        return response


# ── 工具函数 ──────────────────────────────────────────────

def get_rate_limiter() -> SlidingWindowRateLimiter:
    """获取全局限流器实例"""
    return _limiter


def reset_rate_limiter():
    """重置限流器（测试用）"""
    global _limiter
    _limiter = SlidingWindowRateLimiter()
