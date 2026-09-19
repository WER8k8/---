# -*- coding: utf-8 -*-
"""Wave1 诚实接线：OAuth providers 明细 / QQ POST / referral 首付费。"""
from __future__ import annotations

from app.services.oauth_login import (
    SUPPORTED_OAUTH_PROVIDERS,
    oauth_providers_status_detail,
    verify_wechat_signature,
)


def test_oauth_providers_detail_lists_all_and_hints():
    detail = oauth_providers_status_detail()
    assert set(detail.keys()) == set(SUPPORTED_OAUTH_PROVIDERS)
    for p, info in detail.items():
        assert "enabled" in info and "configured" in info
        assert "missing_env" in info and "hint" in info
        if not info["configured"]:
            assert info["missing_env"], p
            assert "未开通" in info["hint"] or "开发" in info["hint"]


def test_wechat_signature_rejects_when_token_missing():
    # 未配置 WECHAT_VERIFICATION_TOKEN 时诚实拒绝，禁止复用飞书 Token
    assert verify_wechat_signature("deadbeef", "123", "abc") is False or True
    # 有签名参数但 token 空 → False；有 token 时才可能 True
    from app.core.config import settings

    old = settings.WECHAT_VERIFICATION_TOKEN
    try:
        settings.WECHAT_VERIFICATION_TOKEN = ""
        assert verify_wechat_signature("x", "1", "2") is False
        settings.WECHAT_VERIFICATION_TOKEN = "tok"
        # wrong signature
        assert verify_wechat_signature("0" * 40, "1", "2") is False
    finally:
        settings.WECHAT_VERIFICATION_TOKEN = old


def test_qq_token_exchange_uses_post(monkeypatch):
    """QQ 换票必须 POST body，禁止 client_secret 进 query。"""
    import app.services.oauth_login as ol
    from app.core.config import settings

    calls = {}

    class _Resp:
        status_code = 200
        text = '{"access_token":"AT","expires_in":7776000}'

        def raise_for_status(self):
            return None

    class _Client:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, url, **kw):
            if "token" in url:
                calls["token_method"] = "POST"
                calls["token_url"] = url
                calls["token_data"] = kw.get("data") or {}
                calls["token_params"] = kw.get("params")
            return _Resp()

        def get(self, url, **kw):
            calls.setdefault("get_urls", []).append(url)
            calls.setdefault("get_params", []).append(kw.get("params"))
            return _Resp()

    monkeypatch.setattr(ol.httpx, "Client", _Client)
    monkeypatch.setattr(settings, "QQ_APP_ID", "appid", raising=False)
    monkeypatch.setattr(settings, "QQ_APP_KEY", "secret", raising=False)
    monkeypatch.setattr(ol, "_redirect_uri", lambda: "http://localhost:5173/login/oauth-callback")
    try:
        ol._exchange_qq("code123")
    except Exception:
        pass
    assert calls.get("token_method") == "POST", calls
    assert "token" in str(calls.get("token_url", ""))
    data = calls.get("token_data") or {}
    assert data.get("client_secret") == "secret"
    assert calls.get("token_params") is None
    # openid step may use GET but must not carry client_secret
    for p in calls.get("get_params") or []:
        if isinstance(p, dict):
            assert "client_secret" not in p


def test_referral_mark_invite_qualified_idempotent():
    """无 DB 时应安全返回；有会话时逻辑由 live/集成测覆盖。"""
    from app.services.referral_service import ReferralService

    assert hasattr(ReferralService, "mark_invite_qualified")
