"""Agent run 状态存储（内存 + 可选 Redis）。

BUG-15 修复：添加持久化保障和异常处理。
Redis 不可用时仍保持内存存储，但添加明确警告日志。
"""

from __future__ import annotations

import logging
import threading
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.cache import get_cache, set_cache

logger = logging.getLogger(__name__)

_MEMORY: dict[str, dict[str, Any]] = {}
_LOCK = threading.Lock()
_CACHE_PREFIX = "agent_run:"
_CACHE_TTL_SECONDS = 3600


def _now_iso() -> str:
    """实现 nowiso 的功能。
    
    :return: 返回 str 结果
    """
    return datetime.now(timezone.utc).isoformat()


def new_run_id() -> str:
    """实现 新建执行ID 的功能。
    
    :return: 返回 str 结果
    """
    return str(uuid.uuid4())


def save_run(run: dict[str, Any]) -> None:
    """保存 agent run 状态到内存和 Redis。"""
    run_id = run["id"]
    run["updated_at"] = _now_iso()
    with _LOCK:
        _MEMORY[run_id] = run
    try:
        set_cache(f"{_CACHE_PREFIX}{run_id}", run, expire=timedelta(seconds=_CACHE_TTL_SECONDS))
    except Exception as exc:
        logger.warning("Redis 缓存写入失败，仅内存存储 run_id=%s: %s", run_id, exc)


def load_run(run_id: str) -> dict[str, Any] | None:
    """加载 agent run 状态，优先内存，其次 Redis。"""
    with _LOCK:
        if run_id in _MEMORY:
            return dict(_MEMORY[run_id])
    try:
        cached = get_cache(f"{_CACHE_PREFIX}{run_id}")
        if cached:
            with _LOCK:
                _MEMORY[run_id] = cached
            return dict(cached)
    except Exception as exc:
        logger.warning("Redis 缓存读取失败 run_id=%s: %s", run_id, exc)
    return None


def patch_run(run_id: str, **updates: Any) -> dict[str, Any] | None:
    """更新 agent run 状态。"""
    run = load_run(run_id)
    if not run:
        return None
    run.update(updates)
    save_run(run)
    return run


def patch_task(run_id: str, task_id: str, **updates: Any) -> dict[str, Any] | None:
    """更新 agent run 中的特定任务状态。"""
    run = load_run(run_id)
    if not run:
        return None
    tasks = run.get("tasks") or []
    for task in tasks:
        if task.get("id") == task_id:
            task.update(updates)
            task["updated_at"] = _now_iso()
            break
    run["tasks"] = tasks
    save_run(run)
    return run
