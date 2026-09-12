"""AiToEarn MCP 本地代理 — 离线回退 + 缓存层。

当 AiToEarn 云端服务不可用时，提供：
- 本地缓存（账号列表、发布任务状态）
- 离线模式（降级为本地模拟）
- 请求重试 + 熔断机制
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# 缓存配置
CACHE_DIR = Path(__file__).parents[2] / ".cache" / "aitoearn"
CACHE_TTL_ACCOUNTS = 300  # 5 分钟
CACHE_TTL_TASKS = 60  # 1 分钟
CACHE_TTL_MATERIALS = 600  # 10 分钟

# 熔断器配置
CIRCUIT_BREAKER_THRESHOLD = 5  # 连续失败 5 次触发熔断
CIRCUIT_BREAKER_TIMEOUT = 60  # 熔断 60 秒

_circuit_state = {
    "failure_count": 0,
    "last_failure_time": 0,
    "is_open": False,
}


def _safe_asyncio_run(coro):
    """_safe_asyncio_run。

    参数说明：
    :param coro: 参数 coro
    :return: 返回处理结果。
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)


def _ensure_cache_dir():
    """_ensure_cache_dir。
    :return: 返回处理结果。
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _get_cache_path(key: str) -> Path:
    """_get_cache_path。

    参数说明：
    :param key: 参数 key
    :return: 返回处理结果。
    """
    return CACHE_DIR / f"{key}.json"


def _read_cache(key: str, ttl_seconds: int) -> dict[str, Any] | None:
    """读取缓存文件。"""
    cache_path = _get_cache_path(key)
    if not cache_path.exists():
        return None

    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
        ts = data.get("ts", 0)
        if time.time() - ts > ttl_seconds:
            return None
        return data.get("data")
    except Exception:
        return None


def _write_cache(key: str, data: Any) -> None:
    """写入缓存文件。"""
    try:
        _ensure_cache_dir()
        cache_path = _get_cache_path(key)
        cache_path.write_text(
            json.dumps({"ts": time.time(), "data": data}, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as exc:
        logger.warning("write cache %s failed: %s", key, exc)


def _check_circuit_breaker() -> bool:
    """检查熔断器状态。返回 True 表示可以请求，False 表示熔断中。"""
    if not _circuit_state["is_open"]:
        return True

    # 检查是否超过熔断超时时间
    if time.time() - _circuit_state["last_failure_time"] > CIRCUIT_BREAKER_TIMEOUT:
        _circuit_state["is_open"] = False
        _circuit_state["failure_count"] = 0
        logger.info("circuit breaker reset after timeout")
        return True

    return False


def _record_success() -> None:
    """记录成功请求。"""
    _circuit_state["failure_count"] = 0
    _circuit_state["is_open"] = False


def _record_failure() -> None:
    """记录失败请求。"""
    _circuit_state["failure_count"] += 1
    _circuit_state["last_failure_time"] = time.time()
    if _circuit_state["failure_count"] >= CIRCUIT_BREAKER_THRESHOLD:
        _circuit_state["is_open"] = True
        logger.warning(
            "circuit breaker opened after %d failures",
            _circuit_state["failure_count"],
        )


async def fetch_accounts_with_cache() -> list[dict[str, Any]]:
    """获取账号列表（带缓存 + 离线回退）。"""
    cache_key = "accounts"
    # 尝试从缓存读取
    cached = _read_cache(cache_key, CACHE_TTL_ACCOUNTS)
    if cached is not None:
        return cached.get("accounts", [])

    # 检查熔断器
    if not _check_circuit_breaker():
        logger.warning("circuit breaker open, returning stale cache")
        stale = _read_cache(cache_key, CACHE_TTL_ACCOUNTS * 10)  # 使用更长的过期
        if stale:
            return stale.get("accounts", [])
        return []

    # 从 AiToEarn 获取
    try:
        from app.services.aitoearn_publish_adapter import fetch_accounts
        accounts = await fetch_accounts()
        _write_cache(cache_key, {"accounts": accounts})
        _record_success()
        return accounts
    except Exception as exc:
        _record_failure()
        logger.warning("fetch accounts failed, using stale cache: %s", exc)
        # 回退到过期缓存
        stale = _read_cache(cache_key, CACHE_TTL_ACCOUNTS * 10)
        if stale:
            return stale.get("accounts", [])
        return []


async def fetch_publish_tasks_with_cache(flow_id: str) -> list[dict[str, Any]]:
    """获取发布任务列表（带缓存 + 离线回退）。"""
    cache_key = f"tasks_{flow_id}"
    # 尝试从缓存读取
    cached = _read_cache(cache_key, CACHE_TTL_TASKS)
    if cached is not None:
        return cached.get("tasks", [])

    # 检查熔断器
    if not _check_circuit_breaker():
        stale = _read_cache(cache_key, CACHE_TTL_TASKS * 10)
        if stale:
            return stale.get("tasks", [])
        return []

    try:
        from app.services.aitoearn_publish_adapter import fetch_publish_tasks
        tasks = await fetch_publish_tasks(flow_id)
        _write_cache(cache_key, {"tasks": tasks})
        _record_success()
        return tasks
    except Exception as exc:
        _record_failure()
        logger.warning("fetch tasks failed, using stale cache: %s", exc)
        stale = _read_cache(cache_key, CACHE_TTL_TASKS * 10)
        if stale:
            return stale.get("tasks", [])
        return []


async def fetch_materials_with_cache(
    *,
    page: int = 1,
    page_size: int = 20,
    material_type: str = "video",
) -> dict[str, Any]:
    """获取素材列表（带缓存 + 离线回退）。"""
    cache_key = f"materials_{page}_{page_size}_{material_type}"
    cached = _read_cache(cache_key, CACHE_TTL_MATERIALS)
    if cached is not None:
        return cached

    if not _check_circuit_breaker():
        stale = _read_cache(cache_key, CACHE_TTL_MATERIALS * 10)
        if stale:
            return stale
        return {"items": [], "total": 0}

    try:
        from app.services.aitoearn_publish_adapter import fetch_materials
        result = await fetch_materials(
            page=page,
            page_size=page_size,
            material_type=material_type,
        )
        _write_cache(cache_key, result)
        _record_success()
        return result
    except Exception as exc:
        _record_failure()
        logger.warning("fetch materials failed: %s", exc)
        stale = _read_cache(cache_key, CACHE_TTL_MATERIALS * 10)
        if stale:
            return stale
        return {"items": [], "total": 0}


def get_circuit_breaker_status() -> dict[str, Any]:
    """获取熔断器状态。"""
    return {
        "is_open": _circuit_state["is_open"],
        "failure_count": _circuit_state["failure_count"],
        "last_failure_time": (
            datetime.fromtimestamp(_circuit_state["last_failure_time"], tz=timezone.utc).isoformat()
            if _circuit_state["last_failure_time"]
            else None
        ),
        "threshold": CIRCUIT_BREAKER_THRESHOLD,
        "timeout_seconds": CIRCUIT_BREAKER_TIMEOUT,
    }


def reset_circuit_breaker() -> None:
    """手动重置熔断器。"""
    _circuit_state["failure_count"] = 0
    _circuit_state["is_open"] = False
    _circuit_state["last_failure_time"] = 0
    logger.info("circuit breaker manually reset")


def clear_cache(key: str | None = None) -> int:
    """清除缓存。返回清除的文件数。"""
    if key:
        cache_path = _get_cache_path(key)
        if cache_path.exists():
            cache_path.unlink()
            return 1
        return 0

    # 清除所有缓存
    count = 0
    if CACHE_DIR.exists():
        for f in CACHE_DIR.glob("*.json"):
            f.unlink()
            count += 1
    return count


def fetch_accounts_with_cache_sync() -> list[dict[str, Any]]:
    """fetch_accounts_with_cache_sync。
    :return: 返回处理结果。
    """
    return _safe_asyncio_run(fetch_accounts_with_cache())


def fetch_publish_tasks_with_cache_sync(flow_id: str) -> list[dict[str, Any]]:
    """fetch_publish_tasks_with_cache_sync。

    参数说明：
    :param flow_id: 参数 flow_id
    :return: 返回处理结果。
    """
    return _safe_asyncio_run(fetch_publish_tasks_with_cache(flow_id))


def fetch_materials_with_cache_sync(**kwargs) -> dict[str, Any]:
    """fetch_materials_with_cache_sync。

    参数说明：
    :param **kwargs: 参数 **kwargs
    :return: 返回处理结果。
    """
    return _safe_asyncio_run(fetch_materials_with_cache(**kwargs))
