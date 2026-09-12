"""Refresh 令牌轮转黑名单：优先 Redis（多实例 / 重启后仍拒绝已吊销 refresh），失败降级进程内内存。"""

from __future__ import annotations

import hashlib
import logging
import threading
import time
from typing import Any, Dict, Optional, Tuple

import redis

from app.core.config import settings

log = logging.getLogger(__name__)

_LOCK = threading.Lock()
_REDIS: Optional[redis.Redis] = None
_RECONNECT_BACKOFF_UNTIL = 0.0
_RECONNECT_BACKOFF_SEC = 10.0

KEY_PREFIX = "jwt:rtbl:"

_memory_lock = threading.Lock()
_memory_entries: dict[str, float] = {}
_MEMORY_MAX = 50_000


def reset_refresh_blacklist_redis_client() -> None:
    """关闭并重置 Redis 客户端缓存（测试 / 运维）。"""
    global _REDIS, _RECONNECT_BACKOFF_UNTIL
    with _LOCK:
        if _REDIS is not None:
            try:
                _REDIS.close()
            except Exception:
                pass
            _REDIS = None
        _RECONNECT_BACKOFF_UNTIL = 0.0


def clear_memory_fallback() -> None:
    """清空内存降级表（仅测试）。"""
    with _memory_lock:
        _memory_entries.clear()


def get_refresh_blacklist_redis() -> Optional[redis.Redis]:
    """
    懒连接 Redis；`REDIS_ENABLED=False` 时返回 None（仅用内存）。
    连接失败时打日志并返回 None，由调用方走内存降级；失败后在短时间内不再反复建连。
    """
    global _REDIS, _RECONNECT_BACKOFF_UNTIL
    if not settings.REDIS_ENABLED:
        return None
    with _LOCK:
        now_m = time.monotonic()
        if _REDIS is None and now_m < _RECONNECT_BACKOFF_UNTIL:
            return None
        if _REDIS is not None:
            try:
                _REDIS.ping()
                return _REDIS
            except Exception as exc:
                log.warning(
                    "refresh_token_blacklist: Redis ping 失败，将重连: %s", exc)
                try:
                    _REDIS.close()
                except Exception:
                    pass
                _REDIS = None
        client = _try_open_redis()
        _REDIS = client
        if client is None:
            _RECONNECT_BACKOFF_UNTIL = time.monotonic() + _RECONNECT_BACKOFF_SEC
        else:
            _RECONNECT_BACKOFF_UNTIL = 0.0
        return _REDIS


def _try_open_redis() -> Optional[redis.Redis]:
    """_try_open_redis。
    :return: 返回处理结果。
    """
    pw = (settings.REDIS_PASSWORD or "").strip() or None
    try:
        client = redis.from_url(
            settings.REDIS_URL,
            password=pw,
            decode_responses=True,
            socket_connect_timeout=2.0,
            socket_timeout=2.0,
        )
        client.ping()
        log.info("refresh_token_blacklist: 已连接 Redis（%s）",
                 settings.REDIS_URL.split("@")[-1])
        return client
    except Exception as exc:
        log.warning(
            "refresh_token_blacklist: Redis 不可用，降级内存黑名单: %s",
            exc,
        )
        return None


def _redis_key(revocation_key: str) -> str:
    """_redis_key。

    参数说明：
    :param revocation_key: 参数 revocation_key
    :return: 返回处理结果。
    """
    return f"{KEY_PREFIX}{revocation_key}"


def refresh_token_revocation_key(
        raw_token: str, payload: Dict[str, Any]) -> Tuple[str, Optional[float]]:
    """refresh_token_revocation_key。

    参数说明：
    :param raw_token: 参数 raw_token
    :param payload: 参数 payload
    :return: 返回处理结果。
    """
    # Some legacy callers/tests inject mock request objects; a token-like object
    # still needs to produce a deterministic fingerprint instead of raising.
    if not isinstance(raw_token, str):
        raw_token = str(raw_token)
    jti = payload.get("jti")
    if isinstance(jti, str) and jti:
        exp = payload.get("exp")
        exp_f = float(exp) if isinstance(exp, (int, float)) else None
        return jti, exp_f
    digest = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    exp = payload.get("exp")
    exp_f = float(exp) if isinstance(exp, (int, float)) else None
    return f"fp:{digest}", exp_f


def _ttl_seconds(exp_ts: Optional[float]) -> int:
    """
    与 Refresh Token 自然失效对齐：TTL = JWT exp 前剩余秒数；
    无 exp 时使用配置的整段 refresh 有效期（秒）。
    """
    now = time.time()
    if exp_ts is not None and exp_ts > now:
        return max(1, int(exp_ts - now))
    return max(1, int(settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400))


def _memory_prune_unlocked(now: float) -> None:
    """_memory_prune_unlocked。

    参数说明：
    :param now: 参数 now
    :return: 返回处理结果。
    """
    dead = [k for k, exp in _memory_entries.items() if exp < now]
    for k in dead:
        _memory_entries.pop(k, None)


def _memory_is_revoked(key: str) -> bool:
    """_memory_is_revoked。

    参数说明：
    :param key: 参数 key
    :return: 返回处理结果。
    """
    now = time.time()
    with _memory_lock:
        _memory_prune_unlocked(now)
        exp = _memory_entries.get(key)
        return exp is not None and exp > now


def _memory_revoke(key: str, ttl_seconds: int) -> None:
    """_memory_revoke。

    参数说明：
    :param key: 参数 key
    :param ttl_seconds: 参数 ttl_seconds
    :return: 返回处理结果。
    """
    until = time.time() + ttl_seconds
    with _memory_lock:
        _memory_prune_unlocked(time.time())
        _memory_entries[key] = until
        if len(_memory_entries) > _MEMORY_MAX:
            sorted_items = sorted(
                _memory_entries.items(),
                key=lambda kv: kv[1])
            for k, _ in sorted_items[: max(1, len(_memory_entries) // 4)]:
                _memory_entries.pop(k, None)


def query_refresh_blacklist(revocation_key: str) -> bool:
    """
    黑名单查询：存在则视为已吊销（优先 Redis，其次内存降级）。
    与 `is_refresh_key_revoked` 等价，便于语义化调用。
    """
    return is_refresh_key_revoked(revocation_key)


def is_refresh_key_revoked(key: str) -> bool:
    """is_refresh_key_revoked。

    参数说明：
    :param key: 参数 key
    :return: 返回处理结果。
    """
    if not key:
        return False
    name = _redis_key(key)
    r = get_refresh_blacklist_redis()
    if r is not None:
        try:
            return bool(r.exists(name))
        except Exception as exc:
            log.warning(
                "refresh_token_blacklist: Redis EXISTS 失败，降级内存: %s", exc)
            reset_refresh_blacklist_redis_client()
    return _memory_is_revoked(key)


def revoke_refresh_key(key: str, exp_ts: Optional[float]) -> None:
    """revoke_refresh_key。

    参数说明：
    :param key: 参数 key
    :param exp_ts: 参数 exp_ts
    :return: 返回处理结果。
    """
    if not key:
        return
    ttl = _ttl_seconds(exp_ts)
    name = _redis_key(key)
    r = get_refresh_blacklist_redis()
    if r is not None:
        try:
            r.setex(name, ttl, "1")
            # 本地镜像：Redis EXISTS 偶发失败时本进程仍可拒绝（与 Redis TTL 一致，到期即失）
            _memory_revoke(key, ttl)
            return
        except Exception as exc:
            log.warning(
                "refresh_token_blacklist: Redis SETEX 失败，降级内存: %s", exc)
            reset_refresh_blacklist_redis_client()
    _memory_revoke(key, ttl)
