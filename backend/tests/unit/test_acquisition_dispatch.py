# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""compose-next#3：作战台一键派发。"""
from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

from app.api.v1.routes import acquisition as acq_api
from app.services.acquisition import ops_card_store
from app.services.acquisition.dispatch_service import dispatch_acquisition
from app.services.hermes import planner_service as ps


REGISTERED = {
    "accio", "lead", "inquiry", "order", "goodjob_crm", "billing",
    "logistics", "deerflow", "trade_ai_agent", "site_builder", "content",
    "publish", "nurture", "egress",
}


def _patch_planner(monkeypatch):
    monkeypatch.setattr(ps, "_registered_executors", lambda: set(REGISTERED))
    caps = set(ps.FALLBACK_CAPABILITIES) | {
        "lead.search", "lead.score", "prospect.enrich", "outreach.letter",
        "billing.meter", "inquiry.capture", "order.create",
        "document.generate_pi", "crm.sync_stage",
        "document.generate_trade_docs", "logistics.track", "default",
    }
    monkeypatch.setattr(ps, "known_capabilities", lambda: frozenset(caps))
    monkeypatch.setattr(ps, "_recall_skills", lambda *a, **k: [])
    monkeypatch.setattr(ps, "_enrich_with_experience", lambda e, d: dict(e.payload or {}))


def test_dispatch_preview_only(monkeypatch):
    _patch_planner(monkeypatch)
    async def _run():
        return await dispatch_acquisition(
            None,
            tenant_id="t1",
            intent="find_leads",
            payload={"keyword": "rockwool", "country": "IN"},
            auto_dispatch=False,
        )
    r = asyncio.new_event_loop().run_until_complete(_run())
    assert r["graph_source"] in ("L1_template", "L1_hybrid", "L2_llm", "L3_minimal")
    assert r["node_count"] >= 1
    assert r["dispatched"] is False
    assert "preview" in r["persistence_note"] or "未派发" in r["persistence_note"] or "auto_dispatch=false" in r["persistence_note"]


def test_dispatch_auto_without_db(monkeypatch):
    _patch_planner(monkeypatch)
    async def _run():
        return await dispatch_acquisition(
            None,
            tenant_id="t1",
            intent="find_leads",
            payload={"keyword": "x", "country": "SA"},
            auto_dispatch=True,
        )
    r = asyncio.new_event_loop().run_until_complete(_run())
    assert r["dispatched"] is False
    assert r["dispatch_error"] or r["persistence_note"]


def test_api_dispatch_endpoint_preview(monkeypatch):
    _patch_planner(monkeypatch)
    ops_card_store._by_id.clear()
    ops_card_store._by_inquiry.clear()
    body = acq_api.DispatchRequest(
        intent="find_leads",
        tenant_id="t1",
        payload={"keyword": "rockwool", "country": "SA"},
        inquiry_id="INQ-D-1",
        auto_dispatch=False,
    )
    resp = asyncio.new_event_loop().run_until_complete(
        acq_api.acquisition_dispatch(body, current_user=None, db=None)
    )
    assert resp.plan_id
    assert resp.nodes
    assert resp.dispatched is False
    assert resp.card is not None
    card = ops_card_store.get_by_inquiry("INQ-D-1")
    assert card is not None
    assert card.stage == "orchestrated"
    assert resp.experience is not None


def test_api_dispatch_requires_intent():
    body = acq_api.DispatchRequest(intent="", tenant_id="t1")
    try:
        asyncio.new_event_loop().run_until_complete(
            acq_api.acquisition_dispatch(body, current_user=None, db=None)
        )
        raise AssertionError("should 400")
    except Exception as e:
        assert "intent" in str(e).lower() or "400" in str(e)
