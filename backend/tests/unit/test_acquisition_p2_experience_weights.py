# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P2-1 经验双源统一 + P2-3 模板权重反哺。"""
from __future__ import annotations

from app.api.v1.routes import acquisition as acq_api
from app.services.acquisition import ops_card_store
from app.services.acquisition.template_weights import (
    approved_weights,
    build_template_weight_suggestions,
)
from app.services.evolution.unified_experience import fetch_experience_hints, experience_source_report


class _User:
    id = "u1"
    username = "tester"


def _user() -> _User:
    return _User()


def setup_function():
    ops_card_store._by_inquiry.clear()
    ops_card_store._by_id.clear()


def test_unified_experience_source_label_and_fallback():
    # 无 db：JSON 兜底必须标注 source
    hints = fetch_experience_hints(None, tenant_id="demo", scene_type="find_leads", limit=3)
    for h in hints:
        assert h.get("source") in ("evolution_pg", "json_fallback")
    rep = experience_source_report(None, tenant_id="demo")
    assert rep["primary_source"] == "evolution_pg"
    assert "JSON" in rep["plain_summary"] or "PG" in rep["plain_summary"]


def test_template_weight_suggestions_read_only():
    # 有成交样本 → fulfillment 可能上调或至少出建议
    for i in range(4):
        ops_card_store.materialize(tenant_id="demo", inquiry_id=f"INQ-TW-{i}")
        ops_card_store.record_win(f"INQ-TW-{i}", amount=1000, note="ok", reasons=["交期靠谱"])
    ops_card_store.materialize(tenant_id="demo", inquiry_id="INQ-TW-L1")
    ops_card_store.record_loss("INQ-TW-L1", ["价格高"], note="")

    view = build_template_weight_suggestions(ops_store=ops_card_store, tenant_id="demo", db=None)
    assert view["mode"] == "read_only_suggestions"
    assert view["won"] >= 4
    assert view["lost"] >= 1
    intents = {s["intent"]: s for s in view["suggestions"]}
    assert "fulfillment" in intents and "find_leads" in intents
    for s in view["suggestions"]:
        assert 0.5 <= s["suggested_weight"] <= 1.5
        assert s["requires_human_review"] is True
        assert s["applied"] is False

    resp = acq_api.acquisition_template_weights(tenant_id="demo", current_user=_user(), db=None)
    assert resp["suggestions"]
    assert "approved" in resp


def test_template_weight_human_approve():
    resp = acq_api.acquisition_template_weights_approve(
        acq_api.TemplateWeightApproveRequest(
            intent="fulfillment", weight=1.2, approved_by="owner", tenant_id="demo"
        ),
        current_user=_user(),
    )
    assert resp["approved"]["weight"] == 1.2
    assert resp["approved"]["mode"] == "human_approved"
    aw = approved_weights("demo")
    assert aw["approved"].get("fulfillment", {}).get("weight") == 1.2


def test_experience_source_api():
    resp = acq_api.acquisition_experience_source(tenant_id="demo", current_user=_user(), db=None)
    assert resp["primary_source"] == "evolution_pg"
    assert "plain_summary" in resp
