# -*- coding: utf-8 -*-
"""P1-1 翻译真源接线契约测试（不连真网络）。"""
from __future__ import annotations

import httpx

from app.core.config import settings
from app.services.acquisition import translate_service


def test_llm_unconfigured_returns_none(monkeypatch):
    monkeypatch.setattr(settings, "TRANSLATE_API_BASE_URL", "")
    monkeypatch.setattr(settings, "TRANSLATE_API_KEY", None)
    assert translate_service._try_llm_translate("hi", "en", "zh") is None


def test_llm_configured_translates(monkeypatch):
    monkeypatch.setattr(settings, "TRANSLATE_API_BASE_URL", "https://fake.test/v1")
    monkeypatch.setattr(settings, "TRANSLATE_API_KEY", "test-key")
    monkeypatch.setattr(settings, "TRANSLATE_MODEL", "M1")
    calls: dict = {}

    class FakeResp:
        status_code = 200
        text = ""

        @staticmethod
        def json():
            return {"choices": [{"message": {"content": "  Bonjour  "}}]}

    def fake_post(self_, url, **kw):
        calls["payload"] = kw.get("json")
        return FakeResp()

    monkeypatch.setattr(httpx.Client, "post", fake_post)
    out = translate_service._try_llm_translate("hi", "en", "fr")
    assert out is not None
    assert out["translated"] == "Bonjour"  # 外层引号壳被剥
    assert out["provider"] == "llm:M1"
    assert isinstance(out["mock"], bool) and not out["mock"]
    assert out["machine_translated"] is True
    assert calls["payload"]["model"] == "M1"


def test_unconfigured_translate_text_is_identity_degraded(monkeypatch):
    monkeypatch.setattr(translate_service, "_try_external_translate", lambda *a, **k: None)
    out = translate_service.translate_text("中文统计", "auto", "en")
    assert out["degraded"] is True
    assert out["provider"] == "identity"
    assert out["translated"] == "中文统计"


def test_configured_translate_text_removes_degraded(monkeypatch):
    monkeypatch.setattr(
        translate_service,
        "_try_external_translate",
        lambda *a, **k: {
            "translated": "English translation",
            "provider": "llm:Atria-Dawn-Preview",
            "mock": False,
            "machine_translated": True,
        },
    )
    out = translate_service.translate_text("中文", "auto", "en")
    assert out["degraded"] is False
    assert out["provider"].startswith("llm:")
    assert out["translated"] == "English translation"


def test_same_lang_identity_not_degraded():
    out = translate_service.translate_text("hello", "en", "en")
    assert out["degraded"] is False
    assert out["provider"] == "identity"