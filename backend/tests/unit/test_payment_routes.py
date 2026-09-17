"""支付路由单元测试 — create / notify / orders / mock-pay"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


# ── 辅助 ────────────────────────────────────────────────────


def _make_user(role: str = "admin", is_active: bool = True):
    u = MagicMock()
    u.id = "usr-1"
    u.role = role
    u.is_active = is_active
    return u


def _make_db() -> MagicMock:
    db = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.first.return_value = None
    db.query.return_value = q
    return db


# ── create_payment ──────────────────────────────────────────


class TestCreatePayment:
    def test_create_payment_calls_service(self):
        from app.api.v1.routes.payment import create_payment
        from app.api.v1.routes.payment import CreatePaymentRequest

        db = _make_db()
        user = _make_user()

        with patch("app.api.v1.routes.payment.get_current_user", return_value=user):
            with patch("app.api.v1.routes.payment.PaymentService") as MockSvc:
                mock_svc = MagicMock()
                mock_svc._create_channel_native.return_value = {"code_url": "weixin://mock"}
                MockSvc.return_value = mock_svc
                with patch("app.api.v1.routes.payment.success_response") as mock_ok:
                    mock_ok.return_value = MagicMock()
                    req = CreatePaymentRequest(
                        tenant_id="tenant-1",
                        subscription_id="sub-1",
                        channel="wechat",
                        amount=10000,
                        subject="订阅续费",
                        currency="CNY",
                    )
                    result = create_payment(req, db=db, current_user=user)
                    mock_ok.assert_called_once()


# ── create_native_payment ──────────────────────────────────


class TestCreateNativePayment:
    def test_native_payment_creates_order(self):
        from app.api.v1.routes.payment import create_native_payment
        from app.api.v1.routes.payment import CreateNativePaymentRequest

        db = _make_db()
        user = _make_user()

        with patch("app.api.v1.routes.payment.get_current_user", return_value=user):
            with patch("app.api.v1.routes.payment.PaymentService") as MockSvc:
                mock_svc = MagicMock()
                mock_svc._create_channel_native.return_value = {"code_url": "mock-url"}
                MockSvc.return_value = mock_svc
                with patch("app.api.v1.routes.payment.success_response") as mock_ok:
                    mock_ok.return_value = MagicMock()
                    req = CreateNativePaymentRequest(
                        tenant_id="tenant-1",
                        plan_id="plan-1",
                        billing_cycle="monthly",
                        channel="wechat",
                    )
                    result = create_native_payment(req, db=db, current_user=user)
                    mock_ok.assert_called_once()


# ── payment_notify ──────────────────────────────────────────


class TestPaymentNotify:
    def test_notify_verify_fail(self):
        from app.api.v1.routes.payment import payment_notify
        from app.api.v1.routes.payment import NotifyRequest

        db = _make_db()

        with patch("app.api.v1.routes.payment._notify_strict_enabled", return_value=True):
            with patch("app.api.v1.routes.payment.PaymentService") as MockSvc:
                mock_svc = MagicMock()
                mock_svc.verify_notify.return_value = False
                MockSvc.return_value = mock_svc
                req = NotifyRequest(channel="wechat", data={}, signature="sig")
                result = payment_notify(req, db=db)
                assert result.status_code == 403

    def test_notify_amount_mismatch(self):
        from app.api.v1.routes.payment import payment_notify
        from app.api.v1.routes.payment import NotifyRequest

        db = _make_db()

        with patch("app.api.v1.routes.payment._notify_strict_enabled", return_value=False):
            with patch("app.api.v1.routes.payment.PaymentService") as MockSvc:
                mock_svc = MagicMock()
                mock_svc.process_wechat_notify.return_value = None
                MockSvc.return_value = mock_svc
                req = NotifyRequest(channel="wechat", data={"total_fee": "999"}, signature="sig")
                result = payment_notify(req, db=db)
                assert result.status_code == 404


# ── list_payment_orders ─────────────────────────────────────


class TestListPaymentOrders:
    def test_list_orders(self):
        from app.api.v1.routes.payment import list_payment_orders

        db = _make_db()
        user = _make_user()
        order = MagicMock()
        order.id = "ord-1"
        order.order_no = "NO-001"
        order.amount = 1000
        order.status = "paid"
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.offset.return_value.all.return_value = [order]
        # count
        db.query.return_value.filter.return_value.count.return_value = 1

        with patch("app.api.v1.routes.payment.get_current_user", return_value=user):
            with patch("app.api.v1.routes.payment.success_response") as mock_ok:
                mock_ok.return_value = MagicMock()
                result = list_payment_orders(db=db, current_user=user, page=1, page_size=10)
                mock_ok.assert_called_once()


# ── get_payment_order ───────────────────────────────────────


class TestGetPaymentOrder:
    def test_get_order_found(self):
        from app.api.v1.routes.payment import get_payment_order

        db = _make_db()
        user = _make_user()
        order = MagicMock()
        order.id = "ord-1"
        db.query.return_value.filter.return_value.first.return_value = order

        with patch("app.api.v1.routes.payment.get_current_user", return_value=user):
            with patch("app.api.v1.routes.payment.success_response") as mock_ok:
                mock_ok.return_value = MagicMock()
                result = get_payment_order("ord-1", db=db, current_user=user)
                mock_ok.assert_called_once()

    def test_get_order_not_found(self):
        from app.api.v1.routes.payment import get_payment_order

        db = _make_db()
        user = _make_user()
        db.query.return_value.filter.return_value.first.return_value = None

        with patch("app.api.v1.routes.payment.get_current_user", return_value=user):
            with patch("app.api.v1.routes.payment.error_response") as mock_err:
                mock_err.return_value = MagicMock(status_code=404)
                result = get_payment_order("ord-999", db=db, current_user=user)
                mock_err.assert_called_once()


# ── mock_pay ────────────────────────────────────────────────


class TestMockPay:
    def test_mock_pay_allowed(self):
        from app.api.v1.routes.payment import mock_pay
        from app.api.v1.routes.payment import MockPayRequest

        db = _make_db()
        user = _make_user()

        with patch("app.api.v1.routes.payment._mock_pay_allowed", return_value=True):
            with patch("app.api.v1.routes.payment.get_current_user", return_value=user):
                with patch("app.api.v1.routes.payment.PaymentService") as MockSvc:
                    mock_svc = MagicMock()
                    mock_svc.mock_pay_order.return_value = MagicMock(success=True)
                    MockSvc.return_value = mock_svc
                    with patch("app.api.v1.routes.payment.success_response") as mock_ok:
                        mock_ok.return_value = MagicMock()
                        req = MockPayRequest(order_id="ord-mock")
                        result = mock_pay(req, db=db, current_user=user)
                        mock_ok.assert_called_once()

    def test_mock_pay_disabled(self):
        from app.api.v1.routes.payment import mock_pay
        from app.api.v1.routes.payment import MockPayRequest

        db = _make_db()
        user = _make_user()

        with patch("app.api.v1.routes.payment._mock_pay_allowed", return_value=False):
            with patch("app.api.v1.routes.payment.get_current_user", return_value=user):
                with patch("app.api.v1.routes.payment.error_response") as mock_err:
                    mock_err.return_value = MagicMock(status_code=403)
                    req = MockPayRequest(order_id="ord-x")
                    result = mock_pay(req, db=db, current_user=user)
                    mock_err.assert_called_once()


# ── payment channels status ────────────────────────────────


class TestPaymentChannelsStatus:
    def test_channels_status(self):
        from app.api.v1.routes.payment import payment_channels_status

        db = _make_db()
        user = _make_user()
        channel = MagicMock()
        channel.channel = "wechat"
        channel.is_active = True
        db.query.return_value.filter.return_value.all.return_value = [channel]

        with patch("app.api.v1.routes.payment.get_current_user", return_value=user):
            with patch("app.api.v1.routes.payment.success_response") as mock_ok:
                mock_ok.return_value = MagicMock()
                result = payment_channels_status(db=db, current_user=user)
                mock_ok.assert_called_once()


# ── list_plans ──────────────────────────────────────────────


class TestListPlans:
    def test_list_plans(self):
        from app.api.v1.routes.payment import list_plans

        db = _make_db()
        user = _make_user()
        plan = MagicMock()
        plan.id = 1
        plan.name = "Pro"
        plan.price_cents = 9900
        db.query.return_value.filter.return_value.all.return_value = [plan]

        with patch("app.api.v1.routes.payment.get_current_user", return_value=user):
            with patch("app.api.v1.routes.payment.success_response") as mock_ok:
                mock_ok.return_value = MagicMock()
                result = list_plans(db=db, current_user=user)
                mock_ok.assert_called_once()
