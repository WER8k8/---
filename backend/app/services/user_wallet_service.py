# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""用户钱包服务（WALLET-SVC）

BUG-04 修复：余额与流水落库（wallet_accounts / wallet_transactions），
DB 为唯一真相源，行锁（with_for_update）保证并发安全；
原「进程内存 dict + Redis 30 天 TTL」实现已废弃——重启清零、
多 worker 分裂、Redis 故障静默降级三类资损场景全部消除。

金额单位：最小货币单位（分），currency 为 ISO 4217 代码。
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError

log = logging.getLogger("uj-admin.wallet")

# ── 数据结构 ──────────────────────────────────────────────


@dataclass
class WalletTxResult:
    """钱包操作的结构化返回。"""
    success: bool
    tx_id: str
    user_id: str
    operation: str  # deposit / withdraw / transfer
    amount: int
    currency: str
    balance_after: int
    ref_type: Optional[str] = None
    ref_id: Optional[str] = None
    to_user_id: Optional[str] = None
    error: Optional[str] = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class WalletSummary:
    """钱包摘要。"""
    user_id: str
    balances: dict[str, int]  # {currency: amount}
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    def to_dict(self) -> dict:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "user_id": self.user_id,
            "balances": self.balances,
            "updated_at": self.updated_at,
        }


class WalletUnavailableError(RuntimeError):
    """DB 不可用时抛出（fail-closed，不再静默降级到内存）。"""


def _session():
    """_session。
    :return: 返回处理结果。
    """
    from app.db.session import SessionLocal
    return SessionLocal()


def _get_or_create_account(db, user_id: str, currency: str, lock: bool = True):
    """_get_or_create_account。

    参数说明：
    :param db: 参数 db
    :param user_id: 参数 user_id
    :param currency: 参数 currency
    :param lock: 参数 lock
    :return: 返回处理结果。
    """
    from app.models.wallet import WalletAccount
    query = db.query(WalletAccount).filter(
        WalletAccount.user_id == user_id, WalletAccount.currency == currency
    )
    if lock:
        query = query.with_for_update()
    account = query.first()
    if account is None:
        account = WalletAccount(user_id=user_id, currency=currency, balance=0)
        db.add(account)
        db.flush()
    return account


def _db_get_balance(db, user_id: str, currency: str) -> int:
    """_db_get_balance。

    参数说明：
    :param db: 参数 db
    :param user_id: 参数 user_id
    :param currency: 参数 currency
    :return: 返回处理结果。
    """
    from app.models.wallet import WalletAccount
    row = (
        db.query(WalletAccount.balance)
        .filter(WalletAccount.user_id == user_id, WalletAccount.currency == currency)
        .first()
    )
    return int(row[0]) if row else 0


def _gen_tx_id() -> str:
    """_gen_tx_id。
    :return: 返回处理结果。
    """
    return uuid.uuid4().hex[:16]


# ── 业务接口 ──────────────────────────────────────────────


def get_wallet_summary(user_id: str) -> WalletSummary:
    """查询用户钱包摘要（所有币种余额，DB 读取）。"""
    from app.models.wallet import WalletAccount
    try:
        with _session() as db:
            rows = (
                db.query(WalletAccount.currency, WalletAccount.balance)
                .filter(WalletAccount.user_id == user_id)
                .all()
            )
            balances = {cur: int(bal) for cur, bal in rows}
    except SQLAlchemyError as exc:
        log.error("[wallet] 摘要查询 DB 失败 fail-closed user=%s: %s", user_id, exc)
        raise WalletUnavailableError("钱包服务暂时不可用") from exc
    log.info("[wallet] 查询摘要 user_id=%s 币种数=%d", user_id, len(balances))
    return WalletSummary(user_id=user_id, balances=balances)


def deposit(
    user_id: str,
    amount: int,
    currency: str,
    ref_type: Optional[str] = None,
    ref_id: Optional[str] = None,
) -> WalletTxResult:
    """充值（入账）。DB 事务 + 行锁。"""
    if amount <= 0:
        log.warning("[wallet] 充值金额非法 user_id=%s amount=%d", user_id, amount)
        return _fail_result("deposit", user_id, amount, currency, "金额必须大于 0")

    from app.models.wallet import WalletTransaction
    tx_id = _gen_tx_id()
    try:
        with _session() as db:
            account = _get_or_create_account(db, user_id, currency)
            account.balance = int(account.balance or 0) + amount
            new_balance = int(account.balance)
            db.add(
                WalletTransaction(
                    tx_id=tx_id,
                    user_id=user_id,
                    operation="deposit",
                    amount=amount,
                    currency=currency,
                    balance_after=new_balance,
                    ref_type=ref_type,
                    ref_id=ref_id,
                )
            )
            db.commit()
    except SQLAlchemyError as exc:
        log.error("[wallet] 充值 DB 失败 fail-closed user=%s: %s", user_id, exc)
        return _fail_result("deposit", user_id, amount, currency, "钱包服务暂时不可用")

    log.info(
        "[wallet] 充值成功 tx_id=%s user_id=%s amount=%d %s 余额=%d",
        tx_id, user_id, amount, currency, new_balance,
    )
    return WalletTxResult(
        success=True,
        tx_id=tx_id,
        user_id=user_id,
        operation="deposit",
        amount=amount,
        currency=currency,
        balance_after=new_balance,
        ref_type=ref_type,
        ref_id=ref_id,
    )


def withdraw(
    user_id: str,
    amount: int,
    currency: str,
    ref_type: Optional[str] = None,
    ref_id: Optional[str] = None,
) -> WalletTxResult:
    """提现（出账），余额不足时拒绝。DB 事务 + 行锁。"""
    if amount <= 0:
        log.warning("[wallet] 提现金额非法 user_id=%s amount=%d", user_id, amount)
        return _fail_result("withdraw", user_id, amount, currency, "金额必须大于 0")

    from app.models.wallet import WalletTransaction
    tx_id = _gen_tx_id()
    try:
        with _session() as db:
            account = _get_or_create_account(db, user_id, currency)
            current = int(account.balance or 0)
            if current < amount:
                db.rollback()
                log.warning(
                    "[wallet] 余额不足 user_id=%s 请求=%d 可用=%d %s",
                    user_id, amount, current, currency,
                )
                return _fail_result("withdraw", user_id, amount, currency, "余额不足")
            account.balance = current - amount
            new_balance = int(account.balance)
            db.add(
                WalletTransaction(
                    tx_id=tx_id,
                    user_id=user_id,
                    operation="withdraw",
                    amount=amount,
                    currency=currency,
                    balance_after=new_balance,
                    ref_type=ref_type,
                    ref_id=ref_id,
                )
            )
            db.commit()
    except SQLAlchemyError as exc:
        log.error("[wallet] 提现 DB 失败 fail-closed user=%s: %s", user_id, exc)
        return _fail_result("withdraw", user_id, amount, currency, "钱包服务暂时不可用")

    log.info(
        "[wallet] 提现成功 tx_id=%s user_id=%s amount=%d %s 余额=%d",
        tx_id, user_id, amount, currency, new_balance,
    )
    return WalletTxResult(
        success=True,
        tx_id=tx_id,
        user_id=user_id,
        operation="withdraw",
        amount=amount,
        currency=currency,
        balance_after=new_balance,
        ref_type=ref_type,
        ref_id=ref_id,
    )


def transfer(
    from_user_id: str,
    to_user_id: str,
    amount: int,
    currency: str,
    ref_type: Optional[str] = None,
    ref_id: Optional[str] = None,
) -> WalletTxResult:
    """转账，余额不足时拒绝。DB 单事务 + 双行锁（固定加锁顺序防死锁）。"""
    if amount <= 0:
        log.warning("[wallet] 转账金额非法 from=%s amount=%d", from_user_id, amount)
        return _fail_result("transfer", from_user_id, amount, currency, "金额必须大于 0")

    if from_user_id == to_user_id:
        log.warning("[wallet] 不能给自己转账 user_id=%s", from_user_id)
        return _fail_result(
            "transfer", from_user_id, amount, currency, "不能给自己转账"
        )

    from app.models.wallet import WalletTransaction
    tx_id = _gen_tx_id()
    try:
        with _session() as db:
            # 固定按 (user_id, currency) 排序加锁，避免双账户互转死锁
            first, second = sorted([from_user_id, to_user_id])
            _get_or_create_account(db, first, currency)
            _get_or_create_account(db, second, currency)
            from_account = _get_or_create_account(db, from_user_id, currency)
            current = int(from_account.balance or 0)
            if current < amount:
                db.rollback()
                log.warning(
                    "[wallet] 转账余额不足 from=%s 请求=%d 可用=%d %s",
                    from_user_id, amount, current, currency,
                )
                return _fail_result(
                    "transfer", from_user_id, amount, currency, "余额不足"
                )
            from_account.balance = current - amount
            new_balance = int(from_account.balance)
            to_account = _get_or_create_account(db, to_user_id, currency)
            to_account.balance = int(to_account.balance or 0) + amount
            db.add(
                WalletTransaction(
                    tx_id=tx_id,
                    user_id=from_user_id,
                    operation="transfer",
                    amount=amount,
                    currency=currency,
                    balance_after=new_balance,
                    to_user_id=to_user_id,
                    ref_type=ref_type,
                    ref_id=ref_id,
                )
            )
            db.commit()
    except SQLAlchemyError as exc:
        log.error("[wallet] 转账 DB 失败 fail-closed from=%s: %s", from_user_id, exc)
        return _fail_result("transfer", from_user_id, amount, currency, "钱包服务暂时不可用")

    log.info(
        "[wallet] 转账成功 tx_id=%s from=%s to=%s amount=%d %s",
        tx_id, from_user_id, to_user_id, amount, currency,
    )
    return WalletTxResult(
        success=True,
        tx_id=tx_id,
        user_id=from_user_id,
        operation="transfer",
        amount=amount,
        currency=currency,
        balance_after=new_balance,
        ref_type=ref_type,
        ref_id=ref_id,
        to_user_id=to_user_id,
    )


def get_transactions(user_id: str, limit: int = 50) -> list[dict]:
    """查询用户交易记录（DB）。"""
    from app.models.wallet import WalletTransaction
    try:
        with _session() as db:
            rows = (
                db.query(WalletTransaction)
                .filter(WalletTransaction.user_id == user_id)
                .order_by(WalletTransaction.created_at.desc())
                .limit(max(1, min(int(limit), 500)))
                .all()
            )
            return [
                {
                    "tx_id": r.tx_id,
                    "user_id": r.user_id,
                    "operation": r.operation,
                    "amount": int(r.amount or 0),
                    "currency": r.currency,
                    "balance_after": int(r.balance_after or 0),
                    "to_user_id": r.to_user_id,
                    "ref_type": r.ref_type,
                    "ref_id": r.ref_id,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ]
    except SQLAlchemyError as exc:
        log.error("[wallet] 交易记录查询 DB 失败 user=%s: %s", user_id, exc)
        return []


def _tx_data_source() -> str:
    """Honest store label."""
    return "db"


def _parse_tx_created_at(raw: object) -> datetime | None:
    """_parse_tx_created_at。

    参数说明：
    :param raw: 参数 raw
    :return: 返回处理结果。
    """
    if raw is None:
        return None
    if isinstance(raw, datetime):
        dt = raw
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    text = str(raw).strip()
    if not text:
        return None
    try:
        # support trailing Z
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def get_monthly_stats(user_id: str) -> dict:
    """当月充值/消费/提现汇总（DB 聚合）。"""
    from sqlalchemy import func
    from app.models.wallet import WalletTransaction
    now = datetime.now(timezone.utc)
    month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    try:
        with _session() as db:
            rows = (
                db.query(
                    WalletTransaction.operation,
                    func.coalesce(func.sum(WalletTransaction.amount), 0),
                )
                .filter(
                    WalletTransaction.user_id == user_id,
                    WalletTransaction.created_at >= month_start,
                )
                .group_by(WalletTransaction.operation)
                .all()
            )
    except SQLAlchemyError as exc:
        log.error("[wallet] 月度统计 DB 失败 user=%s: %s", user_id, exc)
        return {
            "user_id": user_id,
            "year_month": f"{now.year:04d}-{now.month:02d}",
            "deposit": 0,
            "consume": 0,
            "withdraw": 0,
            "data_source": _tx_data_source(),
            "error": "db_unavailable",
        }

    deposit_cents = 0
    consume_cents = 0
    withdraw_cents = 0
    for op, total in rows:
        op = str(op or "")
        total = int(total or 0)
        if total <= 0:
            continue
        if op == "deposit":
            deposit_cents += total
        elif op == "withdraw":
            withdraw_cents += total
        elif op in ("consume", "transfer"):
            consume_cents += total

    return {
        "user_id": user_id,
        "year_month": f"{now.year:04d}-{now.month:02d}",
        "deposit": deposit_cents,
        "consume": consume_cents,
        "withdraw": withdraw_cents,
        "data_source": _tx_data_source(),
    }


# ── 内部工具 ──────────────────────────────────────────────


def _fail_result(
    operation: str,
    user_id: str,
    amount: int,
    currency: str,
    error: str,
) -> WalletTxResult:
    """构造失败结果（余额尽力读取 DB，读不到填 0）。"""
    try:
        with _session() as db:
            balance = _db_get_balance(db, user_id, currency)
    except SQLAlchemyError:
        balance = 0
    return WalletTxResult(
        success=False,
        tx_id="",
        user_id=user_id,
        operation=operation,
        amount=amount,
        currency=currency,
        balance_after=balance,
        error=error,
    )
