# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""司令部快照缓存 — Redis + Stale-While-Revalidate + 云端后台预热。

生产路径目标：用户打开司令部 <1s（命中 Redis 预热缓存），后台异步刷新保持新鲜度。
"""

from __future__ import annotations

import logging
import threading
import time
from copy import deepcopy
from datetime import timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.core.cache import get_cache, redis_available, set_cache
from app.core.config import settings

logger = logging.getLogger(__name__)

_REDIS_KEY = "hermes:command_center:snapshot:v1"
_memory_cache: dict[str, Any] = {"saved_at": 0.0, "payload": None}
_refresh_inflight = False
_refresh_lock = threading.Lock()


def _fresh_ttl_sec() -> int:
    """_fresh_ttl_sec。
    :return: 返回处理结果。
    """
    return int(getattr(settings, "COMMAND_CENTER_CACHE_TTL_SEC", 90) or 90)


def _stale_ttl_sec() -> int:
    """_stale_ttl_sec。
    :return: 返回处理结果。
    """
    return int(getattr(settings, "COMMAND_CENTER_STALE_TTL_SEC", 300) or 300)


def _memory_ttl_sec() -> int:
    """_memory_ttl_sec。
    :return: 返回处理结果。
    """
    return 30 if settings.ENVIRONMENT == "development" else _fresh_ttl_sec()


def _persist_redis(payload: dict[str, Any]) -> None:
    """_persist_redis。

    参数说明：
    :param payload: 参数 payload
    :return: 返回处理结果。
    """
    if not redis_available():
        return
    body = deepcopy(payload)
    body["_cached_at"] = time.time()
    set_cache(_REDIS_KEY, body, expire=timedelta(seconds=_stale_ttl_sec()))


def _read_redis() -> dict[str, Any] | None:
    """_read_redis。
    :return: 返回处理结果。
    """
    if not redis_available():
        return None
    row = get_cache(_REDIS_KEY)
    return row if isinstance(row, dict) else None


def _decorate_cached(payload: dict[str, Any], *, layer: str, cache_hit: bool, cache_stale: bool = False) -> dict[str, Any]:
    """_decorate_cached。

    参数说明：
    :param payload: 参数 payload
    :param layer: 参数 layer
    :param cache_hit: 参数 cache_hit
    :param cache_stale: 参数 cache_stale
    :return: 返回处理结果。
    """
    out = deepcopy(payload)
    cached_at = float(out.pop("_cached_at", 0.0) or 0.0)
    out["cache_hit"] = cache_hit
    out["cache_layer"] = layer
    out["cache_stale"] = cache_stale
    if cached_at:
        out["cache_age_sec"] = round(time.time() - cached_at, 1)
    return out


def warm_command_center_snapshot(*, reason: str = "background") -> dict[str, Any] | None:
    """构建并写入 Redis/内存缓存（供预热调度器或 SWR 后台刷新）。"""
    from app.core.database import SessionLocal
    from app.services.hermes.command_center import _build_command_center_snapshot_uncached
    sdb = SessionLocal()
    try:
        payload = _build_command_center_snapshot_uncached(sdb)
        payload["prewarm_reason"] = reason
        _persist_redis(payload)
        _memory_cache["saved_at"] = time.monotonic()
        _memory_cache["payload"] = deepcopy(payload)
        logger.info(
            "command_center cache warmed (%s) built_ms=%s layer=redis",
            reason,
            payload.get("built_ms"),
        )
        return payload
    except Exception as exc:
        logger.warning("command_center warm failed (%s): %s", reason, exc)
        return None
    finally:
        sdb.close()


def _schedule_background_refresh(reason: str = "swr") -> None:
    """_schedule_background_refresh。

    参数说明：
    :param reason: 参数 reason
    :return: 返回处理结果。
    """
    global _refresh_inflight
    with _refresh_lock:
        if _refresh_inflight:
            return
        _refresh_inflight = True

    def _job() -> None:
        """_job。
        :return: 返回处理结果。
        """
        global _refresh_inflight
        try:
            warm_command_center_snapshot(reason=reason)
        finally:
            with _refresh_lock:
                _refresh_inflight = False

    threading.Thread(target=_job, name="cc-swr-refresh", daemon=True).start()


def invalidate_command_center_cache() -> None:
    """运维循环等写操作后丢弃缓存，下次强制重建。"""
    global _refresh_inflight
    _memory_cache["saved_at"] = 0.0
    _memory_cache["payload"] = None
    if redis_available():
        from app.core.cache import delete_cache
        delete_cache(_REDIS_KEY)


def build_command_center_snapshot(db: Session, *, force_refresh: bool = False) -> dict[str, Any]:
    """司令部快照入口：Redis SWR → 进程内缓存 → 实时构建。"""
    from app.services.hermes.command_center import _build_command_center_snapshot_uncached
    if force_refresh:
        invalidate_command_center_cache()

    now = time.monotonic()
    redis_row = None if force_refresh else _read_redis()
    if redis_row:
        cached_at = float(redis_row.get("_cached_at") or 0.0)
        age = time.time() - cached_at if cached_at else 9999.0
        if age < _fresh_ttl_sec():
            return _decorate_cached(redis_row, layer="redis", cache_hit=True)
        if age < _stale_ttl_sec():
            _schedule_background_refresh("swr")
            return _decorate_cached(redis_row, layer="redis", cache_hit=True, cache_stale=True)

    mem = _memory_cache.get("payload")
    if (
        not force_refresh
        and mem is not None
        and now - float(_memory_cache.get("saved_at") or 0.0) < _memory_ttl_sec()
    ):
        return _decorate_cached(mem, layer="memory", cache_hit=True)

    payload = _build_command_center_snapshot_uncached(db)
    _persist_redis(payload)
    _memory_cache["saved_at"] = time.monotonic()
    _memory_cache["payload"] = deepcopy(payload)
    return _decorate_cached(payload, layer="live", cache_hit=False)


class CommandCenterPrewarmScheduler:
    """云端：后台周期性预热司令部 Redis 缓存，打开页面即可亚秒级响应。"""
    def __init__(self) -> None:
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def interval_seconds(self) -> int:
        """interval_seconds。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        sec = int(getattr(settings, "COMMAND_CENTER_PREWARM_INTERVAL_SEC", 45) or 45)
        return max(30, min(sec, 300))

    def start(self) -> None:
        """start。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="cc-prewarm", daemon=True)
        self._thread.start()
        logger.info("CommandCenterPrewarmScheduler started interval=%ss", self.interval_seconds)

    def stop(self) -> None:
        """stop。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._stop.set()

    def status(self) -> dict[str, Any]:
        """status。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "running": bool(self._thread and self._thread.is_alive()),
            "interval_seconds": self.interval_seconds,
            "redis_key": _REDIS_KEY,
        }

    def _loop(self) -> None:
        """_loop。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        # 启动后稍等 API/DB 就绪再首次预热
        self._stop.wait(15)
        while not self._stop.is_set():
            try:
                warm_command_center_snapshot(reason="scheduler")
            except Exception as exc:
                logger.warning("command_center prewarm tick failed: %s", exc)
            self._stop.wait(self.interval_seconds)


command_center_prewarm_scheduler = CommandCenterPrewarmScheduler()
