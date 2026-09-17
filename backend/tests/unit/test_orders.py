"""订单路由单元测试：order-token 买家鉴权 + 登录态卖家/管理员鉴权"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from fastapi import HTTPException


BUYER_ID = "00000000-0000-0000-0000-000000000002"
MERCHANT_ID = "00000000-0000-0000-0000-000000000003"
ADMIN_ID = "00000000-0000-0000-0000-000000000099"
TOKEN = "tok123"


def _make_order(
    order_id: str = "00000000-0000-0000-0000-000000000001",
    order_number: str = "ORD-1234567890",
    status: str = "pending",
    payment_status: str = "unpaid",
    total_amount: float = 99.99,
    currency: str = "USD",
    access_token: str = TOKEN,
    buyer_id: str = BUYER_ID,
    merchant_id: str = MERCHANT_ID,
):
    order = MagicMock()
    order.id = order_id
    order.order_number = order_number
    order.status = status
    order.payment_status = payment_status
    order.total_amount = total_amount
    order.currency = currency
    order.shipping_address = "123 Test St"
    order.tracking_number = None
    order.access_token = access_token
    order.buyer_id = buyer_id
    order.merchant_id = merchant_id
    order.tenant_id = "00000000-0000-0000-0000-000000000001"
    order.incoterms = None
    order.payment_terms = None
    order.deposit_ratio = None
    order.deposit_amount = None
    order.port_of_loading = None
    order.port_of_discharge = None
    order.gross_weight = None
    order.net_weight = None
    order.volume = None
    order.shipping_marks = None
    order.container_no = None
    order.bl_number = None
    order.created_at = MagicMock()
    order.created_at.isoformat.return_value = "2024-01-01T00:00:00Z"
    return order


def _make_db(order=None) -> MagicMock:
    db = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.first.return_value = order
    q.order_by.return_value = q
    q.offset.return_value = q
    q.limit.return_value = q
    q.all.return_value = [order] if order else []
    q.count.return_value = 0
    db.query.return_value = q
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock(side_effect=lambda o: None)
    db.rollback = MagicMock()
    return db


def _make_request(token: str = "") -> MagicMock:
    req = MagicMock()
    req.headers.get.return_value = token
    req.query_params.get.return_value = ""
    return req


def _make_user(role: str = "admin", uid: str = ADMIN_ID) -> MagicMock:
    u = MagicMock()
    u.id = uid
    u.role = role
    u.tenant_id = ADMIN_ID
    return u


class TestCreateOrder:
    def test_create_order_success_returns_access_token(self):
        from app.api.v1.orders import create_order

        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        db.add = MagicMock(side_effect=lambda o: setattr(o, "id", "00000000-0000-0000-0000-000000000009"))

        result = create_order(
            buyer_id=BUYER_ID,
            merchant_id=MERCHANT_ID,
            total_amount=99.99,
            currency="USD",
            user=_make_user(),
            db=db,
        )
        assert result.code == 0
        assert result.data["access_token"]
        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_create_order_token_is_256bit_hex(self):
        from app.api.v1.orders import create_order

        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        captured = {}

        def _capture(order):
            captured["token"] = order.access_token
            setattr(order, "id", "00000000-0000-0000-0000-000000000009")

        db.add = MagicMock(side_effect=_capture)
        create_order(
            buyer_id=BUYER_ID,
            merchant_id=MERCHANT_ID,
            total_amount=99.99,
            user=_make_user(),
            db=db,
        )
        tok = captured["token"]
        assert len(tok) == 64
        assert all(c in "0123456789abcdef" for c in tok)

    def test_create_order_non_admin_forces_own_buyer_id(self):
        from app.api.v1.orders import create_order

        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        captured = {}

        def _capture(order):
            captured["buyer_id"] = str(order.buyer_id)
            setattr(order, "id", "00000000-0000-0000-0000-000000000009")

        db.add = MagicMock(side_effect=_capture)
        user = _make_user(role="tenant", uid="00000000-0000-0000-0000-000000000007")
        create_order(
            buyer_id=BUYER_ID,  # 尝试伪造他人
            merchant_id=MERCHANT_ID,
            total_amount=99.99,
            user=user,
            db=db,
        )
        assert captured["buyer_id"] == str(user.id)

    def test_create_order_invalid_uuid_raises(self):
        from app.api.v1.orders import create_order

        db = _make_db()
        with pytest.raises(Exception):
            create_order(
                buyer_id="not-a-uuid",
                merchant_id="merchant-1",
                total_amount=100,
                user=_make_user(),
                db=db,
            )


class TestGetOrder:
    def test_get_order_anonymous_without_token_404(self):
        from app.api.v1.orders import get_order

        db = _make_db(_make_order())
        with pytest.raises(HTTPException) as exc:
            get_order("00000000-0000-0000-0000-000000000001", request=_make_request(), user=None, db=db)
        assert exc.value.status_code == 404

    def test_get_order_admin_ok(self):
        from app.api.v1.orders import get_order

        db = _make_db(_make_order())
        result = get_order("00000000-0000-0000-0000-000000000001", request=_make_request(), user=_make_user(), db=db)
        assert result.data["id"] == "00000000-0000-0000-0000-000000000001"

    def test_get_order_with_token_ok(self):
        from app.api.v1.orders import get_order

        db = _make_db(_make_order())
        result = get_order("00000000-0000-0000-0000-000000000001", request=_make_request(TOKEN), user=None, db=db)
        assert result.data["id"] == "00000000-0000-0000-0000-000000000001"

    def test_get_order_wrong_token_404(self):
        from app.api.v1.orders import get_order

        db = _make_db(_make_order())
        with pytest.raises(HTTPException) as exc:
            get_order("00000000-0000-0000-0000-000000000001", request=_make_request("wrong"), user=None, db=db)
        assert exc.value.status_code == 404

    def test_get_order_not_found(self):
        from app.api.v1.orders import get_order

        db = _make_db(None)
        with pytest.raises(HTTPException) as exc:
            get_order("00000000-0000-0000-0000-000000000001", request=_make_request(TOKEN), user=None, db=db)
        assert exc.value.status_code == 404


class TestListOrders:
    def test_list_anonymous_without_token_400(self):
        from app.api.v1.orders import list_orders

        db = _make_db(_make_order())
        with pytest.raises(HTTPException) as exc:
            list_orders(request=_make_request(), user=None, db=db)
        assert exc.value.status_code == 400

    def test_list_with_token_filters_by_token(self):
        from app.api.v1.orders import list_orders

        db = _make_db(_make_order())
        filters = []
        db.query.return_value.filter.side_effect = lambda *a, **k: (filters.append(a) or db.query.return_value)
        list_orders(request=_make_request(TOKEN), user=None, db=db)
        assert any("access_token" in str(c[0]) for c in filters)

    def test_list_admin_with_buyer_filter(self):
        from app.api.v1.orders import list_orders

        db = _make_db(_make_order())
        result = list_orders(request=_make_request(), user=_make_user(), buyer_id=BUYER_ID, db=db)
        assert len(result) == 1

    def test_list_merchant_login_forces_own_scope(self):
        from app.api.v1.orders import list_orders

        db = _make_db(_make_order())
        filters = []
        db.query.return_value.filter.side_effect = lambda *a, **k: (filters.append(a) or db.query.return_value)
        list_orders(request=_make_request(), user=_make_user(role="merchant", uid=MERCHANT_ID), db=db)
        assert filters and any("buyer_id" in str(c[0]) or "merchant_id" in str(c[0]) for c in filters)


class TestUpdateOrderStatus:
    def test_buyer_with_token_can_cancel_pending(self):
        from app.api.v1.orders import update_order_status

        db = _make_db(_make_order())
        result = update_order_status(
            "00000000-0000-0000-0000-000000000001", "cancelled",
            request=_make_request(TOKEN), user=None, db=db,
        )
        assert result.data["status"] == "cancelled"
        db.commit.assert_called_once()

    def test_buyer_with_token_cannot_confirm(self):
        from app.api.v1.orders import update_order_status

        db = _make_db(_make_order())
        with pytest.raises(HTTPException) as exc:
            update_order_status(
                "00000000-0000-0000-0000-000000000001", "confirmed",
                request=_make_request(TOKEN), user=None, db=db,
            )
        assert exc.value.status_code == 403

    def test_admin_any_status_ok(self):
        from app.api.v1.orders import update_order_status

        db = _make_db(_make_order())
        result = update_order_status(
            "00000000-0000-0000-0000-000000000001", "confirmed",
            request=_make_request(), user=_make_user(), db=db,
        )
        assert result.data["status"] == "confirmed"

    def test_no_credentials_404(self):
        from app.api.v1.orders import update_order_status

        db = _make_db(_make_order())
        with pytest.raises(HTTPException) as exc:
            update_order_status(
                "00000000-0000-0000-0000-000000000001", "confirmed",
                request=_make_request(), user=None, db=db,
            )
        assert exc.value.status_code == 404

    def test_invalid_status_rejected(self):
        from app.api.v1.orders import update_order_status

        db = _make_db(_make_order())
        with pytest.raises(HTTPException) as exc:
            update_order_status(
                "00000000-0000-0000-0000-000000000001", "invalid-status",
                request=_make_request(TOKEN), user=None, db=db,
            )
        assert exc.value.status_code == 400


class TestUpdateOrderPaymentStatus:
    def test_buyer_forbidden(self):
        from app.api.v1.orders import update_order_payment_status, PaymentStatusUpdate

        db = _make_db(_make_order())
        body = PaymentStatusUpdate(payment_status="paid", auto_confirm=True)
        with pytest.raises(HTTPException) as exc:
            update_order_payment_status(
                "00000000-0000-0000-0000-000000000001", body,
                request=_make_request(TOKEN), user=None, db=db,
            )
        assert exc.value.status_code == 403

    def test_admin_ok(self):
        from app.api.v1.orders import update_order_payment_status, PaymentStatusUpdate
        from unittest.mock import patch

        db = _make_db(_make_order())
        mock_sync = MagicMock(return_value={"ok": True})
        body = PaymentStatusUpdate(payment_status="paid", auto_confirm=True)
        with patch("app.services.order_payment_sync_service.update_order_payment_status", mock_sync):
            result = update_order_payment_status(
                "00000000-0000-0000-0000-000000000001", body,
                request=_make_request(), user=_make_user(), db=db,
            )
            mock_sync.assert_called_once()
            assert result == {"ok": True}


class TestUpdateOrderTracking:
    def test_buyer_forbidden(self):
        from app.api.v1.orders import update_order_tracking, TrackingNumberUpdate

        db = _make_db(_make_order())
        body = TrackingNumberUpdate(tracking_number="TRK123")
        with pytest.raises(HTTPException) as exc:
            update_order_tracking(
                "00000000-0000-0000-0000-000000000001", body,
                request=_make_request(TOKEN), user=None, db=db,
            )
        assert exc.value.status_code == 403

    def test_merchant_ok(self):
        from app.api.v1.orders import update_order_tracking, TrackingNumberUpdate

        db = _make_db(_make_order())
        body = TrackingNumberUpdate(tracking_number="TRK123", carrier="DHL")
        result = update_order_tracking(
            "00000000-0000-0000-0000-000000000001", body,
            request=_make_request(), user=_make_user(role="merchant", uid=MERCHANT_ID), db=db,
        )
        assert result.data["tracking_number"] == "TRK123"

    def test_not_found(self):
        from app.api.v1.orders import update_order_tracking, TrackingNumberUpdate

        db = _make_db(None)
        body = TrackingNumberUpdate(tracking_number="TRK123")
        with pytest.raises(HTTPException):
            update_order_tracking(
                "00000000-0000-0000-0000-000000000001", body,
                request=_make_request(TOKEN), user=None, db=db,
            )


class TestCancelOrder:
    def test_buyer_cancel_pending_ok(self):
        from app.api.v1.orders import cancel_order

        db = _make_db(_make_order())
        result = cancel_order("00000000-0000-0000-0000-000000000001", request=_make_request(TOKEN), user=None, db=db)
        assert result.data["status"] == "cancelled"

    def test_cancel_shipped_rejected(self):
        from app.api.v1.orders import cancel_order

        db = _make_db(_make_order(status="shipped"))
        with pytest.raises(HTTPException) as exc:
            cancel_order("00000000-0000-0000-0000-000000000001", request=_make_request(TOKEN), user=None, db=db)
        assert exc.value.status_code == 400


class TestConfirmReceipt:
    def test_buyer_confirm_shipped_ok(self):
        from app.api.v1.orders import confirm_receipt

        db = _make_db(_make_order(status="shipped"))
        result = confirm_receipt("00000000-0000-0000-0000-000000000001", request=_make_request(TOKEN), user=None, db=db)
        assert result.data["status"] == "completed"

    def test_confirm_pending_rejected(self):
        from app.api.v1.orders import confirm_receipt

        db = _make_db(_make_order())
        with pytest.raises(HTTPException) as exc:
            confirm_receipt("00000000-0000-0000-0000-000000000001", request=_make_request(TOKEN), user=None, db=db)
        assert exc.value.status_code == 400


class TestUpdateOrderTrade:
    """④定金核销 + ⑥发运单证数据更新（外贸履约补字段）。"""

    def test_buyer_forbidden(self):
        from app.api.v1.orders import update_order_trade, TradeDetailsUpdate

        db = _make_db(_make_order())
        body = TradeDetailsUpdate(incoterms="FOB")
        with pytest.raises(HTTPException) as exc:
            update_order_trade(
                "00000000-0000-0000-0000-000000000001", body,
                request=_make_request(TOKEN), user=None, db=db,
            )
        assert exc.value.status_code == 403

    def test_merchant_sets_incoterms_and_shipment(self):
        from app.api.v1.orders import update_order_trade, TradeDetailsUpdate

        order = _make_order(total_amount=1000.0)
        db = _make_db(order)
        body = TradeDetailsUpdate(incoterms="CIF", gross_weight=1200.0, volume=15.0, container_no="MSKU1234567", bl_number="BL20260913")
        result = update_order_trade(
            "00000000-0000-0000-0000-000000000001", body,
            request=_make_request(), user=_make_user(role="merchant", uid=MERCHANT_ID), db=db,
        )
        assert result.data["incoterms"] == "CIF"
        assert order.container_no == "MSKU1234567"
        db.commit.assert_called_once()

    def test_deposit_amount_auto_computed_from_ratio(self):
        from app.api.v1.orders import update_order_trade, TradeDetailsUpdate

        order = _make_order(total_amount=1000.0)
        db = _make_db(order)
        body = TradeDetailsUpdate(deposit_ratio=30.0)
        update_order_trade(
            "00000000-0000-0000-0000-000000000001", body,
            request=_make_request(), user=_make_user(), db=db,
        )
        assert order.deposit_amount == 300.0

    def test_deposit_amount_explicit_wins_over_ratio(self):
        from app.api.v1.orders import update_order_trade, TradeDetailsUpdate

        order = _make_order(total_amount=1000.0)
        db = _make_db(order)
        body = TradeDetailsUpdate(deposit_ratio=30.0, deposit_amount=500.0)
        update_order_trade(
            "00000000-0000-0000-0000-000000000001", body,
            request=_make_request(), user=_make_user(), db=db,
        )
        assert order.deposit_amount == 500.0


class TestExportProductionStage:
    """⑤生产跟单 IN_PRODUCTION 状态机：confirmed→in_production→shipped，不破坏直发。"""

    def test_confirmed_to_in_production_valid(self):
        from app.models.enums import OrderStatus

        assert OrderStatus.is_valid_transition("confirmed", "in_production")

    def test_in_production_to_shipped_valid_and_in_whitelist(self):
        from app.models.enums import OrderStatus, VALID_ORDER_STATUSES

        assert OrderStatus.is_valid_transition("in_production", "shipped")
        assert "in_production" in VALID_ORDER_STATUSES

    def test_direct_confirmed_to_shipped_still_valid(self):
        from app.models.enums import OrderStatus

        assert OrderStatus.is_valid_transition("confirmed", "shipped")

    def test_invalid_production_jump_rejected(self):
        from app.models.enums import OrderStatus

        assert not OrderStatus.is_valid_transition("in_production", "confirmed")
        assert not OrderStatus.is_valid_transition("pending", "in_production")
