"""海外 B2B 发布适配器单测：只验「诚实路径」，全程不联网。

覆盖：
1. 缺凭证 → raise 且消息含 PLATFORM_NOT_CONFIGURED（任务落 failed，不假成功）
2. 凭证齐 + 平台回链接 → 返回该链接，url_source=platform
3. 平台只回 offer_id → 按模板拼链接，并如实标 url_source=constructed_from_offer_id
4. 无链接模板的平台（GlobalSources）只回 offer_id → 仍判失败，不拿官网 URL 冒充
5. 主链解析：B2B 平台绝不再兜底成 zhihu（历史 P0）
"""

from __future__ import annotations

import pytest

from app.models.content import GeneratedContent, Platform, PlatformAccount
from app.services.platforms import b2b_global
from app.services.platforms.b2b_global import (
    AlibabaPublisherAdapter,
    GlobalSourcesPublisherAdapter,
    MadeInChinaPublisherAdapter,
)
from app.services.publish_capability_registry import PLATFORM_NOT_CONFIGURED


class _FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code
        self.content = b"{}"

    def json(self) -> dict:
        return self._payload

    def raise_for_status(self) -> None:
        return None


class _FakeClient:
    """替掉 httpx.AsyncClient，记录请求但不发包。"""

    def __init__(self, payload: dict, sink: list):
        self._payload = payload
        self._sink = sink

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, json=None, headers=None, **kwargs):
        self._sink.append({"url": url, "json": json, "headers": headers or {}})
        return _FakeResponse(self._payload)


def _install(monkeypatch, payload: dict) -> list:
    sink: list = []
    monkeypatch.setattr(
        b2b_global.httpx,
        "AsyncClient",
        lambda *a, **k: _FakeClient(payload, sink),
    )
    return sink


def _platform(name: str) -> Platform:
    return Platform(id=f"plat-{name}", name=name, platform_type="b2b", region="global")


def _account(**token_data) -> PlatformAccount:
    return PlatformAccount(id="acc-1", platform_id="plat-x", account_name="t", token_data=dict(token_data))


def _content() -> GeneratedContent:
    return GeneratedContent(title="Ceramic Fiber Board", content="200 mm density 128k", status="draft")


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """清掉可能存在的 env 兜底凭证，保证「缺就是缺」。"""
    for name in ("ALIBABA_MEMBER_ID", "ALIBABA_ACCESS_TOKEN", "ALIBABA_SESSION_COOKIE",
                 "MIC_ACCESS_TOKEN", "GS_API_KEY"):
        monkeypatch.delenv(name, raising=False)


def test_alibaba_missing_credentials_raises_not_configured(monkeypatch):
    _install(monkeypatch, {"url": "https://x/should-not-be-called"})
    adapter = AlibabaPublisherAdapter(db=None)
    with pytest.raises(RuntimeError) as exc:
        adapter.publish(_platform("Alibaba.com"), _account(), _content())
    assert PLATFORM_NOT_CONFIGURED in str(exc.value)


def test_alibaba_returns_platform_url(monkeypatch):
    sink = _install(monkeypatch, {"url": "https://www.alibaba.com/product-detail/a.html"})
    adapter = AlibabaPublisherAdapter(db=None)
    account = _account(
        alibaba_member_id="m1",
        alibaba_access_token="tok-abc",
    )
    url = adapter.publish(_platform("Alibaba.com"), account, _content())
    assert url == "https://www.alibaba.com/product-detail/a.html"
    assert sink, "应发起一次 offer 提交"
    # 有 access_token 时走 OAuth 头，不回退到 Cookie
    assert sink[0]["headers"].get("Authorization", "").startswith("Bearer ")
    assert "Cookie" not in sink[0]["headers"]


def test_alibaba_cookie_fallback_when_no_access_token(monkeypatch):
    sink = _install(monkeypatch, {"offer_id": "9001"})
    adapter = AlibabaPublisherAdapter(db=None)
    account = _account(alibaba_member_id="m1", alibaba_session_cookie="x=1")
    url = adapter.publish(_platform("Alibaba.com"), account, _content())
    assert "9001" in url
    assert sink[0]["headers"].get("Cookie") == "x=1"


def test_constructed_url_is_labeled(monkeypatch):
    _install(monkeypatch, {"data": {"id": "7788"}})
    adapter = MadeInChinaPublisherAdapter(db=None)
    url = adapter.publish(
        _platform("Made-in-China.com"), _account(mic_access_token="t"), _content()
    )
    assert url == "https://www.made-in-china.com/products/7788.html"


def test_globalsources_without_url_template_is_not_faked(monkeypatch):
    """GlobalSources 无详情页模板：平台不回链接就必须判失败，不拿 base_url 冒充。"""
    _install(monkeypatch, {"id": "555"})
    adapter = GlobalSourcesPublisherAdapter(db=None)
    with pytest.raises(RuntimeError) as exc:
        adapter.publish(_platform("Global Sources"), _account(gs_api_key="k"), _content())
    assert "未返回作品链接" in str(exc.value)


def test_b2b_platforms_never_resolve_to_zhihu():
    """历史 P0：_publisher_key 末尾 return "zhihu" 会把海外平台误发到知乎。"""
    from app.services.publish_dispatch_service import _publisher_key

    for name in ("Alibaba.com", "Reddit", "Medium", "Global Sources", "Kompass"):
        assert _publisher_key(_platform(name)) != "zhihu", name


def test_b2b_adapters_registered_in_dispatch_mapping():
    from app.services.publish_dispatch_service import _NAME_ADAPTER_IMPORTS

    for name in ("Alibaba.com", "Made-in-China.com", "Global Sources"):
        assert name in _NAME_ADAPTER_IMPORTS, name
        assert _NAME_ADAPTER_IMPORTS[name][0] == "app.services.platforms.b2b_global"


def test_dispatch_raises_when_no_publisher(monkeypatch):
    """无适配器且无发布器键 → 明确失败，不改投其它平台。"""
    from app.services.publish_dispatch_service import SeoPublishService

    _install(monkeypatch, {})
    svc = SeoPublishService(db=None)
    plat = Platform(id="p2", name="Kompass", platform_type="b2b", region="global")
    with pytest.raises(RuntimeError) as exc:
        svc._dispatch_to_platform(plat, _account(), _content())
    assert "PLATFORM_NOT_IMPLEMENTED" in str(exc.value)
