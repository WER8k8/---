"""用户钱包 — 余额账户与交易流水（BUG-04 修复：DB 落库唯一真相源）

原实现余额存于进程内存 dict + Redis 30 天 TTL，重启即清零、多 worker 数据分裂。
本模型将余额与流水持久化到数据库，行锁保证并发安全。
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint

from app.core.database import UUID_TYPE, Base


class WalletAccount(Base):
    """钱包账户：每用户每币种一行，balance 为唯一真相源。"""
    __tablename__ = "wallet_accounts"
    __table_args__ = (
        UniqueConstraint("user_id", "currency", name="uq_wallet_account_user_currency"),
    )
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(64), nullable=False, index=True)
    currency = Column(String(8), nullable=False, default="CNY")
    balance = Column(Integer, nullable=False, default=0)  # 最小货币单位（分）
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class WalletTransaction(Base):
    """钱包交易流水：deposit / withdraw / transfer / consume。"""
    __tablename__ = "wallet_transactions"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tx_id = Column(String(32), nullable=False, unique=True, index=True)
    user_id = Column(String(64), nullable=False, index=True)
    operation = Column(String(20), nullable=False)  # deposit/withdraw/transfer/consume
    amount = Column(Integer, nullable=False)
    currency = Column(String(8), nullable=False, default="CNY")
    balance_after = Column(Integer, nullable=False)
    to_user_id = Column(String(64), nullable=True)
    ref_type = Column(String(50), nullable=True)
    ref_id = Column(String(100), nullable=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
