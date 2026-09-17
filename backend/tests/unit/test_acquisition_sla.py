# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""获客跟进 SLA / 今日待办。"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.api.v1.routes import acquisition as acq_api
from app.services.acquisition import ops_card_store
from app.services.acquisition.sla import card_sla, default_next_action_at, evaluate_sla


def test_sla_overdue_when_past_due():
    now = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)
    s = evaluate_sla(stage="engaged", next_action="回电", next_action_at="2026-09-18T08:00:00+00:00", now=now)
    assert s["sla"] == "overdue"
    assert s["overdue"] is True


def test_sla_due_soon():
    now = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)
    due = (now + timedelta(hours=3)).isoformat()
    s = evaluate_sla(stage="engaged", next_action="回电", next_action_at=due, now=now)
    assert s["sla"] == "due"
    assert s["overdue"] is False


def test_sla_lost_closed():
    s = evaluate_sla(stage="lost", next_action="x", now=datetime.now(timezone.utc))
    assert s["sla"] == "closed"


def test_sla_estimates_from_last_touch():
    now = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)
    touch = (now - timedelta(hours=2)).isoformat()
    s = evaluate_sla(stage="engaged", next_action="跟进", last_touch_at=touch, now=now)
    assert s["sla"] == "due"
    assert s["due_at"]


def test_reply_ingest_sets_next_action_at_and_sla():
    ops_card_store._by_id.clear()
    ops_card_store._by_inquiry.clear()
    body = acq_api.ReplyIngestRequest(
        tenant_id="t1",
        inquiry_id="INQ-SLA-1",
        message="请报价 quote",
        country="SA",
        grade=70,
        contact_name="Ahmed",
    )
    resp = acq_api.reply_ingest(body, current_user=None, db=None)
    assert resp["intent_analysis"]["intent"] in ("request_quote", "price_haggling", "generic_interest", "unknown")
    assert resp["sla"] is not None
    assert resp["card"]["next_action_at"]
    card = ops_card_store.get_by_inquiry("INQ-SLA-1")
    sla = card_sla(card)
    assert sla["sla"] in ("due", "overdue", "none")


def test_followups_api_orders_overdue_first():
    ops_card_store._by_id.clear()
    ops_card_store._by_inquiry.clear()
    now = datetime.now(timezone.utc)
    ops_card_store.materialize(tenant_id="demo", inquiry_id="INQ-LATE", stage="engaged")
    ops_card_store.record_touch(
        "INQ-LATE", channel="manual", summary="超期",
        next_action="立刻联系", next_action_at=(now - timedelta(hours=5)).isoformat(),
    )
    ops_card_store.materialize(tenant_id="demo", inquiry_id="INQ-SOON", stage="engaged")
    ops_card_store.record_touch(
        "INQ-SOON", channel="manual", summary="将到期",
        next_action="稍后跟进", next_action_at=(now + timedelta(hours=2)).isoformat(),
    )
    ops_card_store.materialize(tenant_id="demo", inquiry_id="INQ-LOSTX", stage="lost")
    r = acq_api.acquisition_followups(tenant_id="demo", include_lost=False, current_user=None)
    ids = [i["inquiry_id"] for i in r["items"]]
    assert "INQ-LATE" in ids
    assert "INQ-LOSTX" not in ids
    assert ids[0] == "INQ-LATE"
    assert r["overdue_count"] >= 1
    assert default_next_action_at(now=now)


def test_mint_and_login_untouched():
    from pathlib import Path
    wt = Path(__file__).resolve().parents[3]
    ui = (wt / "frontend/admin/src/stores/uiPreferences.ts").read_text(encoding="utf-8")
    assert "#4a9b8c" in ui
    assert (wt / "frontend/admin/src/views/login/index.vue").exists()
    menus = (wt / "frontend/admin/src/constants/proShellMenus.ts").read_text(encoding="utf-8")
    assert "acquisition-ops" in menus
