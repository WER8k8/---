"""平台生存基金台账 — 仅超管收款账号；与租户 PaymentOrder / 代理分润完全隔离。"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text, UniqueConstraint

from app.core.database import UUID_TYPE, Base

WALLET_SCOPE = "platform_survival"


class PlatformSurvivalLedgerEntry(Base):
    """
    真钱流水：只记录 platform_survival 钱包。
    tenant_id 故意不存在 — 禁止与 L4 租户账单混账。
    """
    __tablename__ = "platform_survival_ledger_entries"
    __table_args__ = (
        UniqueConstraint(
            "payment_provider",
            "provider_payment_id",
            name="uq_platform_survival_provider_payment",
        ),
    )
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    wallet_scope = Column(String(32), nullable=False, default=WALLET_SCOPE, index=True)
    entry_type = Column(String(20), nullable=False, index=True)  # revenue | infra_cost | refund
    channel = Column(String(40), nullable=False, index=True)
    amount_minor = Column(Integer, nullable=False)
    currency = Column(String(10), nullable=False, default="CNY")
    amount_base_minor = Column(Integer, nullable=False)
    base_currency = Column(String(10), nullable=False, default="CNY")
    fx_rate_to_base = Column(String(24), nullable=False, default="1")
    payment_provider = Column(String(40), nullable=True, index=True)
    provider_payment_id = Column(String(200), nullable=True, index=True)
    status = Column(String(20), nullable=False, default="settled", index=True)
    opportunity_id = Column(String(100), nullable=True)
    ecc_verdict = Column(String(20), nullable=True)
    recorded_by_user_id = Column(UUID_TYPE, nullable=True)
    note = Column(Text)
    recorded_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
