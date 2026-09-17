"""跨境支付与出海合规单元测试。"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock
from app.services.stripe_pay_service import StripePayService
from app.services.paypal_pay_service import PayPalPayService
from app.services.gdpr_compliance_service import GDPRComplianceService


def test_stripe_checkout_creation():
    db = MagicMock()
    svc = StripePayService(db)
    res = svc.create_checkout_session(
        tenant_id="00000000-0000-0000-0000-000000000001",
        amount_cents=2900,
        currency="usd",
        product_name="Pro Tier Plan",
    )
    assert res["amount"] == 2900
    assert res["currency"] == "USD"
    assert "checkout_url" in res
    assert res["order_no"].startswith("STP_")
    assert db.add.called
    assert db.commit.called


def test_stripe_webhook_handle_success():
    db = MagicMock()
    order = MagicMock()
    order.status = "pending"
    order.amount = 2900
    order.tenant_id = "00000000-0000-0000-0000-000000000001"
    order.order_no = "STP_12345_abc"
    db.query.return_value.filter.return_value.first.return_value = order

    svc = StripePayService(db)
    event = {
        "type": "checkout.session.completed",
        "data": {"object": {"client_reference_id": "STP_12345_abc"}},
    }
    assert svc.handle_checkout_completed(event) is True
    assert order.status == "paid"


def test_paypal_order_and_capture():
    db = MagicMock()
    svc = PayPalPayService(db)
    res = svc.create_order(
        tenant_id="00000000-0000-0000-0000-000000000001",
        amount_cents=5000,
        currency="USD",
    )
    assert res["amount"] == 50.0
    assert res["order_no"].startswith("PPL_")

    order = MagicMock()
    order.status = "pending"
    order.amount = 5000
    order.tenant_id = "00000000-0000-0000-0000-000000000001"
    db.query.return_value.filter.return_value.first.return_value = order

    assert svc.capture_order(res["order_no"], res["paypal_order_id"]) is True
    assert order.status == "paid"


def test_gdpr_export_and_anonymize():
    db = MagicMock()
    user = MagicMock()
    user.id = "00000000-0000-0000-0000-000000000001"
    user.username = "test_john"
    user.email = "john@example.com"
    user.role = "member"
    db.query.return_value.filter.return_value.first.return_value = user

    svc = GDPRComplianceService(db)
    export_data = svc.export_user_data(str(user.id))
    assert export_data["username"] == "test_john"
    assert "GDPR" in export_data["compliance_standard"]

    assert svc.anonymize_user(str(user.id)) is True
    assert user.is_active is False
    assert "@privacy-gdpr.void" in user.email
