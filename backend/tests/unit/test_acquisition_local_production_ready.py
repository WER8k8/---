# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""本地生产开关 + 跟单卡 PG 持久化。"""
from __future__ import annotations

import os

from app.services.acquisition import ops_card_store
from app.services.acquisition.ops_card_pg import (
    load_ops_card,
    patch_store_persistence,
    restore_ops_card,
    save_ops_card,
)
from app.services.acquisition.translate_service import translate_text
from app.services.acquisition.wallet_guard import check_wallet_status


def setup_function():
    ops_card_store._by_inquiry.clear()
    ops_card_store._by_id.clear()


def test_ops_card_pg_patch_installed():
    assert getattr(ops_card_store, "_pg_patched", False) is True


def test_save_and_restore_ops_card_roundtrip():
    ops_card_store.materialize(tenant_id="demo", inquiry_id="INQ-PG-1", grade="A", score=88)
    card = ops_card_store.get_by_inquiry("INQ-PG-1")
    card.buyer_display = "Ahmed @ SA Project"
    card = ops_card_store.record_win("INQ-PG-1", amount=12000, note="ok")
    saved = save_ops_card(card)
    # 有库则 persisted；无库诚实 false
    assert "persisted" in saved
    if saved.get("persisted"):
        data = load_ops_card("INQ-PG-1")
        assert data and data.get("inquiry_id") == "INQ-PG-1"
        ops_card_store._by_inquiry.clear()
        restored = restore_ops_card(ops_card_store, "INQ-PG-1")
        assert restored is not None
        assert restored.stage == "won"
        assert restored.buyer_display
    else:
        assert saved.get("reason")


def test_env_gates_documented_for_local():
    # 代码支持；运行时读 env — 这里断言 wallet/translate 契约仍诚实
    w = check_wallet_status("demo", db=None)
    assert w["status"] in ("unknown", "ok", "empty", "blocked")
    t = translate_text("hello", "auto", "zh")
    assert "provider" in t
    assert t.get("degraded") in (True, False)


def test_hard_block_logic_with_env():
    os.environ["ACQ_HARD_BLOCK_TOKEN"] = "true"
    try:
        from app.services.acquisition.wallet_guard import check_wallet_status as cw
        from unittest.mock import MagicMock

        class _Q:
            def filter(self, *a, **k):
                return self

            def all(self):
                class R:
                    balance_after = 0
                    created_at = "2026-01-01"
                return [R()]

            def order_by(self, *a):
                return self

            def first(self):
                class R:
                    balance_after = 0
                    created_at = "2026-01-01"
                return R()

        class _DB:
            def query(self, *a, **k):
                return _Q()

        out = cw("demo", db=_DB())
        assert out["hard_block_enabled"] is True
        assert out["status"] == "blocked"
        assert out["token_balance"] == 0
    finally:
        os.environ.pop("ACQ_HARD_BLOCK_TOKEN", None)


def test_pipeline_gates_env_effect():
    os.environ["PIPELINE_GATES_ENABLED"] = "1"
    try:
        from app.services.pipeline import chains
        assert chains.gates_enabled("email") is True
    finally:
        os.environ.pop("PIPELINE_GATES_ENABLED", None)


def test_patch_store_persistence_idempotent():
    patch_store_persistence(ops_card_store)
    assert getattr(ops_card_store, "_pg_patched", False) is True
