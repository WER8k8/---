# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""汇率服务（GJ-U3 · GoodJob 上游 v1.9.1 同源只读接入）。

上游参照：``_external/goodjob-crm/backend/src/exchange-rates.ts``（Frankfurter / ECB 参考价）。
- 数据源固定 https://api.frankfurter.dev（SSRF 四重约束：仅 https + host 白名单 +
  解析 IP 拒绝私网/环回/链路本地/保留地址 + 禁止重定向）；
- 15 分钟进程内缓存（与上游一致）；失败 **fail-closed**（available=False），绝不伪造汇率（交付求真）；
- 只读消费面：报价/BOQ 展示层可调用；**不改 boq_calculator 计价数学（零漂移）**。
"""
from __future__ import annotations

import ipaddress
import logging
import os
import re
import socket
import time
from typing import Any, Optional
from urllib.parse import urlparse

import httpx

logger = logging.getLogger("uj.exchange_rates")

_DEFAULT_URL = "https://api.frankfurter.dev/v1/latest?base=USD&symbols=CNY,EUR,GBP,JPY"
_ALLOWED_HOST = "api.frankfurter.dev"
_TTL_SECONDS = 15 * 60
_TIMEOUT_SECONDS = 8.0

_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")

_cache: dict[str, Any] = {"payload": None, "at": 0.0}


class ExchangeRateSourceError(ValueError):
    """汇率源配置或响应不合规（含 SSRF 守卫拒绝）。"""


def _assert_url_safe(url: str) -> None:
    """SSRF 守卫：https + host 白名单 + 解析 IP 全部为公网（拒私网/环回/链路本地/保留/组播）。"""
    parsed = urlparse(url)
    if parsed.scheme != "https" or (parsed.hostname or "") != _ALLOWED_HOST:
        raise ExchangeRateSourceError(
            f"汇率源必须为 https://{_ALLOWED_HOST}（拒绝 {parsed.scheme or '?'}://{parsed.hostname or '?'}）"
        )
    try:
        infos = socket.getaddrinfo(parsed.hostname, 443, proto=socket.IPPROTO_TCP)
    except OSError as exc:
        raise ExchangeRateSourceError(f"汇率源主机解析失败: {exc}") from exc
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
            or not ip.is_global
        ):
            raise ExchangeRateSourceError(f"汇率源主机解析到非公网地址，已拒绝: {ip}")


def _configured_url() -> str:
    url = (os.getenv("GOODJOB_EXCHANGE_RATES_URL") or "").strip() or _DEFAULT_URL
    _assert_url_safe(url)
    return url


def _finite_rate(payload: dict, currency: str) -> float:
    value = payload.get("rates", {}).get(currency)
    try:
        value = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        value = 0.0
    if value <= 0:
        raise ExchangeRateSourceError(f"汇率数据缺少有效的 {currency} 报价")
    return value


def _parse(payload: Any) -> dict:
    """镜像上游 parsePayload：USD 基准 + 四货币对派生。"""
    if not isinstance(payload, dict):
        raise ExchangeRateSourceError("汇率数据格式不正确")
    date = payload.get("date")
    if payload.get("base") != "USD" or not isinstance(date, str) or not _DATE_RE.fullmatch(date):
        raise ExchangeRateSourceError("汇率数据格式不正确")
    eur = _finite_rate(payload, "EUR")
    gbp = _finite_rate(payload, "GBP")
    return {
        "date": date,
        "base": "USD",
        "rates": [
            {"pair": "USD/CNY", "value": _finite_rate(payload, "CNY"), "decimals": 4},
            {"pair": "EUR/USD", "value": round(1 / eur, 6), "decimals": 4},
            {"pair": "GBP/USD", "value": round(1 / gbp, 6), "decimals": 4},
            {"pair": "USD/JPY", "value": _finite_rate(payload, "JPY"), "decimals": 2},
        ],
        "source": "Frankfurter / ECB reference rates",
    }


def get_latest(*, force: bool = False) -> dict[str, Any]:
    """当日汇率（fail-closed）。成功：{"available": True, date, base, rates, source, fetched_at}；
    任何失败：{"available": False, "reason": ...}——调用方必须按不可用处理，禁止伪造数值。"""
    now = time.monotonic()
    if not force and _cache["payload"] is not None and now - _cache["at"] < _TTL_SECONDS:
        return {**_cache["payload"], "available": True}
    try:
        url = _configured_url()
        response = httpx.get(
            url,
            headers={"accept": "application/json"},
            timeout=_TIMEOUT_SECONDS,
            follow_redirects=False,  # SSRF：禁止重定向绕过白名单
        )
        if response.status_code != 200:
            raise ExchangeRateSourceError(f"汇率源返回 HTTP {response.status_code}")
        parsed = _parse(response.json())
    except Exception as exc:  # noqa: BLE001 —— fail-closed，不伪造
        logger.warning("exchange rates unavailable: %s", exc)
        return {"available": False, "reason": f"{type(exc).__name__}: {exc}"}
    payload = {**parsed, "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    _cache["payload"] = payload
    _cache["at"] = now
    return {**payload, "available": True}


def get_rate(pair: str) -> Optional[float]:
    """便捷取值：如 "USD/CNY"。不可用时返回 None（调用方自行降级）。"""
    data = get_latest()
    if not data.get("available"):
        return None
    for item in data["rates"]:
        if item["pair"] == pair:
            return float(item["value"])
    return None


def reset_cache_for_test() -> None:
    _cache["payload"] = None
    _cache["at"] = 0.0
