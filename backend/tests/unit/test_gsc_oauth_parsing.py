"""GSC 真链路单测：服务账号换票、siteUrl 编码、日期、响应 shape。全程离线。

补的三类历史缺陷：
1. GSC_SERVICE_ACCOUNT_JSON 只被 configured() 检查、从不参与鉴权（等于配了也查不到）
2. siteUrl 被剥掉 https:// 且未 URL 编码 → 资源路径不合法
3. 响应行读 data.data.rows（GSC 实际在顶层 rows）→ 指标恒为 0
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import httpx
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.services import google_search_console_service as gsc

_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048).private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
).decode("ascii")

_SA = {
    "type": "service_account",
    "client_email": "gsc-probe@project.iam.gserviceaccount.com",
    "private_key": _PRIVATE_KEY,
}


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    monkeypatch.delenv(gsc._GSC_API_KEY_ENV, raising=False)
    monkeypatch.delenv(gsc._GSC_SERVICE_ACCOUNT_ENV, raising=False)
    gsc._TOKEN_CACHE.clear()


def _run(coro):
    import asyncio

    return asyncio.run(coro)


class _Resp:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("boom", request=None, response=None)


class _Client:
    def __init__(self, sink, payload, status_code=200):
        self._sink = sink
        self._payload = payload
        self._status = status_code

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, json=None, params=None, headers=None):
        self._sink.append(
            {"url": url, "json": json, "params": params or {}, "headers": headers or {}}
        )
        return _Resp(self._payload, self._status)


def test_service_account_reads_inline_json_and_file(tmp_path, monkeypatch):
    monkeypatch.setenv(gsc._GSC_SERVICE_ACCOUNT_ENV, json.dumps(_SA))
    assert gsc._service_account()["client_email"] == _SA["client_email"]

    path = tmp_path / "sa.json"
    path.write_text(json.dumps(_SA), encoding="utf-8")
    monkeypatch.setenv(gsc._GSC_SERVICE_ACCOUNT_ENV, str(path))
    assert gsc._service_account() is not None

    # 残缺 / 非法内容一律视为未配置，不带着半套凭证去发请求
    monkeypatch.setenv(gsc._GSC_SERVICE_ACCOUNT_ENV, "{not json")
    assert gsc._service_account() is None
    monkeypatch.setenv(gsc._GSC_SERVICE_ACCOUNT_ENV, '{"client_email": "x"}')
    assert gsc._service_account() is None


def test_access_token_exchanges_and_caches(monkeypatch):
    calls = []

    def fake_post(url, data=None, timeout=None):
        calls.append({"url": url, "data": data})
        return _Resp({"access_token": "ya29probe", "expires_in": 3600})

    monkeypatch.setattr(gsc.httpx, "post", fake_post)
    token, err = gsc._access_token(_SA)
    assert token == "ya29probe" and err is None
    assert calls[0]["url"] == gsc._GSC_TOKEN_URL
    assert calls[0]["data"]["grant_type"].endswith("jwt-bearer")
    # assertion 是三段式 JWT，且绝不包含私钥原文
    assertion = calls[0]["data"]["assertion"]
    assert assertion.count(".") == 2
    assert "BEGIN" not in assertion and _PRIVATE_KEY[:24] not in assertion

    # 第二次走缓存，不再换票
    before = len(calls)
    assert gsc._access_token(_SA)[0] == "ya29probe"
    assert len(calls) == before


def test_access_token_failure_is_reported_without_leaking_key(monkeypatch):
    def boom(*a, **k):
        raise httpx.ConnectError("no network")

    monkeypatch.setattr(gsc.httpx, "post", boom)
    token, err = gsc._access_token(_SA)
    assert token is None
    assert err and "ConnectError" in err
    assert _PRIVATE_KEY[:24] not in err


def test_performance_uses_bearer_and_encoded_full_siteurl(monkeypatch):
    sink = []
    monkeypatch.setenv(gsc._GSC_SERVICE_ACCOUNT_ENV, json.dumps(_SA))
    monkeypatch.setattr(
        gsc.httpx, "post", lambda *a, **k: _Resp({"access_token": "tok", "expires_in": 3600})
    )
    monkeypatch.setattr(
        gsc.httpx,
        "AsyncClient",
        lambda *a, **k: _Client(
            sink,
            {
                "rows": [
                    {"keys": ["ceramic fiber board"], "clicks": 3, "impressions": 120, "position": 8.5},
                    {"keys": ["other query"], "clicks": 1, "impressions": 30, "position": 22.0},
                ]
            },
        ),
    )

    res = _run(
        gsc.GSCService.get_performance("https://example.com/", days=7, keyword="ceramic")
    )
    assert res["success"] is True
    req = sink[0]
    # siteUrl 保留 scheme 并整体转义（GSC 资源路径形如 sc-domain%3A 或 https%3A%2F%2F...）
    assert "https%3A%2F%2Fexample.com" in req["url"]
    assert req["headers"]["Authorization"] == "Bearer tok"
    assert "key" not in req["params"]
    # 日期是真值，不再是 N/A
    rng = req["json"]["dateRanges"][0]
    assert rng["startDate"] == gsc._days_ago(7)
    assert rng["endDate"] == datetime.now(timezone.utc).strftime("%Y-%m-%d")
    assert req["json"]["aggregations"] == ["clicks", "impressions", "position", "ctr"]
    # 指标按 GSC 真 shape 累加
    assert res["data"]["total_clicks"] == 4
    assert res["data"]["total_impressions"] == 150
    # keys 是与 dimensions 对齐的列表，query 命中按首位字符串比对
    assert res["data"]["keyword_hits"] == 1
    assert res["data"]["keyword_present"] is True


def test_pure_api_key_cannot_query_data_is_honest(monkeypatch):
    sink = []
    monkeypatch.setattr(
        gsc.httpx, "AsyncClient", lambda *a, **k: _Client(sink, {}, status_code=403)
    )
    res = _run(gsc.GSCService.get_performance("example.com", api_key="AIza-demo"))
    assert res["success"] is False
    assert "AIza-demo" not in json.dumps(res, ensure_ascii=False)
    assert "searchconsole.googleapis.com" not in (res["message"] or "")


def test_no_credential_still_not_configured():
    res = _run(gsc.GSCService.get_performance("example.com", api_key=""))
    assert res.get("data") is None or res["data"].get("mode") == "mock"
    assert gsc.GSCService.configured() is False


def test_rows_helper_accepts_both_shapes():
    assert gsc._rows({"rows": [{"clicks": 1}]}) == [{"clicks": 1}]
    assert gsc._rows({"data": {"rows": [{"clicks": 2}]}}) == [{"clicks": 2}]
    assert gsc._rows({}) == []
    assert gsc._sum_rows({"rows": [{"keys": ["q"], "clicks": 5}]}, "clicks") == 5
    # 指标缺失时保守 0，不把维度值当指标
    assert gsc._sum_rows({"rows": [{"keys": ["q"]}]}, "clicks") == 0
