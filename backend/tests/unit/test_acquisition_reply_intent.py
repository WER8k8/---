# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""compose-next#4：回复意图判断。"""
from __future__ import annotations

from app.api.v1.routes import acquisition as acq_api
from app.services.acquisition import ops_card_store
from app.services.acquisition.intent_classifier import classify_reply


def test_classify_price():
    r = classify_reply("你们价格太贵了，能便宜点吗 quote price")
    assert r["intent"] in ("price_haggling", "request_quote")
    assert r["next_action"]


def test_classify_sample():
    r = classify_reply("请寄样品 sample")
    assert r["intent"] == "request_sample"
    assert r["stage_suggestion"] == "sampling"


def test_classify_payment():
    r = classify_reply("定金 T/T 30% 可以吗 payment deposit")
    assert r["intent"] == "payment_discuss"
    assert r["stage_suggestion"] == "negotiating"


def test_classify_reject():
    r = classify_reply("已从别家订了 already ordered")
    assert r["intent"] == "reject_competitor"
    assert r["stage_suggestion"] == "lost_risk"


def test_classify_unknown_honest():
    r = classify_reply("asdfgh 12345")
    assert r["intent"] == "unknown"
    assert "资格" in r["next_action"] or "24h" in r["next_action"]


def test_reply_ingest_includes_intent_analysis():
    ops_card_store._by_id.clear()
    ops_card_store._by_inquiry.clear()
    body = acq_api.ReplyIngestRequest(
        tenant_id="t1",
        inquiry_id="INQ-INT-1",
        message="请寄样品并说明运费 sample",
        country="SA",
        grade=70,
        contact_name="Ahmed",
    )
    resp = acq_api.reply_ingest(body, current_user=None, db=None)
    assert "intent_analysis" in resp
    assert resp["intent_analysis"]["intent"] == "request_sample"
    card = ops_card_store.get_by_inquiry("INQ-INT-1")
    assert card is not None
    assert card.stage == "sampling"
    assert "样品" in (card.next_action or "") or "sample" in (card.next_action or "").lower()
    assert any("样品" in t or "sample" in t.lower() for t in (card.playbook_tips or []))


def test_lost_not_overwritten_by_price():
    ops_card_store._by_id.clear()
    ops_card_store._by_inquiry.clear()
    ops_card_store.materialize(tenant_id="t1", inquiry_id="INQ-LOST-1", stage="lost")
    ops_card_store.record_loss("INQ-LOST-1", reasons=["已选同行"])
    body = acq_api.ReplyIngestRequest(
        tenant_id="t1",
        inquiry_id="INQ-LOST-1",
        message="价格太贵了 price",
        country="IN",
    )
    resp = acq_api.reply_ingest(body, current_user=None, db=None)
    assert resp["card"]["stage"] == "lost"
