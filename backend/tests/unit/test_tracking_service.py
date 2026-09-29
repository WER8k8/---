# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""物流轨迹服务测试（修正设计稿 模块8.4/8.5 / Gate G8）。

锁定语义：
- 事件幂等：(provider, external_event_id) 同键重放只落一条；
- 状态归一：Provider 原始状态/描述 → 规范状态；无法识别 → unknown；
- 秩序守卫：delivered 之后又来 in_transit → 拒绝落库不回退；
- shipment_stage 由真实事件推导（booking/shipped/delivered/exception）；
- 无事件 → current_view = tracking_unavailable（红线：不伪造 in_transit）；
- 人工录入必须带操作审计（operator/reason）；
- demo 轨迹不得写回订单状态（sync_order_from_tracking 守卫）。
"""
from __future__ import annotations

import pytest

from app.models.trade_fulfillment import LogisticsShipment
from app.services import tracking_service as ts

TENANT = "7a111111-1111-4111-8111-111111111111"


@pytest.fixture
def shipment(db_session):
    s = LogisticsShipment(
        id="7b111111-1111-4111-8111-111111111111",
        tenant_id=TENANT,
        tracking_no="SF999888777",
        carrier="kuaidi100",
        status="pending",
    )
    db_session.add(s)
    db_session.commit()
    return s


class TestIngest:
    def test_ingest_and_idempotent_replay(self, db_session, shipment):
        r1 = ts.ingest_event(
            db_session, shipment, provider="kuaidi100", external_event_id="EVT-1",
            raw_status="已揽收", location="深圳",
        )
        assert r1["persisted"] is True
        assert r1["status"] == "picked_up"
        assert shipment.shipment_stage == "shipped"

        # 同事件重放（Provider 重试/回调重放）→ 幂等，不落第二条
        r2 = ts.ingest_event(
            db_session, shipment, provider="kuaidi100", external_event_id="EVT-1",
            raw_status="已揽收",
        )
        assert r2["idempotent"] is True
        assert db_session.query(ts.TrackingEvent).count() == 1

    def test_regression_guard(self, db_session, shipment):
        """delivered 之后又来 in_transit → 拒绝落库，状态不回退。"""
        ts.ingest_event(db_session, shipment, provider="kuaidi100",
                        external_event_id="E1", raw_status="delivered")
        assert shipment.shipment_stage == "delivered"
        r = ts.ingest_event(db_session, shipment, provider="kuaidi100",
                            external_event_id="E2", raw_status="in_transit")
        assert r.get("ignored") is True
        assert shipment.shipment_stage == "delivered"  # 不回退
        assert db_session.query(ts.TrackingEvent).filter_by(external_event_id="E2").count() == 0


class TestManualAudit:
    def test_manual_requires_reason(self, db_session, shipment):
        with pytest.raises(ts.TrackingError):
            ts.manual_event(db_session, shipment, operator="op-1", reason="", raw_status="in_transit")

    def test_manual_persists_with_audit(self, db_session, shipment):
        r = ts.manual_event(
            db_session, shipment, operator="op-1",
            reason="客户口述已提货，待与承运商核实", raw_status="in_transit",
        )
        assert r["persisted"] is True
        ev = db_session.query(ts.TrackingEvent).filter_by(source="manual").one()
        assert ev.operator == "op-1"
        assert "口述" in (ev.operator_reason or "")


class TestCurrentView:
    def test_no_events_is_tracking_unavailable(self, db_session, shipment):
        view = ts.current_view(db_session, shipment)
        assert view["status"] == "tracking_unavailable"
        assert view["events"] == []

    def test_with_events_returns_canonical_timeline(self, db_session, shipment):
        ts.ingest_event(db_session, shipment, provider="kuaidi100",
                        external_event_id="A1", raw_status="已揽收")
        ts.ingest_event(db_session, shipment, provider="kuaidi100",
                        external_event_id="A2", raw_status="运输中", location="中转中心")
        view = ts.current_view(db_session, shipment)
        assert view["status"] == "in_transit"
        assert view["shipment_stage"] == "shipped"
        assert len(view["events"]) == 2


class TestNormalizeStatus:
    def test_provider_tokens_map(self):
        assert ts.normalize_status("kuaidi100", "已揽收") == "picked_up"
        assert ts.normalize_status("dhl", "in transit") == "in_transit"
        assert ts.normalize_status("x", "out for delivery") == "out_for_delivery"
        assert ts.normalize_status("x", "delivered") == "delivered"
        assert ts.normalize_status("x", "清关中") == "customs"

    def test_unknown_is_unknown(self):
        assert ts.normalize_status("x", "完全未知的说法") == "unknown"


class TestDemoGuard:
    def test_demo_payload_not_persisted_to_order(self, db_session, monkeypatch):
        """Gate G8 红线：demo 轨迹不得写回订单状态。"""
        from types import SimpleNamespace

        from app.services import logistics_tracking_service as lts

        order = SimpleNamespace(
            id="ord-1", order_number="SO-1", tracking_number="SF123",
            status="paid", estimated_delivery=None,
        )
        monkeypatch.setattr(
            lts, "fetch_tracking_payload",
            lambda n, c: {"status": "in_transit", "demo": True, "provider": "demo"},
        )
        result = lts.sync_order_from_tracking(db_session, order)
        assert result["persisted"] is False
        assert result["reason"] == "demo_tracking_not_persisted"
        assert order.status == "paid"  # 未被伪造状态覆盖
