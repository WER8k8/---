# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""缓存工具模块 — FIX-24: 三级缓存架构

L1: 进程内 LRU（<1ms，容量 1000 条，TTL 30s）
L2: Redis（<5ms，容量无限制，TTL 可配置）
L3: CDN（Cloudflare / 边缘节点，>50ms 但全站共享）

eviction: L1 → L2 → DB，逐级回退
"""

import json
import logging
import time
from collections import OrderedDict
from datetime import timedelta
from functools import wraps
from threading import RLock
from typing import Any, Callable, Optional

import redis

from app.core.config import settings

log = logging.getLogger(__name__)

# Redis 客户端（短超时：司令部等只读聚合不得在 Redis 宕机时拖垮整页）
_redis_connect_timeout = float(getattr(settings, "REDIS_CONNECT_TIMEOUT", 1.0) or 1.0)
_redis_socket_timeout = float(getattr(settings, "REDIS_SOCKET_TIMEOUT", 1.0) or 1.0)
redis_client = (
    redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD,
        decode_responses=True,
        socket_connect_timeout=_redis_connect_timeout,
        socket_timeout=_redis_socket_timeout,
    )
    if settings.REDIS_ENABLED
    else None
)

_redis_circuit_open_until = 0.0
_REDIS_CIRCUIT_SECONDS = 30.0


def get_redis():
    """返回共享 Redis 客户端（未启用时 None）——app.core.database 兼容导出真身。"""
    return redis_client



def redis_available(*, force_check: bool = False) -> bool:
    """Redis 是否可用；失败后短时熔断，避免司令部等多段聚合反复阻塞。"""
    global _redis_circuit_open_until
    if not redis_client:
        return False
    if not force_check and time.monotonic() < _redis_circuit_open_until:
        return False
    try:
        redis_client.ping()
        _redis_circuit_open_until = 0.0
        return True
    except Exception as exc:
        _redis_circuit_open_until = time.monotonic() + _REDIS_CIRCUIT_SECONDS
        log.warning("redis unavailable (circuit %ss): %s", int(_REDIS_CIRCUIT_SECONDS), exc)
        return False


def tenant_cache_key(tenant_id: str, key: str) -> str:
    """构造租户隔离的缓存键。

    格式: t:{tenant_id}:{original_key}
    确保不同租户的缓存完全隔离，避免数据泄漏。

    Args:
        tenant_id: 租户 UUID
        key: 原始缓存键

    Returns:
        带租户前缀的缓存键

    Example:
        tenant_cache_key("abc123", "product:list")
        # => "t:abc123:product:list"
    """
    # 如果 key 已经以 t:{tenant_id}: 开头，不再重复添加
    prefix = f"t:{tenant_id}:"
    if key.startswith(prefix):
        return key
    return f"{prefix}{key}"


def extract_tenant_from_cache_key(key: str) -> Optional[str]:
    """从租户缓存键中提取租户 ID。

    Args:
        key: 缓存键，如 "t:abc123:product:list"

    Returns:
        租户 ID，如果非标准格式则返回 None
    """
    if key.startswith("t:") and ":" in key[2:]:
        return key[2:].split(":", 1)[0]
    return None


def get_cache(key: str) -> Optional[Any]:
    """获取缓存"""
    if not redis_available():
        return None

    try:
        value = redis_client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception:
        return None


def set_cache(key: str, value: Any, expire: timedelta = None) -> bool:
    """设置缓存"""
    if not redis_client:
        return False

    try:
        serialized = json.dumps(value)
        if expire:
            redis_client.setex(key, int(expire.total_seconds()), serialized)
        else:
            redis_client.set(key, serialized)
        return True
    except Exception:
        return False


def delete_cache(key: str) -> bool:
    """删除缓存"""
    if not redis_client:
        return False

    try:
        redis_client.delete(key)
        return True
    except Exception:
        return False


def delete_pattern(pattern: str) -> int:
    """删除匹配模式的缓存（使用 SCAN 避免 KEYS 阻塞生产 Redis）"""
    if not redis_client:
        return 0

    try:
        deleted = 0
        cursor = 0
        while True:
            cursor, keys = redis_client.scan(cursor, match=pattern, count=100)
            if keys:
                deleted += redis_client.delete(*keys)
            if cursor == 0:
                break
        return deleted
    except Exception:
        return 0


def delete_tenant_cache(tenant_id: str, pattern: str = "*") -> int:
    """删除指定租户的所有匹配缓存。

    仅清除属于该租户的缓存键，不影响其他租户。

    Args:
        tenant_id: 租户 ID
        pattern: 键模式后缀，默认为 * (全部)

    Returns:
        删除的键数量
    """
    full_pattern = f"t:{tenant_id}:{pattern}"
    return delete_pattern(full_pattern)


def invalidate_tenant_cache(tenant_id: str) -> int:
    """清除指定租户的所有缓存。

    用于租户登出、配置更新、数据迁移等场景。

    Args:
        tenant_id: 租户 ID

    Returns:
        删除的键数量
    """
    return delete_tenant_cache(tenant_id, "*")


def cache_decorator(expire: timedelta = timedelta(minutes=5)):
    """缓存装饰器"""
    def decorator(func: Callable) -> Callable:
        """decorator。

        参数说明：
        :param func: 参数 func
        :return: 返回处理结果。
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            """wrapper。

            参数说明：
            :param *args: 参数 *args
            :param **kwargs: 参数 **kwargs
            :return: 返回处理结果。
            """
            # 生成缓存key
            key_parts = [func.__name__]
            for arg in args:
                key_parts.append(str(arg))
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}={v}")
            cache_key = ":".join(key_parts)
            # 尝试获取缓存
            cached = get_cache(cache_key)
            if cached is not None:
                return cached

            # 执行函数
            result = func(*args, **kwargs)
            # 设置缓存
            set_cache(cache_key, result, expire)
            return result

        return wrapper

    return decorator


# 缓存key前缀常量
CACHE_KEYS = {
    "USER": "user:{}",
    "PRODUCT": "product:{}",
    "PRODUCT_SLUG": "product:slug:{}",
    "CATEGORY": "category:{}",
    "CATEGORY_TREE": "category:tree",
    "PAGE": "page:{}",
    "PAGE_SLUG": "page:slug:{}",
    "SEO": "seo:{}:{}",  # (resource_type, resource_id)
    "POPULAR_PRODUCTS": "product:popular",
    "STATS": "stats:{}",
}


def invalidate_user_cache(user_id: str) -> None:
    """使用户缓存失效"""
    delete_cache(CACHE_KEYS["USER"].format(user_id))


# ── FIX-20: 异步缓存装饰器（FastAPI 端点用）──

def async_cache_decorator(
    expire: timedelta = timedelta(minutes=5),
    key_prefix: str = "",
    ttl: int | None = None,
):
    """异步缓存装饰器 —— 用于 FastAPI 异步端点。

    Usage:
        @async_cache_decorator(expire=timedelta(minutes=10), key_prefix="capabilities")
        async def get_capabilities(...):
            ...

    兼容别名：``ttl``（秒）等价于 ``expire=timedelta(seconds=ttl)``，
    用于修复部分路由模块以 ``ttl=`` 调用导致的导入失败。
    """
    if ttl is not None:
        expire = timedelta(seconds=ttl)
    def decorator(func: Callable) -> Callable:
        """decorator。

        参数说明：
        :param func: 参数 func
        :return: 返回处理结果。
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            """wrapper。

            参数说明：
            :param *args: 参数 *args
            :param **kwargs: 参数 **kwargs
            :return: 返回处理结果。
            """
            # 生成缓存 key
            key_parts = [key_prefix or func.__name__]
            for arg in args:
                # 跳过 DB session、Depends 等对象
                if hasattr(arg, "__class__") and "Session" in arg.__class__.__name__:
                    continue
                key_parts.append(str(arg))
            for k, v in sorted(kwargs.items()):
                if k in ("db", "current_user"):
                    continue
                key_parts.append(f"{k}={v}")
            cache_key = ":".join(key_parts)
            # 尝试获取缓存
            cached = get_cache(cache_key)
            if cached is not None:
                log.debug("cache HIT: %s", cache_key)
                return cached

            # 执行函数
            result = await func(*args, **kwargs)
            # 设置缓存（只缓存 dict/list 等可序列化数据）
            if isinstance(result, dict) and result.get("code") == 0:
                set_cache(cache_key, result, expire)
                log.debug("cache SET: %s", cache_key)

            return result
        return wrapper
    return decorator


def invalidate_product_cache(product_id: str, slug: str = None) -> None:
    """使产品缓存失效"""
    delete_cache(CACHE_KEYS["PRODUCT"].format(product_id))
    if slug:
        delete_cache(CACHE_KEYS["PRODUCT_SLUG"].format(slug))
    delete_cache(CACHE_KEYS["POPULAR_PRODUCTS"])


def invalidate_category_cache(category_id: str = None) -> None:
    """使分类缓存失效"""
    if category_id:
        delete_cache(CACHE_KEYS["CATEGORY"].format(category_id))
    delete_cache(CACHE_KEYS["CATEGORY_TREE"])


def invalidate_page_cache(page_id: str, slug: str = None) -> None:
    """使页面缓存失效"""
    delete_cache(CACHE_KEYS["PAGE"].format(page_id))
    if slug:
        delete_cache(CACHE_KEYS["PAGE_SLUG"].format(slug))


def invalidate_seo_cache(resource_type: str, resource_id: str) -> None:
    """使SEO缓存失效"""
    delete_cache(CACHE_KEYS["SEO"].format(resource_type, resource_id))


# ============================================
# 超级管理员缓存扩展
# ============================================

ADMIN_CACHE_KEYS = {
    "ADMIN_SESSION": "admin:session:{}",          # {user_id}:{jti}
    "ADMIN_PERMISSIONS": "perm:{}",               # {user_id}
    "ADMIN_MENU_TREE": "menu:{}:{}",              # {user_id}:{parent_id}
    "ADMIN_DASHBOARD": "admin:dashboard:{}",       # {user_id}
    "AI_MODEL_CONFIG": "ai:model:{}",              # {model_id}
    "AI_ALL_MODELS": "ai:models:all",
    "CC_SWITCH_CONFIG": "cc:switch:{}",            # {config_id}
    "CC_ALL_CONFIGS": "cc:switch:all",
    "RATE_LIMIT": "rate:{}:{}",                    # {user_id}:{endpoint}
    "SYSTEM_MONITOR": "monitor:{}",                # {metric_name}
}

ADMIN_CACHE_TTL = {
    "session": 3600,       # 1 小时
    "permissions": 1800,   # 30 分钟
    "menu_tree": 600,      # 10 分钟
    "dashboard": 60,       # 1 分钟
    "ai_model": 300,       # 5 分钟
    "cc_switch": 300,      # 5 分钟
    "monitor": 15,         # 15 秒
}


def invalidate_admin_session(user_id: str, jti: str = None) -> None:
    """失效管理员会话"""
    if jti:
        set_cache(
            ADMIN_CACHE_KEYS["ADMIN_SESSION"].format(f"{user_id}:{jti}"),
            True,
        )
    else:
        delete_pattern(f"admin:session:{user_id}:*")


def invalidate_admin_user_cache(user_id: str) -> None:
    """清除用户所有管理员缓存"""
    delete_cache(ADMIN_CACHE_KEYS["ADMIN_PERMISSIONS"].format(user_id))
    delete_pattern(ADMIN_CACHE_KEYS["ADMIN_MENU_TREE"].format(user_id, "*"))
    delete_cache(ADMIN_CACHE_KEYS["ADMIN_DASHBOARD"].format(user_id))


def invalidate_ai_model_cache(model_id: str = None) -> None:
    """清除 AI 模型配置缓存"""
    if model_id:
        delete_cache(ADMIN_CACHE_KEYS["AI_MODEL_CONFIG"].format(model_id))
    delete_cache(ADMIN_CACHE_KEYS["AI_ALL_MODELS"])


def invalidate_cc_switch_cache(config_id: str = None) -> None:
    """清除 CC Switch 配置缓存"""
    if config_id:
        delete_cache(ADMIN_CACHE_KEYS["CC_SWITCH_CONFIG"].format(config_id))
    delete_cache(ADMIN_CACHE_KEYS["CC_ALL_CONFIGS"])


def invalidate_system_monitor_cache() -> None:
    """清除系统监控缓存"""
    delete_pattern("monitor:*")


def check_rate_limit(user_id: str, endpoint: str, max_requests: int = 60) -> bool:
    """检查请求频率限制（滑动窗口）"""
    key = ADMIN_CACHE_KEYS["RATE_LIMIT"].format(user_id, endpoint)
    try:
        current = redis_client.incr(key) if redis_client else 1
        if current == 1 and redis_client:
            redis_client.expire(key, 60)
        return current <= max_requests
    except Exception:
        return True


# ============================================
# FIX-24: L1 进程内 LRU 缓存（三级缓存架构）
# ============================================

_L1_MAX_SIZE = 1000
_L1_DEFAULT_TTL_SEC = 30.0
_l1_store: OrderedDict[str, tuple[float, Any]] = OrderedDict()
_l1_lock = RLock()


def _l1_get(key: str) -> Optional[Any]:
    """L1 进程内缓存读取。"""
    with _l1_lock:
        if key not in _l1_store:
            return None
        expires_at, value = _l1_store[key]
        if time.monotonic() > expires_at:
            del _l1_store[key]
            return None
        # LRU: 移到末尾
        _l1_store.move_to_end(key)
        return value


def _l1_set(key: str, value: Any, ttl_sec: float = _L1_DEFAULT_TTL_SEC) -> None:
    """L1 进程内缓存写入。"""
    with _l1_lock:
        if key in _l1_store:
            _l1_store.move_to_end(key)
        elif len(_l1_store) >= _L1_MAX_SIZE:
            # 淘汰最久未使用的条目
            _l1_store.popitem(last=False)
        _l1_store[key] = (time.monotonic() + ttl_sec, value)


def _l1_delete(key: str) -> None:
    """L1 进程内缓存删除。"""
    with _l1_lock:
        _l1_store.pop(key, None)


def l1_cache_stats() -> dict:
    """L1 缓存统计。"""
    with _l1_lock:
        now = time.monotonic()
        active = sum(1 for _, (exp, _) in _l1_store.items() if now <= exp)
        return {"size": len(_l1_store), "active": active, "max": _L1_MAX_SIZE}


def multi_level_get(key: str) -> Optional[Any]:
    """三级缓存读取：L1 → L2(Redis) → 回填 L1"""
    # L1
    value = _l1_get(key)
    if value is not None:
        return value

    # L2
    value = get_cache(key)
    if value is not None:
        _l1_set(key, value, ttl_sec=_L1_DEFAULT_TTL_SEC)
        return value

    return None


def multi_level_set(key: str, value: Any, ttl_sec: float = _L1_DEFAULT_TTL_SEC) -> None:
    """三级缓存写入：L1 + L2 同时写入"""
    _l1_set(key, value, ttl_sec=ttl_sec)
    set_cache(key, value, expire=timedelta(seconds=ttl_sec))


def multi_level_delete(key: str) -> None:
    """三级缓存删除：L1 + L2 同时清除"""
    _l1_delete(key)
    delete_cache(key)


def multi_level_invalidate(pattern: str) -> int:
    """按模式清除缓存（L1 前缀匹配 + L2 Redis SCAN）。"""
    # L1: 前缀匹配
    with _l1_lock:
        keys_to_del = [k for k in _l1_store if k.startswith(pattern.rstrip("*"))]
        for k in keys_to_del:
            del _l1_store[k]

    # L2: Redis SCAN
    redis_count = delete_pattern(pattern)
    return len(keys_to_del) + redis_count


def multi_level_cache_decorator(
    ttl_sec: float = _L1_DEFAULT_TTL_SEC,
    key_prefix: str = "",
):
    """三级缓存装饰器（L1 + L2），用于 FastAPI 异步端点。

    Usage:
        @multi_level_cache_decorator(ttl_sec=30, key_prefix="hot:products")
        async def get_products(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        """decorator。

        参数说明：
        :param func: 参数 func
        :return: 返回处理结果。
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            """wrapper。

            参数说明：
            :param *args: 参数 *args
            :param **kwargs: 参数 **kwargs
            :return: 返回处理结果。
            """
            key_parts = [key_prefix or func.__name__]
            for arg in args:
                if hasattr(arg, "__class__") and "Session" in arg.__class__.__name__:
                    continue
                key_parts.append(str(arg))
            for k, v in sorted(kwargs.items()):
                if k in ("db", "current_user", "request"):
                    continue
                key_parts.append(f"{k}={v}")
            cache_key = ":".join(key_parts)
            # L1 → L2 → compute
            cached = multi_level_get(cache_key)
            if cached is not None:
                return cached

            result = await func(*args, **kwargs)
            if isinstance(result, dict) and result.get("code") == 0:
                multi_level_set(cache_key, result, ttl_sec=ttl_sec)

            return result
        return wrapper
    return decorator
