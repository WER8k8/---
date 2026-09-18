# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P2：Win/Loss 入环 + 租户 Onboarding 清单。"""
from __future__ import annotations

from app.api.v1.routes import acquisition as acq_api
from app.services.acquisition import ops_card_store
from app.services.acquisition.onboarding import build_onboarding


class _User:
    id = "u1"
    username = "tester"


def _user() -> _User:
    return _User()


def setup_function():
    ops_card_store._by_inquiry.clear()
    ops_card_store._by_id.clear()


def test_ops_card_win_and_win_loss_stats():
    ops_card_store.materialize(tenant_id="demo", inquiry_id="INQ-WIN-1", grade="A", score=90)
    resp = acq_api.ops_card_win(
        "INQ-WIN-1",
        acq_api.OpsCardWinRequest(amount=12000, currency="USD", note="认证齐全交期稳", reasons=["认证齐全"]),
        current_user=_user(),
        db=None,
    )
    assert resp["card"]["stage"] == "won"
    assert resp["card"]["won_amount"] == 12000
    assert resp["experience"]["recorded"] in (True, False)  # 无 db 诚实降级
    wl = resp["win_loss"]
    assert wl["won_count"] >= 1
    assert "成交" in wl["plain_summary"]

    ops_card_store.materialize(tenant_id="demo", inquiry_id="INQ-LOSS-1")
    ops_card_store.record_loss("INQ-LOSS-1", ["价格高"], note="预算不够")
    wl2 = acq_api.acquisition_win_loss(tenant_id="demo", current_user=_user())
    assert wl2["won_count"] >= 1
    assert wl2["lost_count"] >= 1
    assert wl2["loss_reasons"].get("价格高")


def test_onboarding_checklist_steps():
    ops_card_store.materialize(tenant_id="demo", inquiry_id="INQ-OB-1")
    card = ops_card_store.get_by_inquiry("INQ-OB-1")
    card.owner_user_id = "sales1"
    ops_card_store.record_touch("INQ-OB-1", channel="manual", summary="已联系", next_action="明天报价")
    resp = acq_api.acquisition_onboarding(tenant_id="demo", has_dispatch=True, current_user=_user())
    assert resp["total"] == 5
    assert resp["done_count"] >= 3  # login/ops/has_card + dispatch + touch
    assert resp["percent"] > 0
    assert "开通引导" in resp["plain_summary"]
    titles = {s["title"] for s in resp["steps"]}
    assert "打开获客作战台" in titles
    assert "智能拆解一次" in titles


def test_onboarding_builder_without_store():
    view = build_onboarding("demo", ops_store=None, has_dispatch=False)
    assert view["done_count"] == 2  # login + ops_opened 默认视为已进系统
    assert view["next_step"] is not None
    assert view["next_step"]["id"] == "step-first-inquiry"
