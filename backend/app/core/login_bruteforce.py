# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""登录暴力破解防护：优先 Redis（多实例共享），失败降级进程内内存；接口与阈值行为保持不变。"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import logging
import threading
import time
from dataclasses import dataclass
from typing import Any, Optional, Tuple

from app.core.config import settings

log = logging.getLogger(__name__)

MAX_FAIL_PER_IDENTITY = 5
LOCK_SECONDS = 15 * 60
IP_FAIL_THRESHOLD = 40
IP_LOCK_SECONDS = 15 * 60

# Redis 键 TTL：覆盖最长锁定期并留余量，便于空闲键自动回收
_STATE_TTL_SECONDS = max(LOCK_SECONDS, IP_LOCK_SECONDS) + 300

_LUA_RECORD = """
local raw = redis.call('GET', KEYS[1])
local fails = 0
local lock_until = 0
if raw then
  local o = cjson.decode(raw)
  fails = tonumber(o.fails) or 0
  lock_until = tonumber(o.lock_until) or 0
end
local now = tonumber(ARGV[1])
local maxf = tonumber(ARGV[2])
local locksec = tonumber(ARGV[3])
local ttl = tonumber(ARGV[4])
if lock_until > now then
  fails = fails + 1
else
  if lock_until > 0 then
    fails = 0
  end
  fails = fails + 1
end
if fails >= maxf then
  lock_until = now + locksec
end
redis.call('SET', KEYS[1], cjson.encode({fails = fails, lock_until = lock_until}), 'EX', ttl)
return fails
"""


@dataclass
class _Entry:
    fails: int = 0
    lock_until: float = 0.0


_identity_store: dict[str, _Entry] = {}
_ip_store: dict[str, _Entry] = {}
_memory_lock = threading.Lock()
_last_cleanup: float = 0.0
_CLEANUP_INTERVAL: float = 300.0  # 5 minutes


def _cleanup_stale_entries(now: float) -> None:
    """Remove entries whose lock has expired and that have not been updated
    recently.  Called periodically (every ~5 min) to prevent unbounded growth
    of the in-memory stores when Redis is unavailable."""
    global _last_cleanup
    if now - _last_cleanup < _CLEANUP_INTERVAL:
        return
    _last_cleanup = now
    cutoff = now - 3600.0  # 1 hour of inactivity
    with _memory_lock:
        for store in (_identity_store, _ip_store):
            stale = [k for k, e in store.items()
                     if e.lock_until < now and e.lock_until < cutoff]
            for k in stale:
                del store[k]


def _identity_key(ip: str, username_or_email: str) -> str:
    """_identity_key。

    参数说明：
    :param ip: 参数 ip
    :param username_or_email: 参数 username_or_email
    :return: 返回处理结果。
    """
    raw = f"{ip}|{username_or_email.strip().lower()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _now_mono() -> float:
    """_now_mono。
    :return: 返回处理结果。
    """
    return time.monotonic()


def _redis_prefix() -> str:
    """_redis_prefix。
    :return: 返回处理结果。
    """
    p = getattr(settings, "LOGIN_BF_REDIS_PREFIX", None) or "login_bf"
    return str(p).strip() or "login_bf"


def _redis_client():
    """复用 refresh 黑名单的懒连接 Redis，避免额外连接池。"""
    if not getattr(settings, "LOGIN_BF_USE_REDIS", True):
        return None
    if not settings.REDIS_ENABLED:
        return None
    try:
        from app.core.refresh_token_blacklist import \
            get_refresh_blacklist_redis

        return get_refresh_blacklist_redis()
    except Exception as exc:  # pragma: no cover - 导入失败极少
        log.warning("login_bruteforce: 无法获取 Redis 客户端: %s", exc)
        return None


def _redis_key_ip(ip: str) -> str:
    """_redis_key_ip。

    参数说明：
    :param ip: 参数 ip
    :return: 返回处理结果。
    """
    return f"{_redis_prefix()}:ip:{ip}"


def _redis_key_id(ik: str) -> str:
    """_redis_key_id。

    参数说明：
    :param ik: 参数 ik
    :return: 返回处理结果。
    """
    return f"{_redis_prefix()}:id:{ik}"


def _redis_check(r: Any, client_ip: str,
                 username_or_email: str) -> Optional[Tuple[int, str]]:
    """_redis_check。

    参数说明：
    :param r: 参数 r
    :param client_ip: 参数 client_ip
    :param username_or_email: 参数 username_or_email
    :return: 返回处理结果。
    """
    now = time.time()
    ik = _identity_key(client_ip, username_or_email)
    for key in (_redis_key_ip(client_ip), _redis_key_id(ik)):
        try:
            raw = r.get(key)
            if not raw:
                continue
            o = json.loads(raw)
            lu = float(o.get("lock_until") or 0)
            if lu > now:
                return 429, "请求过于频繁，请稍后再试"
        except Exception as exc:
            log.warning("login_bruteforce: Redis 读取失败，将降级内存: %s", exc)
            raise
    return None


def _redis_record_failure(client_ip: str, username_or_email: str) -> None:
    """_redis_record_failure。

    参数说明：
    :param client_ip: 参数 client_ip
    :param username_or_email: 参数 username_or_email
    :return: 返回处理结果。
    """
    r = _redis_client()
    if r is None:
        _memory_record_failure(client_ip, username_or_email)
        return
    now = time.time()
    ik = _identity_key(client_ip, username_or_email)
    ttl = int(
        getattr(
            settings,
            "LOGIN_BF_REDIS_STATE_TTL",
            _STATE_TTL_SECONDS))
    args_id = [now, MAX_FAIL_PER_IDENTITY, LOCK_SECONDS, ttl]
    args_ip = [now, IP_FAIL_THRESHOLD, IP_LOCK_SECONDS, ttl]
    try:
        pipe = r.pipeline(transaction=True)
        pipe.eval(_LUA_RECORD, 1, _redis_key_id(ik),
                  *args_id)  # type: ignore[arg-type]
        pipe.eval(_LUA_RECORD, 1, _redis_key_ip(client_ip),
                  *args_ip)  # type: ignore[arg-type]
        pipe.execute()
    except Exception as exc:
        log.warning("login_bruteforce: Redis 写入失败，将降级内存: %s", exc)
        raise


def _redis_record_success(client_ip: str, username_or_email: str) -> None:
    """_redis_record_success。

    参数说明：
    :param client_ip: 参数 client_ip
    :param username_or_email: 参数 username_or_email
    :return: 返回处理结果。
    """
    r = _redis_client()
    if r is None:
        _memory_record_success(client_ip, username_or_email)
        return
    ik = _identity_key(client_ip, username_or_email)
    try:
        r.delete(_redis_key_id(ik))
    except Exception as exc:
        log.warning("login_bruteforce: Redis 删除失败，将降级内存: %s", exc)
        raise


def _memory_check(
        client_ip: str, username_or_email: str) -> Optional[Tuple[int, str]]:
    """_memory_check。

    参数说明：
    :param client_ip: 参数 client_ip
    :param username_or_email: 参数 username_or_email
    :return: 返回处理结果。
    """
    if not client_ip:
        client_ip = "unknown"
    t = _now_mono()
    with _memory_lock:
        ip_e = _ip_store.get(client_ip)
        if ip_e and ip_e.lock_until > t:
            return 429, "请求过于频繁，请稍后再试"

        ik = _identity_key(client_ip, username_or_email)
        e = _identity_store.get(ik)
        if e and e.lock_until > t:
            return 429, "请求过于频繁，请稍后再试"
    return None


def _memory_record_failure(client_ip: str, username_or_email: str) -> None:
    """_memory_record_failure。

    参数说明：
    :param client_ip: 参数 client_ip
    :param username_or_email: 参数 username_or_email
    :return: 返回处理结果。
    """
    if not client_ip:
        client_ip = "unknown"
    t = _now_mono()
    # Periodic cleanup to prevent unbounded memory growth
    _cleanup_stale_entries(time.time())
    with _memory_lock:
        ik = _identity_key(client_ip, username_or_email)
        e = _identity_store.get(ik) or _Entry()
        if e.lock_until > t:
            e.fails += 1
        else:
            if e.lock_until > 0:
                e.fails = 0
            e.fails += 1
        if e.fails >= MAX_FAIL_PER_IDENTITY:
            e.lock_until = t + LOCK_SECONDS
        _identity_store[ik] = e
        ip_e = _ip_store.get(client_ip) or _Entry()
        if ip_e.lock_until > t:
            ip_e.fails += 1
        else:
            if ip_e.lock_until > 0:
                ip_e.fails = 0
            ip_e.fails += 1
        if ip_e.fails >= IP_FAIL_THRESHOLD:
            ip_e.lock_until = t + IP_LOCK_SECONDS
        _ip_store[client_ip] = ip_e


def _memory_record_success(client_ip: str, username_or_email: str) -> None:
    """_memory_record_success。

    参数说明：
    :param client_ip: 参数 client_ip
    :param username_or_email: 参数 username_or_email
    :return: 返回处理结果。
    """
    if not client_ip:
        client_ip = "unknown"
    with _memory_lock:
        ik = _identity_key(client_ip, username_or_email)
        _identity_store.pop(ik, None)


def check_login_allowed(
        client_ip: str, username_or_email: str) -> Optional[Tuple[int, str]]:
    """
    登录前调用。若应拒绝则返回 (http_status, message)，否则 None。
    message 使用中性文案，避免枚举账号/锁定原因组合攻击。
    """
    if str(getattr(settings, "ENVIRONMENT", "") or "").lower() == "development":
        return None
    if not client_ip:
        client_ip = "unknown"
    try:
        r = _redis_client()
        if r is None:
            return _memory_check(client_ip, username_or_email)
        blocked = _redis_check(r, client_ip, username_or_email)
        if blocked is not None:
            return blocked
        return None
    except Exception:
        log.warning(
            "login_bruteforce: Redis 不可用，使用进程内检查（多实例下防暴可能不一致）",
            exc_info=True,
        )
        return _memory_check(client_ip, username_or_email)


def record_login_failure(client_ip: str, username_or_email: str) -> None:
    """record_login_failure。

    参数说明：
    :param client_ip: 参数 client_ip
    :param username_or_email: 参数 username_or_email
    :return: 返回处理结果。
    """
    try:
        _redis_record_failure(client_ip, username_or_email)
    except Exception:
        log.warning(
            "login_bruteforce: Redis 记录失败降级内存",
            exc_info=True,
        )
        _memory_record_failure(client_ip, username_or_email)


def record_login_success(client_ip: str, username_or_email: str) -> None:
    """record_login_success。

    参数说明：
    :param client_ip: 参数 client_ip
    :param username_or_email: 参数 username_or_email
    :return: 返回处理结果。
    """
    try:
        _redis_record_success(client_ip, username_or_email)
    except Exception:
        log.warning(
            "login_bruteforce: Redis 清理失败降级内存",
            exc_info=True,
        )
        _memory_record_success(client_ip, username_or_email)


def client_ip_from_request(request: Any) -> str:
    """获取客户端真实 IP — 仅信任已知代理的 X-Forwarded-For"""
    direct_ip = request.client.host if request.client else "unknown"
    # 只有来自可信代理（本机/内网）时才信任 X-Forwarded-For
    if _is_trusted_proxy(direct_ip):
        fwd = request.headers.get("x-forwarded-for") or request.headers.get("X-Forwarded-For")
        if fwd:
            return fwd.split(",")[0].strip()
    return direct_ip or "unknown"


# Trusted proxy CIDR ranges
_TRUSTED_PROXY_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]


def _is_trusted_proxy(ip_str: str) -> bool:
    """Return True if *ip_str* belongs to a trusted proxy network."""
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    return any(addr in net for net in _TRUSTED_PROXY_NETWORKS)
