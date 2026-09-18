# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P3：报价有效期 / 交期门禁 / 退订抑制 / 付款风险闸。"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.api.v1.routes import acquisition as acq_api
from app.services.acquisition import ops_card_store
from app.services.acquisition.payment_risk import payment_risk_gate
from app.services.acquisition.quote_guard import leadtime_gate, quote_validity_view
from app.services.acquisition.suppression_list import SuppressionStore


class _User:
    id = "u1"
    username = "tester"


def _user() -> _User:
    return _User()


def setup_function():
    ops_card_store._by_inquiry.clear()
    ops_card_store._by_id.clear()


def test_quote_validity_expired_and_soon():
    now = datetime.now(timezone.utc)
    past = (now - timedelta(days=20)).isoformat()
    soon = (now - timedelta(days=12)).isoformat()
    v1 = quote_validity_view(quote_at=past, valid_days=14)
    assert v1["expired"] is True
    assert v1["status"] == "expired"
    assert "过期" in v1["plain"]

    v2 = quote_validity_view(quote_at=soon, valid_days=14)
    assert v2["expired"] is False
    assert v2["status"] == "expiring"
    assert v2["days_left"] is not None and v2["days_left"] <= 3

    v3 = quote_validity_view(quote_at="", valid_days=14)
    assert v3["status"] == "unset"


def test_leadtime_gate_blocks_fake_promise():
    g1 = leadtime_gate(promised_days=20, has_inventory_evidence=False, has_capacity_evidence=False)
    assert g1["allowed"] is False
    assert g1["level"] == "blocked"
    assert "禁止" in g1["plain"]

    g2 = leadtime_gate(promised_days=3, has_inventory_evidence=False, has_capacity_evidence=True)
    assert g2["allowed"] is False  # ≤7 无现货

    g3 = leadtime_gate(promised_days=25, has_inventory_evidence=False, has_capacity_evidence=True)
    assert g3["allowed"] is True

    # API
    ops_card_store.materialize(tenant_id="demo", inquiry_id="INQ-Q1")
    resp = acq_api.ops_card_leadtime(
        "INQ-Q1",
        acq_api.LeadtimeRequest(promised_days=5, has_inventory_evidence=False, has_capacity_evidence=False),
        current_user=_user(),
    )
    assert resp["leadtime_gate"]["allowed"] is False


def test_suppression_blocks_outreach():
    store = SuppressionStore()
    r = store.add(email="buyer@example.com", tenant_id="demo", reason="unsubscribe")
    assert r["ok"] is True
    chk = store.check_outreach(email="buyer@example.com", tenant_id="demo", mode="personalized")
    assert chk["allowed"] is False
    assert chk["code"] == "suppressed"
    # 解除需 confirm
    rel = store.remove(email="buyer@example.com", tenant_id="demo", confirm=False)
    assert rel["ok"] is False
    rel2 = store.remove(email="buyer@example.com", tenant_id="demo", confirm=True)
    assert rel2["ok"] is True
    chk2 = store.check_outreach(email="buyer@example.com", tenant_id="demo")
    assert chk2["allowed"] is True

    # API
    acq_api.acquisition_suppression_add(
        acq_api.SuppressionRequest(email="x@y.com", tenant_id="demo", reason="complaint"),
        current_user=_user(),
    )
    rep = acq_api.acquisition_suppression_list(tenant_id="demo", current_user=_user())
    assert rep["total"] >= 1
    allow = acq_api.acquisition_outreach_allow(
        acq_api.OutreachAllowRequest(email="x@y.com", tenant_id="demo"),
        current_user=_user(),
    )
    assert allow["allowed"] is False


def test_payment_risk_blocks_auto_pi():
    # 高风险：D 级 + 高风险国别 + 0 定金
    g = payment_risk_gate(
        country="NG",
        buyer_type="new",
        buyer_grade="D",
        deposit_ratio=0,
        auto_pi=True,
    )
    assert g["auto_pi_allowed"] is False
    assert g["auto_pi_blocked"] is True
    assert g["level"] == "high"
    assert "禁止自动" in g["plain"] or "已阻断" in g["plain"]

    # 低风险：A 级 + 高定金
    g2 = payment_risk_gate(
        country="DE",
        buyer_type="distributor",
        buyer_grade="A",
        deposit_ratio=0.4,
        auto_pi=True,
    )
    assert g2["auto_pi_allowed"] is True
    assert g2["level"] == "low"

    # API
    resp = acq_api.acquisition_payment_risk(
        acq_api.PaymentRiskRequest(country="IN", buyer_type="new", auto_pi=True, deposit_ratio=0),
        current_user=_user(),
    )
    assert resp["auto_pi_allowed"] in (True, False)
    assert resp["reasons"] is not None
    assert "hint" in resp


def test_quote_validity_api_and_ops_payload():
    ops_card_store.materialize(tenant_id="demo", inquiry_id="INQ-Q2")
    now = datetime.now(timezone.utc).isoformat()
    resp = acq_api.ops_card_quote_validity(
        "INQ-Q2",
        acq_api.QuoteValidityRequest(quote_at=now, valid_days=14, fx_locked=True, fx_note="锁 7.2"),
        current_user=_user(),
    )
    assert resp["quote_validity"]["fx_locked"] is True
    assert resp["quote_validity"]["status"] == "valid"
    assert "quote_validity" in resp and "leadtime_gate" in resp and "payment_risk" in resp
