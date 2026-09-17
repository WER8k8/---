# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""财务台账 — 营收/成本流水（MVP）"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.database import UUID_TYPE, Base


class FinanceLedgerEntry(Base):
    __tablename__ = "finance_ledger_entries"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    entry_type = Column(String(20), nullable=False, index=True)  # revenue | cost
    category = Column(String(50), nullable=False)  # subscription | token | ip | model_api | ...
    amount_cents = Column(Integer, nullable=False)  # 分，收入为正，成本为正数记录绝对值
    tenant_id = Column(UUID_TYPE, nullable=True, index=True)
    reference_id = Column(String(100))  # 订单/发票 ID
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
