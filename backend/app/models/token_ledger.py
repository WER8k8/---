"""Token 账本流水"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String

from app.core.database import UUID_TYPE, Base


class TokenLedgerEntry(Base):
    __tablename__ = "token_ledger_entries"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, nullable=False, index=True)
    delta = Column(Integer, nullable=False)  # 负数扣减，正数充值
    balance_after = Column(Integer, nullable=False)
    reason = Column(String(100), nullable=False)
    reference_id = Column(String(100))
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
