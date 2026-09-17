"""余额支付服务单元测试 — preview / pay / 边界条件"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from app.services.payment_balance_service import (
    BalancePaymentResult,
    BalancePreviewResult,
    pay_order_with_balance,
    preview_balance_payment,
)


# ── preview_balance_payment ────────────────────────────────


class TestPreviewBalancePayment:
    def test_negative_amount_returns_error(self):
        result = preview_balance_payment("u1", -100, "CNY")
        assert result.success is False
        assert result.error == "金额必须大于 0"
        assert result.current_balance == 0

    def test_zero_amount_returns_error(self):
        result = preview_balance_payment("u1", 0, "CNY")
        assert result.success is False
        assert result.error == "金额必须大于 0"

    def test_sufficient_balance(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.payment_balance_service.get_wallet_summary",
            lambda uid: MagicMock(balances={"CNY": 5000}),
        )
        result = preview_balance_payment("u1", 3000, "CNY")
        assert result.success is True
        assert result.current_balance == 5000
        assert result.shortage is None

    def test_insufficient_balance(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.payment_balance_service.get_wallet_summary",
            lambda uid: MagicMock(balances={"CNY": 100}),
        )
        result = preview_balance_payment("u1", 500, "CNY")
        assert result.success is False
        assert result.error == "余额不足"
        assert result.shortage == 400

    def test_empty_wallet(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.payment_balance_service.get_wallet_summary",
            lambda uid: MagicMock(balances={}),
        )
        result = preview_balance_payment("u1", 100, "CNY")
        assert result.success is False
        assert result.current_balance == 0
        assert result.shortage == 100

    def test_multi_currency_ignores_other(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.payment_balance_service.get_wallet_summary",
            lambda uid: MagicMock(balances={"USD": 500, "CNY": 0}),
        )
        result = preview_balance_payment("u1", 100, "CNY")
        assert result.success is False
        assert result.shortage == 100


# ── pay_order_with_balance ─────────────────────────────────


class TestPayOrderWithBalance:
    def test_negative_amount(self):
        result = pay_order_with_balance("u1", "ord-1", -50, "CNY")
        assert result.success is False
        assert result.error == "金额必须大于 0"

    def test_zero_amount(self):
        result = pay_order_with_balance("u1", "ord-1", 0, "CNY")
        assert result.success is False
        assert result.error == "金额必须大于 0"

    def test_success(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.payment_balance_service.preview_balance_payment",
            lambda uid, amt, cur: BalancePreviewResult(
                success=True, user_id=uid, amount=amt, currency=cur, current_balance=amt
            ),
        )
        mock_tx = MagicMock()
        mock_tx.success = True
        mock_tx.tx_id = "tx-abc"
        mock_tx.operation = "withdraw"
        mock_tx.amount = 100
        mock_tx.currency = "CNY"
        mock_tx.balance_after = 900
        mock_tx.ref_type = "order"
        mock_tx.ref_id = "ord-1"
        mock_tx.created_at = "2024-01-01T00:00:00Z"
        monkeypatch.setattr(
            "app.services.payment_balance_service.withdraw",
            lambda **kw: mock_tx,
        )
        result = pay_order_with_balance("u1", "ord-1", 100, "CNY", tenant_id="t1")
        assert result.success is True
        assert result.user_id == "u1"
        assert result.order_id == "ord-1"
        assert result.amount == 100
        assert result.wallet_tx is not None
        assert result.wallet_tx["tx_id"] == "tx-abc"
        assert result.shortage is None
        assert result.error is None

    def test_preview_fails_returns_failure(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.payment_balance_service.preview_balance_payment",
            lambda uid, amt, cur: BalancePreviewResult(
                success=False,
                user_id=uid,
                amount=amt,
                currency=cur,
                current_balance=0,
                shortage=50,
                error="余额不足",
            ),
        )
        result = pay_order_with_balance("u1", "ord-1", 100, "CNY")
        assert result.success is False
        assert result.error == "余额不足"
        assert result.shortage == 50

    def test_withdraw_fails(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.payment_balance_service.preview_balance_payment",
            lambda uid, amt, cur: BalancePreviewResult(
                success=True, user_id=uid, amount=amt, currency=cur, current_balance=amt
            ),
        )
        mock_tx = MagicMock()
        mock_tx.success = False
        mock_tx.error = None
        monkeypatch.setattr(
            "app.services.payment_balance_service.withdraw",
            lambda **kw: mock_tx,
        )
        result = pay_order_with_balance("u1", "ord-1", 100, "CNY")
        assert result.success is False
        assert result.error == "扣款失败"

    def test_result_to_dict(self):
        result = BalancePaymentResult(
            success=True,
            user_id="u1",
            order_id="ord-1",
            amount=100,
            currency="CNY",
        )
        d = result.to_dict()
        assert d["success"] is True
        assert d["user_id"] == "u1"
        assert "created_at" in d


# ── _wallet_tx_to_dict ────────────────────────────────────


class TestWalletTxToDict:
    def test_converts_tx_result(self):
        from app.services.payment_balance_service import _wallet_tx_to_dict
        tx = MagicMock()
        tx.tx_id = "tx-1"
        tx.operation = "withdraw"
        tx.amount = 200
        tx.currency = "CNY"
        tx.balance_after = 800
        tx.ref_type = "order"
        tx.ref_id = "ord-2"
        tx.created_at = "2024-01-01T00:00:00Z"
        d = _wallet_tx_to_dict(tx)
        assert d["tx_id"] == "tx-1"
        assert d["operation"] == "withdraw"
        assert d["balance_after"] == 800
