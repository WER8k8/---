# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""GJ-U3 汇率服务配对反证测试。

- 正向：Frankfurter 载荷 → 四货币对派生（EUR/USD = 1/EUR，与上游 parsePayload 逐字段一致）；
- fail-closed：非 200 / 坏载荷 / 网络异常 → available=False，**绝不伪造数值**；
- 缓存：TTL 内第二次调用不重发请求；
- SSRF 守卫：http / 非 https / host 白名单外 → 拒绝。
"""
from __future__ import annotations

import socket

import pytest

from app.services import exchange_rate_service as svc


CANNED = {
    "base": "USD",
    "date": "2026-10-01",
    "rates": {"CNY": 7.1, "EUR": 0.9, "GBP": 0.8, "JPY": 150.0},
}


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    svc.reset_cache_for_test()
    monkeypatch.delenv("GOODJOB_EXCHANGE_RATES_URL", raising=False)
    yield
    svc.reset_cache_for_test()


def _patch_http(monkeypatch, *, status=200, payload=None, calls=None):
    def _fake_getaddrinfo(host, port, **kwargs):
        # 密闭性：DNS 解析返回公网 IP（1.2.3.4 is_global，通过 SSRF 守卫）
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.2.3.4", port))]

    monkeypatch.setattr(svc.socket, "getaddrinfo", _fake_getaddrinfo)

    def _fake_get(url, **kwargs):
        if calls is not None:
            calls.append(url)
        assert url.startswith("https://api.frankfurter.dev"), f"SSRF: {url}"

        class _Resp:
            status_code = status

            def json(self):
                return payload if payload is not None else CANNED

        return _Resp()

    monkeypatch.setattr(svc.httpx, "get", _fake_get)


class TestPositive:
    def test_derives_four_pairs(self, monkeypatch):
        _patch_http(monkeypatch)
        data = svc.get_latest()
        assert data["available"] is True
        pairs = {r["pair"]: r["value"] for r in data["rates"]}
        assert pairs["USD/CNY"] == 7.1
        assert pairs["EUR/USD"] == pytest.approx(1 / 0.9, abs=1e-6)
        assert pairs["GBP/USD"] == pytest.approx(1.25, abs=1e-6)
        assert pairs["USD/JPY"] == 150.0
        assert data["date"] == "2026-10-01" and data["base"] == "USD"
        assert data["source"] == "Frankfurter / ECB reference rates"

    def test_cache_within_ttl_no_refetch(self, monkeypatch):
        calls: list[str] = []
        _patch_http(monkeypatch, calls=calls)
        svc.get_latest()
        svc.get_latest()
        assert len(calls) == 1, "TTL 内第二次调用不得重发请求"

    def test_force_bypasses_cache(self, monkeypatch):
        calls: list[str] = []
        _patch_http(monkeypatch, calls=calls)
        svc.get_latest()
        svc.get_latest(force=True)
        assert len(calls) == 2

    def test_get_rate_helper(self, monkeypatch):
        _patch_http(monkeypatch)
        assert svc.get_rate("USD/CNY") == 7.1
        assert svc.get_rate("USD/AUD") is None


class TestFailClosed:
    def test_http_error_never_fabricates(self, monkeypatch):
        _patch_http(monkeypatch, status=503)
        data = svc.get_latest()
        assert data["available"] is False
        assert "503" in data["reason"]
        assert "rates" not in data

    def test_bad_payload_never_fabricates(self, monkeypatch):
        _patch_http(monkeypatch, payload={"base": "EUR", "date": "2026-10-01", "rates": {}})
        data = svc.get_latest()
        assert data["available"] is False

    def test_missing_cny_never_fabricates(self, monkeypatch):
        _patch_http(monkeypatch, payload={"base": "USD", "date": "2026-10-01", "rates": {"EUR": 0.9, "GBP": 0.8, "JPY": 150}})
        data = svc.get_latest()
        assert data["available"] is False
        assert "CNY" in data["reason"]

    def test_network_exception_never_fabricates(self, monkeypatch):
        def _boom(url, **kwargs):
            raise ConnectionError("upstream down")

        monkeypatch.setattr(svc.httpx, "get", _boom)
        data = svc.get_latest()
        assert data["available"] is False
        assert svc.get_rate("USD/CNY") is None


class TestSSRFGuard:
    def test_http_scheme_rejected(self, monkeypatch):
        monkeypatch.setenv("GOODJOB_EXCHANGE_RATES_URL", "http://api.frankfurter.dev/v1/latest")
        data = svc.get_latest()
        assert data["available"] is False
        assert "https" in data["reason"]

    def test_foreign_host_rejected(self, monkeypatch):
        monkeypatch.setenv("GOODJOB_EXCHANGE_RATES_URL", "https://evil.example.com/v1/latest")
        data = svc.get_latest()
        assert data["available"] is False
        assert "api.frankfurter.dev" in data["reason"]

    def test_private_host_rejected(self, monkeypatch):
        monkeypatch.setenv("GOODJOB_EXCHANGE_RATES_URL", "https://localhost/v1/latest")
        data = svc.get_latest()
        assert data["available"] is False
