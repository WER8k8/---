# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P0：钱包真余额 / 渠道红标 / 翻译钩子。"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from app.api.v1.routes import acquisition as acq_api
from app.services.acquisition.translate_service import translate_text
from app.services.acquisition.wallet_guard import check_wallet_status


def test_wallet_unknown_without_db():
    r = check_wallet_status("t1", db=None)
    assert r["status"] == "unknown"
    assert r["token_balance"] is None
    assert r["hard_block_enabled"] is False


def test_wallet_reads_ledger_balance(monkeypatch):
    monkeypatch.setenv("ACQ_HARD_BLOCK_TOKEN", "false")
    db = MagicMock()

    class _Q:
        def filter(self, *a, **k):
            return self
        def all(self):
            return [SimpleNamespace(balance_after=1200, created_at="2026-09-18T00:00:00+00:00")]
        def first(self):
            return SimpleNamespace(balance_after=1200, created_at="2026-09-18T00:00:00+00:00")
        def order_by(self, *a, **k):
            return self
    db.query = MagicMock(return_value=_Q())
    import sys
    sys.modules["app.models.token_ledger"] = SimpleNamespace(
        TokenLedgerEntry=SimpleNamespace(tenant_id="x", balance_after=1, created_at="t")
    )
    r = check_wallet_status("tenant-1", db=db)
    assert r["token_balance"] == 1200
    assert r["source"] == "token_ledger"
    assert r["hard_block_enabled"] is False


def test_wallet_hard_block_when_zero(monkeypatch):
    monkeypatch.setenv("ACQ_HARD_BLOCK_TOKEN", "true")
    db = MagicMock()

    class _Q:
        def filter(self, *a, **k):
            return self
        def all(self):
            return [SimpleNamespace(balance_after=0, created_at="2026-09-18T01:00:00+00:00")]
        def first(self):
            return SimpleNamespace(balance_after=0)
        def order_by(self, *a, **k):
            return self
    db.query = MagicMock(return_value=_Q())
    import sys
    sys.modules["app.models.token_ledger"] = SimpleNamespace(
        TokenLedgerEntry=SimpleNamespace(tenant_id="x", balance_after=1, created_at="t")
    )
    r = check_wallet_status("t-zero", db=db)
    assert r["token_balance"] == 0
    assert r["hard_block_enabled"] is True
    assert r["status"] == "blocked"


def test_translate_still_degrades_without_engine(monkeypatch):
    monkeypatch.delenv("LIBRETRANSLATE_URL", raising=False)
    r = translate_text("Hello buyer", "en", "zh")
    assert r["degraded"] is True
    assert r["translated"] == "Hello buyer"


def test_channels_api_returns_shape():
    r = acq_api.acquisition_channels(current_user=None)
    assert "channels" in r
    # 无论有无 key，结构应存在；mock_count 可为 0
    if r.get("channels"):
        assert all("status" in c and "is_mock" in c for c in r["channels"])
    assert "hint" in r or r.get("error")


def test_wallet_status_route_with_db_none():
    r = acq_api.acquisition_wallet_status(tenant_id="demo", current_user=None, db=None)
    assert r["status"] in ("unknown", "ok", "empty", "blocked")
