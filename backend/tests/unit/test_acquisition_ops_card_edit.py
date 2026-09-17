# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P1-1 跟单卡：收款 / 物流 / 货物编辑。"""
from __future__ import annotations

from app.api.v1.routes import acquisition as acq_api
from app.services.acquisition import ops_card_store


def _card(inquiry_id: str):
    return ops_card_store.get_by_inquiry(inquiry_id)


def test_payment_update():
    ops_card_store._by_inquiry.clear()
    ops_card_store._by_id.clear()
    ops_card_store.materialize(tenant_id="t1", inquiry_id="INQ-PAY-1")
    r = acq_api.ops_card_payment(
        "INQ-PAY-1",
        acq_api.OpsCardPaymentRequest(
            pi_no="PI-2026-001",
            deposit_amount=3000,
            deposit_paid_at="2026-09-18",
            balance_amount=7000,
            balance_status="pending",
        ),
        current_user=None,
    )
    s = r["summary"]
    assert "PI-2026-001" in s["付款"]
    assert "已收" in s["付款"] or "3000" in s["付款"]
    assert _card("INQ-PAY-1").payment.deposit_amount == 3000


def test_logistics_update():
    ops_card_store._by_inquiry.clear()
    ops_card_store._by_id.clear()
    ops_card_store.materialize(tenant_id="t1", inquiry_id="INQ-LOG-1")
    r = acq_api.ops_card_logistics(
        "INQ-LOG-1",
        acq_api.OpsCardLogisticsRequest(carrier="COSCO", bl_no="COSU123456", etd="2026-10-01", eta="2026-10-20"),
        current_user=None,
    )
    assert "COSCO" in r["summary"]["物流"] or "COSU123456" in r["summary"]["物流"]
    assert _card("INQ-LOG-1").logistics.etd == "2026-10-01"


def test_goods_update():
    ops_card_store._by_inquiry.clear()
    ops_card_store._by_id.clear()
    ops_card_store.materialize(tenant_id="t1", inquiry_id="INQ-GOODS-1")
    r = acq_api.ops_card_goods(
        "INQ-GOODS-1",
        acq_api.OpsCardGoodsRequest(
            sku_lines=[acq_api.OpsCardSkuLineRequest(name="岩棉板", spec="1200x600x50", qty=5000, unit="㎡")]
        ),
        current_user=None,
    )
    assert "岩棉板" in r["summary"]["货"]
    assert _card("INQ-GOODS-1").sku_lines[0].name == "岩棉板"


def test_hard_locks_still_ok():
    from pathlib import Path
    wt = Path(__file__).resolve().parents[3]
    assert (wt / "frontend/admin/src/views/login/index.vue").exists()
    ui = (wt / "frontend/admin/src/stores/uiPreferences.ts").read_text(encoding="utf-8")
    assert "#4a9b8c" in ui
