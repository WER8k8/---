"""BFF 首屏缓存 — Redis 优先，开发环境内存兜底（Phase 4 / T-ARCH-2）。"""

from __future__ import annotations

import time
from datetime import timedelta
from typing import Any, Callable, TypeVar

from app.core.cache import get_cache, set_cache

T = TypeVar("T")

_MEMORY: dict[str, tuple[float, Any]] = {}


def bff_cache_key(scope: str, *parts: str) -> str:
    """bff_cache_key。

    参数说明：
    :param scope: 参数 scope
    :param *parts: 参数 *parts
    :return: 返回处理结果。
    """
    suffix = ":".join(p for p in parts if p)
    return f"uj:{scope}:{suffix}" if suffix else f"uj:{scope}"


def get_bff_cached(key: str, *, ttl_sec: int = 60) -> Any | None:
    """get_bff_cached。

    参数说明：
    :param key: 参数 key
    :param ttl_sec: 参数 ttl_sec
    :return: 返回处理结果。
    """
    hit = get_cache(key)
    if hit is not None:
        return hit
    entry = _MEMORY.get(key)
    if not entry:
        return None
    ts, value = entry
    if time.time() - ts > ttl_sec:
        _MEMORY.pop(key, None)
        return None
    return value


def set_bff_cached(key: str, value: Any, *, ttl_sec: int = 60) -> None:
    """set_bff_cached。

    参数说明：
    :param key: 参数 key
    :param value: 参数 value
    :param ttl_sec: 参数 ttl_sec
    :return: 返回处理结果。
    """
    set_cache(key, value, expire=timedelta(seconds=ttl_sec))
    _MEMORY[key] = (time.time(), value)


def cached_bff(key: str, *, ttl_sec: int = 60, builder: Callable[[], T]) -> T:
    """cached_bff。

    参数说明：
    :param key: 参数 key
    :param ttl_sec: 参数 ttl_sec
    :param builder: 参数 builder
    :return: 返回处理结果。
    """
    cached = get_bff_cached(key, ttl_sec=ttl_sec)
    if cached is not None:
        return cached  # type: ignore[return-value]
    value = builder()
    set_bff_cached(key, value, ttl_sec=ttl_sec)
    return value
