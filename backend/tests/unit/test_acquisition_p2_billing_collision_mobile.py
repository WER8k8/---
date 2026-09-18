# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P2-5/6/7/8/10 + 撞单/账单/旺财/NPS/手机待办。"""
from __future__ import annotations

from app.api.v1.routes import acquisition as acq_api
from app.services.acquisition import ops_card_store
from app.services.acquisition.billing_explain import billing_explain
from app.services.acquisition.nps_rescue import nps_and_rescue_brief
from app.services.acquisition.onboarding import build_onboarding
from app.services.acquisition.sales_collision import claim_inquiry, collision_report
from app.services.acquisition.wangcai_line_b import rescue_plan


class _User:
    id = "u1"
    username = "tester"


def _user() -> _User:
    return _User()


def setup_function():
    ops_card_store._by_inquiry.clear()
    ops_card_store._by_id.clear()
    from app.services.acquisition.wangcai_line_b import _recent
    _recent.clear()


def test_billing_explain_empty_honest():
    resp = acq_api.acquisition_billing_explain(tenant_id="demo", current_user=_user(), db=None)
    assert resp["balance"] is None
    assert "诚实" in resp["plain_summary"] or "无" in resp["plain_summary"]
    out = billing_explain(None, tenant_id="demo")
    assert out["items"] == []


def test_collision_claim_and_force_handoff():
    ops_card_store.materialize(tenant_id="demo", inquiry_id="INQ-C1", owner_user_id="alice")
    # 有主：无 confirm 应被拒
    r1 = claim_inquiry(
        ops_card_store,
        inquiry_id="INQ-C1",
        user_id="bob",
        tenant_id="demo",
        confirm_force=False,
        note="想接",
    )
    assert r1["ok"] is False
    assert r1.get("code") in ("collision", "need_confirm", "owned_by_other")
    # confirm 交接
    r2 = claim_inquiry(
        ops_card_store,
        inquiry_id="INQ-C1",
        user_id="bob",
        tenant_id="demo",
        confirm_force=True,
        note="老板确认交接",
    )
    assert r2["ok"] is True
    card = ops_card_store.get_by_inquiry("INQ-C1")
    assert card.owner_user_id == "bob"
    assert card.handoff_history
    rep = collision_report(ops_card_store, tenant_id="demo")
    assert rep["total"] >= 1
    assert "认领" in rep["rule"] or "交接" in rep["rule"]
    api_rep = acq_api.acquisition_collision_report(tenant_id="demo", current_user=_user())
    assert api_rep["plain_summary"] is not None


def test_wangcai_rescue_no_block_then_with_blocker_and_cooldown():
    # 无库：无卡壳
    view = rescue_plan(tenant_id="demo", db=None)
    assert view["blocked"] is False
    assert "无需补救" in view["plain_summary"] or view["blockers"] == []

    blockers = [{
        "task_id": "t1",
        "task_type": "site_builder",
        "status": "failed",
        "error": "site publish timeout",
    }]
    v1 = rescue_plan(tenant_id="demo", blockers=blockers)
    assert v1["blocked"] is True
    assert v1["allow_dispatch"] is True
    assert v1["repeated"] is False
    assert v1["suggested_intent"]
    # 冷却窗内重复 → repeated
    v2 = rescue_plan(tenant_id="demo", blockers=blockers)
    assert v2["repeated"] is True
    assert v2["allow_dispatch"] is False
    # API
    api = acq_api.acquisition_wangcai_rescue(tenant_id="demo", current_user=_user(), db=None)
    assert "plain_summary" in api


def test_nps_rescue_low_usage_actions():
    ops_card_store.materialize(tenant_id="demo", inquiry_id="INQ-N1")
    view = nps_and_rescue_brief(
        tenant_id="demo",
        ops_store=ops_card_store,
        onboarding_view=build_onboarding("demo", ops_store=None, has_dispatch=False),
        nps_score=None,
    )
    assert view["nps"]["collected"] is False
    assert "尚未收集" in view["nps"]["plain"]
    assert view["rescue_actions"]
    assert view["should_notify"] is True  # 使用度低

    view2 = nps_and_rescue_brief(
        tenant_id="demo",
        ops_store=None,
        nps_score=3,
    )
    assert view2["nps"]["bucket"] == "detractor"
    assert view2["should_notify"] is True

    view3 = nps_and_rescue_brief(tenant_id="demo", ops_store=None, nps_score=10)
    assert view3["nps"]["bucket"] == "promoter"
    assert view3["nps"]["score"] == 10


def test_nps_api_endpoint():
    ops_card_store.materialize(tenant_id="demo", inquiry_id="INQ-N2")
    resp = acq_api.acquisition_nps_rescue(tenant_id="demo", current_user=_user(), db=None)
    assert "nps" in resp and "rescue_actions" in resp
    assert "plain_summary" in resp
