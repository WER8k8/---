# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Access Token 黑名单：登出后将 JWT jti 加入黑名单，阻止已登出令牌继续使用。

优先 Redis（多实例共享），不可用时降级进程内内存。
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Optional

from app.core.refresh_token_blacklist import (
    KEY_PREFIX,
    _memory_lock,
    _memory_entries,
    _memory_prune_unlocked,
    _ttl_seconds,
    get_refresh_blacklist_redis,
    _redis_key,
)

AT_KEY_PREFIX = "jwt:atbl:"
_AT_MEMORY_MAX = 100_000

log = logging.getLogger(__name__)


def _at_redis_key(jti: str) -> str:
    """_at_redis_key。

    参数说明：
    :param jti: 参数 jti
    :return: 返回处理结果。
    """
    return f"{AT_KEY_PREFIX}{jti}"


def revoke_access_token(jti: str, exp_ts: Optional[float]) -> None:
    """将 access token 的 jti 加入黑名单，TTL 与 JWT 过期时间对齐。"""
    if not jti:
        return
    ttl = _ttl_seconds(exp_ts)
    key = _at_redis_key(jti)
    r = get_refresh_blacklist_redis()
    if r is not None:
        try:
            r.setex(key, ttl, "1")
            _at_memory_revoke(jti, ttl)
            return
        except Exception as exc:
            log.warning(
                "access_token_blacklist: Redis SETEX 失败，降级内存: %s", exc)
    _at_memory_revoke(jti, ttl)


def is_access_token_revoked(jti: str) -> bool:
    """检查 access token 的 jti 是否在黑名单中。"""
    if not jti:
        return False
    key = _at_redis_key(jti)
    r = get_refresh_blacklist_redis()
    if r is not None:
        try:
            return bool(r.exists(key))
        except Exception as exc:
            log.warning(
                "access_token_blacklist: Redis EXISTS 失败，降级内存: %s", exc)
    return _at_memory_is_revoked(jti)


def _at_memory_revoke(jti: str, ttl_seconds: int) -> None:
    """_at_memory_revoke。

    参数说明：
    :param jti: 参数 jti
    :param ttl_seconds: 参数 ttl_seconds
    :return: 返回处理结果。
    """
    until = time.time() + ttl_seconds
    with _memory_lock:
        _memory_prune_unlocked(time.time())
        _memory_entries[f"at:{jti}"] = until
        # 清理超出上限的旧条目
        at_entries = {k: v for k, v in _memory_entries.items() if k.startswith("at:")}
        if len(at_entries) > _AT_MEMORY_MAX:
            sorted_items = sorted(at_entries.items(), key=lambda kv: kv[1])
            for k, _ in sorted_items[: max(1, len(at_entries) // 4)]:
                _memory_entries.pop(k, None)


def _at_memory_is_revoked(jti: str) -> bool:
    """_at_memory_is_revoked。

    参数说明：
    :param jti: 参数 jti
    :return: 返回处理结果。
    """
    key = f"at:{jti}"
    now = time.time()
    with _memory_lock:
        _memory_prune_unlocked(now)
        exp = _memory_entries.get(key)
        return exp is not None and exp > now
