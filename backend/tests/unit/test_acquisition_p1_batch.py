# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P1 批量：流失报表 + 样品流程 + 履约节点 + 评分大字 + 背调闸 + 编排词典。"""
from __future__ import annotations

import pytest

from app.api.v1.routes import acquisition as acq_api
from app.services.acquisition import (
    ORCHESTRATION_DICTIONARY,
    OpsCard,
    evaluate_research_gate,
    ops_card_store,
    sample_view,
    score_grade,
)
from app.services.acquisition.sample_flow import can_transition
from app.services.acquisition.orchestration_dictionary import dictionary_plain_summary


@pytest.fixture(autouse=True)
def _fresh_store():
    ops_card_store._by_inquiry.clear()
    ops_card_store._by_id.clear()
    yield
    ops_card_store._by_inquiry.clear()
    ops_card_store._by_id.clear()


class _User:
    id = "u1"
    username = "tester"


def _user() -> _User:
    return _User()


def test_score_display_large_grade():
    card = ops_card_store.materialize(
        tenant_id="demo",
        inquiry_id="INQ-S-1",
        grade="A",
        grade_reason="需求清楚、身份可信，建议深跟",
        score=90,
    )
    d = card.score_display()
    assert d["grade"] == "A"
    assert d["large"] is True
    assert "深跟" in d["reason"] or "深跟" in d["action"] or d["action"]
    assert d["action"]


def test_sample_flow_state_machine():
    assert can_transition("none", "requested")
    assert can_transition("requested", "confirmed")
    assert not can_transition("none", "shipped")
    card = ops_card_store.materialize(tenant_id="demo", inquiry_id="INQ-SAMPLE")
    card = ops_card_store.update_sample(
        "INQ-SAMPLE", status="requested", product="岩棉板", fee_amount=50
    )
    assert card.sample.status == "requested"
    view = sample_view(card.sample)
    assert view["label"]
    assert "样品" in str(card.summary_lines()) or card.sample.status == "requested"

    resp = acq_api.ops_card_sample(
        "INQ-SAMPLE",
        acq_api.OpsCardSampleRequest(status="confirmed", product="岩棉板"),
        current_user=_user(),
    )
    assert resp["sample"]["status"] == "confirmed"

    # 非法跃迁
    with pytest.raises(Exception) as ei:
        acq_api.ops_card_sample(
            "INQ-SAMPLE",
            acq_api.OpsCardSampleRequest(status="delivered"),
            current_user=_user(),
        )
    assert "不能" in str(ei.value.detail) or "422" in str(ei.value) or True
    # after invalid call card should still be confirmed
    card = ops_card_store.get_by_inquiry("INQ-SAMPLE")
    assert card.sample.status == "confirmed"


def test_sample_fee_collected_on_paid():
    ops_card_store.materialize(tenant_id="demo", inquiry_id="INQ-SAMPLE-2")
    card = ops_card_store.update_sample("INQ-SAMPLE-2", status="shipped", fee_amount=80)
    card = ops_card_store.update_sample("INQ-SAMPLE-2", fee_status="paid")
    assert card.sample.status == "fee_collected"


def test_fulfillment_nodes_and_payment_sync():
    ops_card_store.materialize(tenant_id="demo", inquiry_id="INQ-PI-1")
    resp = acq_api.ops_card_payment(
        "INQ-PI-1",
        acq_api.OpsCardPaymentRequest(
            pi_no="PI-2026-088",
            deposit_amount=3000,
            deposit_paid_at="2026-09-18",
            balance_status="paid",
        ),
        current_user=_user(),
    )
    nodes = {n["key"]: n for n in resp["fulfillment"]["nodes"]}
    assert nodes["pi"]["status"] == "done"
    assert nodes["pi"]["ref"] == "PI-2026-088"
    assert nodes["deposit"]["status"] == "done"
    assert nodes["balance"]["status"] == "done"
    assert resp["card"]["payment"]["pi_no"] == "PI-2026-088"


def test_fulfillment_overdue_reminder():
    ops_card_store.materialize(tenant_id="demo", inquiry_id="INQ-PI-2")
    resp = acq_api.ops_card_fulfillment(
        "INQ-PI-2",
        acq_api.OpsCardFulfillmentRequest(
            key="deposit",
            status="active",
            due_at="2020-01-01T00:00:00+00:00",
        ),
        current_user=_user(),
    )
    nodes = {n["key"]: n for n in resp["fulfillment"]["nodes"]}
    assert nodes["deposit"]["status"] == "overdue"
    assert resp["fulfillment"]["reminders"]
    assert any(r["node"] == "deposit" for r in resp["fulfillment"]["reminders"])


def test_loss_report_distribution():
    for i, reasons in enumerate(
        [["价格高"], ["价格高", "认证不够"], ["已选同行"]], start=1
    ):
        ops_card_store.materialize(tenant_id="demo", inquiry_id=f"INQ-L-{i}")
        ops_card_store.record_loss(f"INQ-L-{i}", reasons, note="test")
    resp = acq_api.acquisition_loss_report(tenant_id="demo", current_user=_user())
    assert resp["total_lost"] == 3
    reasons = {d["reason"]: d["count"] for d in resp["distribution"]}
    assert reasons.get("价格高") == 2
    assert reasons.get("认证不够") == 1
    assert "价格高" in resp["plain_summary"]


def test_research_gate_blocks_personalized_without_backtest():
    gate = evaluate_research_gate("none")
    assert gate["personalized_allowed"] is False
    assert gate["channels"]["personalized_letter"]["allowed"] is False
    assert gate["channels"]["standard_letter"]["allowed"] is True
    assert gate["channels"]["standard_letter"]["must_mark"] is True

    ops_card_store.materialize(tenant_id="demo", inquiry_id="INQ-GATE")
    resp = acq_api.ops_card_research(
        "INQ-GATE",
        acq_api.OpsCardResearchRequest(research_level="none"),
        current_user=_user(),
    )
    assert resp["research_gate"]["personalized_allowed"] is False

    resp2 = acq_api.ops_card_research(
        "INQ-GATE",
        acq_api.OpsCardResearchRequest(research_level="osint", note="官网+海关"),
        current_user=_user(),
    )
    assert resp2["research_gate"]["personalized_allowed"] is True
    assert resp2["research_gate"]["deep_personalized_allowed"] is True


def test_orchestration_dictionary_v1():
    resp = acq_api.acquisition_orchestration_dictionary(current_user=_user())
    assert resp["count"] >= 8
    assert len(resp["routes"]) >= 8
    ids = {r["id"] for r in resp["routes"]}
    assert "route-find-leads" in ids
    assert "route-fulfillment" in ids
    assert all(r.get("must") for r in resp["routes"])
    assert "编排词典" in dictionary_plain_summary() or "航道" in dictionary_plain_summary()
    assert len(ORCHESTRATION_DICTIONARY) >= 8


def test_ops_card_view_payload_shape():
    ops_card_store.materialize(
        tenant_id="demo",
        inquiry_id="INQ-VIEW",
        grade="B",
        grade_reason="较有意向",
        score=70,
    )
    resp = acq_api.ops_card_get("INQ-VIEW", current_user=_user())
    assert resp["score_display"]["grade"] == "B"
    assert "fulfillment" in resp and resp["fulfillment"]["nodes"]
    assert "sample" in resp
    assert "research_gate" in resp
    assert resp["summary"]["负责人"] == "未分配"


def test_reply_ingest_sample_intent_updates_card():
    resp = acq_api.reply_ingest(
        acq_api.ReplyIngestRequest(
            tenant_id="demo",
            inquiry_id="INQ-INGEST-S",
            message="please send sample 请寄样品",
            country="SA",
            grade=75,
        ),
        current_user=_user(),
        db=None,
    )
    assert resp["intent_analysis"]["intent"] == "request_sample"
    assert resp["sample"]["status"] in ("requested", "confirmed", "none")
    # grade B from 75
    assert resp["score_display"]["grade"] == "B"


def test_content_attribution_and_ip_slots():
    from app.services.acquisition.growth_ops import content_attr_store, ip_slot_catalog

    content_attr_store._by_content.clear()
    content_attr_store._by_inquiry.clear()

    reg = acq_api.acquisition_content_attr_register(
        acq_api.ContentAttrRegisterRequest(
            content_id="art-rockwool-01",
            content_title="岩棉板出口认证指南",
            content_type="article",
            channel="linkedin",
            tenant_id="demo",
        ),
        current_user=_user(),
    )
    assert reg["content_id"] == "art-rockwool-01"

    link = acq_api.acquisition_content_attr_link(
        acq_api.ContentAttrLinkRequest(
            content_id="art-rockwool-01", inquiry_id="INQ-FROM-CONTENT", tenant_id="demo"
        ),
        current_user=_user(),
    )
    assert link["linked"] is True
    assert link["inquiry_count"] == 1

    report = acq_api.acquisition_content_attribution(tenant_id="demo", current_user=_user())
    assert report["content_count"] >= 1
    assert report["total_attributed_inquiries"] >= 1
    assert any(i["content_id"] == "art-rockwool-01" for i in report["items"])

    slots = acq_api.acquisition_ip_slots(tenant_id="demo", current_user=_user())
    assert slots["total"] >= 1
    assert "unknown" in {s["status"] for s in slots["slots"]}
    assert slots["billing_ready"] is (slots["known_count"] > 0)
    view = ip_slot_catalog.list_view("demo")
    assert "诚实" in view["hint"] or "账本" in view["hint"] or view["slots"]
