# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""余额支付接入服务 — FEAT-余额支付

基于已有 user_wallet_service 提供余额支付能力。
提供订单余额支付与支付预览两个核心接口。

金额单位：最小货币单位（分），currency 为 ISO 4217 代码。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.services.user_wallet_service import (
    WalletTxResult,
    withdraw,
    get_wallet_summary,
)

logger = logging.getLogger("uj-admin.payment.balance")


# ── 数据结构 ──────────────────────────────────────────────


@dataclass
class BalancePaymentResult:
    """余额支付结果。"""
    success: bool
    user_id: str
    order_id: str
    amount: int
    currency: str
    wallet_tx: Optional[dict] = None
    shortage: Optional[int] = None
    error: Optional[str] = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    def to_dict(self) -> dict:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        result: dict = {
            "success": self.success,
            "user_id": self.user_id,
            "order_id": self.order_id,
            "amount": self.amount,
            "currency": self.currency,
            "created_at": self.created_at,
        }
        if self.wallet_tx is not None:
            result["wallet_tx"] = self.wallet_tx
        if self.shortage is not None:
            result["shortage"] = self.shortage
        if self.error is not None:
            result["error"] = self.error
        return result


@dataclass
class BalancePreviewResult:
    """余额支付预览结果。"""
    success: bool
    user_id: str
    amount: int
    currency: str
    current_balance: int
    shortage: Optional[int] = None
    error: Optional[str] = None
    def to_dict(self) -> dict:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        result: dict = {
            "success": self.success,
            "user_id": self.user_id,
            "amount": self.amount,
            "currency": self.currency,
            "current_balance": self.current_balance,
        }
        if self.shortage is not None:
            result["shortage"] = self.shortage
        if self.error is not None:
            result["error"] = self.error
        return result


# ── 内部工具 ──────────────────────────────────────────────


def _wallet_tx_to_dict(tx: WalletTxResult) -> dict:
    """将 WalletTxResult 转换为可序列化字典。"""
    return {
        "tx_id": tx.tx_id,
        "operation": tx.operation,
        "amount": tx.amount,
        "currency": tx.currency,
        "balance_after": tx.balance_after,
        "ref_type": tx.ref_type,
        "ref_id": tx.ref_id,
        "created_at": tx.created_at,
    }


# ── 公开接口 ──────────────────────────────────────────────


def preview_balance_payment(
    user_id: str,
    amount: int,
    currency: str,
) -> BalancePreviewResult:
    """预览余额支付：检查余额是否足够，不实际扣款。

    Args:
        user_id: 用户 ID
        amount: 需支付金额（最小货币单位）
        currency: ISO 4217 货币代码

    Returns:
        BalancePreviewResult: 包含当前余额、是否足够、差额等信息
    """
    if amount <= 0:
        logger.warning(
            "[balance-pay] 预览金额非法 user_id=%s amount=%d",
            user_id, amount,
        )
        return BalancePreviewResult(
            success=False,
            user_id=user_id,
            amount=amount,
            currency=currency,
            current_balance=0,
            error="金额必须大于 0",
        )

    summary = get_wallet_summary(user_id)
    current_balance = summary.balances.get(currency, 0)
    if current_balance >= amount:
        logger.info(
            "[balance-pay] 预览通过 user_id=%s amount=%d %s 余额=%d",
            user_id, amount, currency, current_balance,
        )
        return BalancePreviewResult(
            success=True,
            user_id=user_id,
            amount=amount,
            currency=currency,
            current_balance=current_balance,
        )

    shortage = amount - current_balance
    logger.info(
        "[balance-pay] 预览余额不足 user_id=%s amount=%d %s 余额=%d shortage=%d",
        user_id, amount, currency, current_balance, shortage,
    )
    return BalancePreviewResult(
        success=False,
        user_id=user_id,
        amount=amount,
        currency=currency,
        current_balance=current_balance,
        shortage=shortage,
        error="余额不足",
    )


def pay_order_with_balance(
    user_id: str,
    order_id: str,
    amount: int,
    currency: str,
    tenant_id: Optional[str] = None,
) -> BalancePaymentResult:
    """使用余额支付订单。

    流程：
    1. 校验金额合法性
    2. 预览余额是否充足
    3. 调用 wallet_service.withdraw 扣款
    4. 返回结构化结果（含 wallet_tx 信息）

    Args:
        user_id: 用户 ID
        order_id: 订单 ID
        amount: 需支付金额（最小货币单位）
        currency: ISO 4217 货币代码
        tenant_id: 租户 ID（可选，用于多租户场景）

    Returns:
        BalancePaymentResult: 支付结果，包含 wallet_tx 信息
    """
    if amount <= 0:
        logger.warning(
            "[balance-pay] 支付金额非法 user_id=%s order_id=%s amount=%d",
            user_id, order_id, amount,
        )
        return BalancePaymentResult(
            success=False,
            user_id=user_id,
            order_id=order_id,
            amount=amount,
            currency=currency,
            error="金额必须大于 0",
        )

    # 预览余额
    preview = preview_balance_payment(user_id, amount, currency)
    if not preview.success:
        logger.warning(
            "[balance-pay] 余额不足，拒绝支付 user_id=%s order_id=%s "
            "amount=%d %s shortage=%d",
            user_id, order_id, amount, currency, preview.shortage or 0,
        )
        return BalancePaymentResult(
            success=False,
            user_id=user_id,
            order_id=order_id,
            amount=amount,
            currency=currency,
            shortage=preview.shortage,
            error="余额不足",
        )

    # 扣款
    tx: WalletTxResult = withdraw(
        user_id=user_id,
        amount=amount,
        currency=currency,
        ref_type="order",
        ref_id=order_id,
    )
    if not tx.success:
        logger.error(
            "[balance-pay] 扣款失败 user_id=%s order_id=%s error=%s",
            user_id, order_id, tx.error,
        )
        return BalancePaymentResult(
            success=False,
            user_id=user_id,
            order_id=order_id,
            amount=amount,
            currency=currency,
            error=tx.error or "扣款失败",
        )

    logger.info(
        "[balance-pay] 支付成功 tx_id=%s user_id=%s order_id=%s "
        "amount=%d %s tenant_id=%s",
        tx.tx_id, user_id, order_id, amount, currency, tenant_id,
    )
    return BalancePaymentResult(
        success=True,
        user_id=user_id,
        order_id=order_id,
        amount=amount,
        currency=currency,
        wallet_tx=_wallet_tx_to_dict(tx),
    )
