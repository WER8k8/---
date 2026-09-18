"""全域商业闭环单元测试：
1. 询盘 -> BOQ 22 参数核价 -> 报价单生成
2. 报价单一键转换为正式外贸订单（含 256 位安全 Access Token 与定金折算）
3. 支付状态机联动：定金 partial 到账触发 deposit_received，尾款 paid 触发 final_payment_received
4. 经验自进化引擎：任务终态留痕与沉淀
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from app.api.v1.quotes import (
    calculate_boq,
    create_from_inquiry,
    convert_to_order,
    BOQCalculationRequest,
    QuoteFromInquiryRequest,
    ConvertQuoteToOrderRequest,
)
from app.services.order_payment_sync_service import update_order_payment_status
from app.services.hermes.experience_engine import get_engine, ExperienceEngine
from app.models.enums import OrderStatus, PaymentStatus


TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")
INQUIRY_ID = uuid.UUID("00000000-0000-0000-0000-000000000003")
QUOTE_ID = uuid.UUID("00000000-0000-0000-0000-000000000004")
ORDER_ID = uuid.UUID("00000000-0000-0000-0000-000000000005")


def _make_user(uid=USER_ID, role="admin", tid=TENANT_ID):
    u = MagicMock()
    u.id = uid
    u.role = role
    u.tenant_id = tid
    return u


def _make_mock_db():
    db = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.first.return_value = None
    q.all.return_value = []
    db.query.return_value = q
    db.add = MagicMock()
    db.flush = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock(side_effect=lambda o: None)
    return db


class TestCommercialClosedLoop:
    def test_boq_calculate_endpoint(self):
        """测试 BOQ 22 参数核价端点"""
        req = BOQCalculationRequest(
            material_type="granite",
            quantity_sqm=500.0,
            incoterms="CIF",
            customization=True,
            insurance_required=True,
        )
        res = calculate_boq(req)
        data = res.data
        assert data["currency"] == "USD"
        assert data["quantity"] == 500.0
        assert data["base_price"] == 60.0
        # 60 * 500 * 1.15 * 1.02 = 35190.0
        assert data["total"] == 35190.0

    def test_inquiry_to_quote_conversion(self):
        """测试从询盘一键创建报价单草稿"""
        db = _make_mock_db()
        inquiry = MagicMock()
        inquiry.id = INQUIRY_ID
        inquiry.tenant_id = TENANT_ID
        inquiry.product_name = "Calcium Silicate Board"
        db.query.return_value.filter.return_value.first.return_value = inquiry

        user = _make_user()
        req = QuoteFromInquiryRequest(
            inquiry_id=str(INQUIRY_ID),
            payment_terms="T/T 30% Deposit, 70% before shipment",
            delivery_terms="CIF Jeddah",
            quantity=1000.0,
            unit_price=25.5,
        )

        res = create_from_inquiry(req=req, db=db, current_user=user)
        quote_data = res.data
        assert quote_data["inquiry_id"] == str(INQUIRY_ID)
        assert quote_data["total_amount"] == 25500.0
        assert quote_data["payment_terms"] == "T/T 30% Deposit, 70% before shipment"
        assert quote_data["delivery_terms"] == "CIF Jeddah"
        assert db.add.called

    def test_quote_to_order_conversion(self):
        """测试报价单一键转为正式订单，自动签发 256 位安全 Access Token"""
        db = _make_mock_db()
        quote = MagicMock()
        quote.id = QUOTE_ID
        quote.tenant_id = TENANT_ID
        quote.merchant_id = USER_ID
        quote.total_amount = 25500.0
        quote.currency = "USD"
        quote.delivery_terms = "CIF Jeddah"
        quote.payment_terms = "T/T 30/70"
        quote.status = "approved"
        db.query.return_value.filter.return_value.first.return_value = quote

        user = _make_user()
        req = ConvertQuoteToOrderRequest(
            deposit_ratio=30.0,
            shipping_address="Jeddah Islamic Port, Warehouse 4B",
        )

        res = convert_to_order(quote_id=str(QUOTE_ID), req=req, db=db, current_user=user)
        order_data = res.data
        assert order_data["status"] == "pending"
        assert order_data["total_amount"] == 25500.0
        assert order_data["deposit_amount"] == 7650.0  # 30% of 25500
        assert len(order_data["access_token"]) == 64   # 256-bit hex
        assert order_data["incoterms"] == "CIF Jeddah"
        assert quote.status == "converted"


class TestPaymentStateTransitions:
    def test_partial_payment_triggers_deposit_received(self):
        """测试定金支付回调(partial)自动推进订单状态机至 deposit_received"""
        db = _make_mock_db()
        order = MagicMock()
        order.id = ORDER_ID
        order.order_number = "ORD-20260913-001"
        order.status = "confirmed"
        order.payment_status = "unpaid"
        db.query.return_value.filter.return_value.first.return_value = order

        res = update_order_payment_status(db, str(ORDER_ID), "partial", auto_confirm=True)
        assert res["payment_status"] == "partial"
        assert res["status"] == "deposit_received"
        assert order.status == "deposit_received"

    def test_paid_payment_triggers_final_payment_received(self):
        """测试尾款结清回调(paid)推进已发货订单至 final_payment_received"""
        db = _make_mock_db()
        order = MagicMock()
        order.id = ORDER_ID
        order.order_number = "ORD-20260913-002"
        order.status = "shipped"
        order.payment_status = "partial"
        db.query.return_value.filter.return_value.first.return_value = order

        res = update_order_payment_status(db, str(ORDER_ID), "paid", auto_confirm=True)
        assert res["payment_status"] == "paid"
        assert res["status"] == "final_payment_received"
        assert order.status == "final_payment_received"


class TestExperienceEngineRecording:
    def test_experience_engine_records_and_evolves(self):
        """测试经验引擎记录与进化统计"""
        engine = get_engine()
        engine.record("test_task_type", True, 1.25)
        engine.record("test_task_type", False, 3.5, error_type="timeout", solution="retry with longer timeout")

        history = engine.query("test_task_type", top_k=5)
        assert len(history) >= 2
        stats = engine.get_stats()
        assert "test_task_type" in stats
        assert stats["test_task_type"]["total"] >= 2
