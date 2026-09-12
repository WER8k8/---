"""Distributed scheduler leader lock - Redis SET NX.

Fail-closed when Redis is unavailable (Batch A2 / ADR-0001).
支持锁续租（redlock风格），防止长时间任务因锁超时而中断。
"""
from __future__ import annotations

import logging
import os
import socket
import threading
import time

from app.core.cache import redis_client

logger = logging.getLogger("uj-admin.scheduler_leader")

# 续租间隔：每 1/3 TTL 自动续租一次
_RENEWAL_INTERVAL_RATIO = 3


def _holder_id() -> str:
    """_holder_id。
    :return: 返回处理结果。
    """
    return f"{socket.gethostname()}:{os.getpid()}"


class _LockState:
    """内部锁状态跟踪。"""
    __slots__ = ("key", "holder", "acquired_at", "ttl")
    def __init__(self, key: str, holder: str, acquired_at: float, ttl: int) -> None:
        """__init__。

        参数说明：
        :param self: 参数 self
        :param key: 参数 key
        :param holder: 参数 holder
        :param acquired_at: 参数 acquired_at
        :param ttl: 参数 ttl
        :return: 返回处理结果。
        """
        self.key = key
        self.holder = holder
        self.acquired_at = acquired_at
        self.ttl = ttl


# 内存中跟踪已持有的锁（用于续租）
_lock_registry: dict[str, _LockState] = {}
_registry_lock = threading.Lock()


def try_acquire_scheduler_lock(lock_name: str, ttl_seconds: int = 900) -> bool:
    """try_acquire_scheduler_lock。

    参数说明：
    :param lock_name: 参数 lock_name
    :param ttl_seconds: 参数 ttl_seconds
    :return: 返回处理结果。
    """
    if not redis_client:
        logger.error(
            "Scheduler lock unavailable (fail-closed): redis_client is None lock=%s",
            lock_name,
        )
        return False
    key = f"scheduler:leader:{lock_name}"
    try:
        ok = redis_client.set(key, _holder_id(), nx=True, ex=max(int(ttl_seconds), 30))
    except Exception as exc:
        logger.error("Scheduler lock error (fail-closed): lock=%s err=%s", lock_name, exc)
        return False
    if not ok:
        logger.debug("Scheduler lock busy: %s", lock_name)
        return False

    # 记录锁状态，用于续租
    state = _LockState(
        key=key,
        holder=_holder_id(),
        acquired_at=time.monotonic(),
        ttl=max(int(ttl_seconds), 30),
    )
    with _registry_lock:
        _lock_registry[key] = state

    logger.info("Scheduler lock acquired: %s (ttl=%ds)", lock_name, state.ttl)
    return True


def release_scheduler_lock(lock_name: str) -> None:
    """release_scheduler_lock。

    参数说明：
    :param lock_name: 参数 lock_name
    :return: 返回处理结果。
    """
    key = f"scheduler:leader:{lock_name}"
    with _registry_lock:
        _lock_registry.pop(key, None)

    if not redis_client:
        return
    try:
        holder = redis_client.get(key)
        if holder is None:
            return
        val = holder.decode() if isinstance(holder, bytes) else str(holder)
        if val == _holder_id():
            redis_client.delete(key)
            logger.info("Scheduler lock released: %s", lock_name)
    except Exception:
        logger.warning("Failed to release scheduler lock: %s", lock_name)


def renew_scheduler_lock(lock_name: str) -> bool:
    """续租锁，延长 TTL。用于长时间运行的任务。

    返回 True 表示续租成功，False 表示锁已过期或被其他节点获取。
    """
    key = f"scheduler:leader:{lock_name}"
    current_holder = _holder_id()
    if not redis_client:
        return False

    try:
        # 检查当前持有者是否仍是自己
        holder = redis_client.get(key)
        if holder is None:
            logger.warning("Scheduler lock expired before renewal: %s", lock_name)
            with _registry_lock:
                _lock_registry.pop(key, None)
            return False

        val = holder.decode() if isinstance(holder, bytes) else str(holder)
        if val != current_holder:
            logger.warning(
                "Scheduler lock holder changed, cannot renew: %s (was=%s, now=%s)",
                lock_name,
                current_holder,
                val,
            )
            with _registry_lock:
                _lock_registry.pop(key, None)
            return False

        # 续租：重置 TTL
        ttl = max(int(redis_client.ttl(key)) * 2, 30)
        redis_client.expire(key, ttl)
        # 更新内存状态
        with _registry_lock:
            state = _lock_registry.get(key)
            if state:
                state.ttl = ttl
                state.acquired_at = time.monotonic()

        logger.debug("Scheduler lock renewed: %s (new_ttl=%ds)", lock_name, ttl)
        return True
    except Exception as exc:
        logger.error("Scheduler lock renewal error: %s err=%s", lock_name, exc)
        return False


def start_lock_renewal(lock_name: str, interval_seconds: float | None = None) -> threading.Thread:
    """启动后台续租线程。

    Args:
        lock_name: 锁名称
        interval_seconds: 续租间隔（秒），默认 TTL/3

    Returns:
        后台线程对象
    """
    key = f"scheduler:leader:{lock_name}"
    with _registry_lock:
        state = _lock_registry.get(key)
        if not state:
            logger.warning("Cannot start renewal: lock not held %s", lock_name)
            return None

    interval = interval_seconds or (state.ttl / _RENEWAL_INTERVAL_RATIO)
    def _renew_loop() -> None:
        """_renew_loop。
        :return: 返回处理结果。
        """
        logger.info("Lock renewal thread started: %s (interval=%ds)", lock_name, int(interval))
        while True:
            time.sleep(interval)
            if not renew_scheduler_lock(lock_name):
                logger.warning("Lock renewal failed or lock expired: %s", lock_name)
                break

    thread = threading.Thread(target=_renew_loop, daemon=True, name=f"lock-renewal-{lock_name}")
    thread.start()
    return thread


def stop_lock_renewal(lock_name: str) -> None:
    """停止续租线程（显式释放锁时调用）。"""
    # 续租线程是 daemon 线程，会在主线程退出时自动终止
    pass
