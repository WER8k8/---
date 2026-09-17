# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""获客服务层单元测试：身份锁 / 跟单卡 / Playbook / 评分。"""
from __future__ import annotations

from app.services.acquisition import (
    BuyerMaster,
    BuyerMasterStore,
    OpsCardStore,
    PlaybookEntry,
    PlaybookStore,
    score_grade,
)


# ── Buyer Master 身份锁 ─────────────────────────────────────

def test_buyer_master_display_identity():
    b = BuyerMaster(
        contact_name="Ahmed",
        contact_gender="male",
        contact_title="Purchasing Manager",
        company_name="Gulf Insulation",
    )
    assert "Ahmed" in b.display_identity()
    assert "Gulf Insulation" in b.display_identity()
    assert b.persona_locked is True


def test_identity_lock_blocks_gender_change():
    store = BuyerMasterStore()
    b1 = BuyerMaster(tenant_id="t1", email="a@x.com", contact_name="Ahmed", contact_gender="male")
    store.upsert(b1)
    # 同邮箱换人设（女）→ 身份锁拒绝
    b2 = BuyerMaster(tenant_id="t1", email="a@x.com", contact_name="Ahmed", contact_gender="female")
    out, is_new, alerts = store.upsert(b2)
    assert is_new is False
    assert out.buyer_id == b1.buyer_id
    assert out.contact_gender == "male"
    assert any("身份锁" in a or "人设" in a for a in alerts)
    assert len(store.conflict_alerts) >= 1


def test_identity_lock_blocks_rename():
    store = BuyerMasterStore()
    b1 = BuyerMaster(tenant_id="t1", email="b@x.com", contact_name="Li", contact_gender="male")
    store.upsert(b1)
    b2 = BuyerMaster(tenant_id="t1", email="b@x.com", contact_name="Wang", contact_gender="male")
    out, _, alerts = store.upsert(b2)
    assert out.contact_name == "Li"
    assert any("改名" in a or "人设" in a for a in alerts)


def test_buyer_get_by_email():
    store = BuyerMasterStore()
    b = BuyerMaster(tenant_id="t1", email="c@x.com", contact_name="X")
    store.upsert(b)
    got = store.get_by_email("t1", "C@X.com")
    assert got is not None and got.buyer_id == b.buyer_id


# ── Ops Card 跟单卡 ─────────────────────────────────────────

def test_ops_card_materialize_and_summary():
    store = OpsCardStore()
    buyer = BuyerMaster(tenant_id="t1", contact_name="Ahmed", company_name="Gulf")
    card = store.materialize(
        tenant_id="t1",
        inquiry_id="inq1",
        buyer_id=buyer.buyer_id,
        owner_user_id="user_001",
        buyer=buyer,
        grade="B",
        grade_reason="规格清楚",
        playbook_tips=["印度新客首款偏全款"],
    )
    assert card.owner_user_id == "user_001"
    assert "Ahmed" in card.buyer_display
    assert card.buyer_grade == "B"
    assert card.playbook_tips

    lines = card.summary_lines()
    assert lines["负责人"] == "user_001"
    assert "Ahmed" in lines.get("负责人", "") or "Ahmed" in card.buyer_display


def test_ops_card_handoff():
    store = OpsCardStore()
    store.materialize(tenant_id="t1", inquiry_id="inq2", owner_user_id="u1")
    card = store.set_owner("inq2", "u2", note="交接")
    assert card.owner_user_id == "u2"
    assert card.handoff_history and card.handoff_history[0]["from"] == "u1"
    assert card.handoff_history[0]["to"] == "u2"


def test_ops_card_touch_notes_payment():
    store = OpsCardStore()
    store.materialize(tenant_id="t1", inquiry_id="inq3")
    store.record_touch("inq3", channel="whatsapp", summary="已读未回", next_action="三日后再触达")
    card = store.add_note("inq3", author="sales", body="客户要求 CIF 吉达")
    card = store.update_payment("inq3", pi_no="PI-001", deposit_amount=3000, deposit_paid_at="2026-09-18")
    card = store.update_logistics("inq3", carrier="COSCO", bl_no="COSU123", milestone="已装船")
    s = card.summary_lines()
    assert "已读未回" in s["联系"]
    assert "CIF" in s["交代"]
    assert "PI-001" in s["付款"]
    assert "COSCO" in s["物流"] or "COSU123" in s["物流"]


def test_ops_card_loss():
    store = OpsCardStore()
    store.materialize(tenant_id="t1", inquiry_id="inq4")
    card = store.record_loss("inq4", reasons=["价格高", "已选同行"], note="聊到报价后流失")
    assert card.stage == "lost"
    assert "价格高" in card.loss_reasons


# ── Playbook ────────────────────────────────────────────────

def test_playbook_india_new_buyer():
    store = PlaybookStore()
    tips = store.tips_for("IN", "new")
    assert any("全款" in t or "定金" in t for t in tips)


def test_playbook_saudi_project():
    store = PlaybookStore()
    entries = store.match(country="SA", buyer_type="project")
    assert entries
    assert any("认证" in t or "SASO" in t for t in entries[0].tips)


def test_playbook_custom_add():
    store = PlaybookStore(seed=False)
    store.add(PlaybookEntry(country="BR", buyer_type="distributor", tips=["巴西分销商注意付款方式"]))
    tips = store.tips_for("BR", "distributor")
    assert "巴西" in tips[0]


# ── 评分 ────────────────────────────────────────────────────

def test_score_grade_reasons():
    assert score_grade(90)[0] == "A"
    assert score_grade(70)[0] == "B"
    assert score_grade(50)[0] == "C"
    assert score_grade(10)[0] == "D"
    g, r = score_grade(10)
    assert r  # 有理由
