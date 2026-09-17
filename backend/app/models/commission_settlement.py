# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""代理分润结算单"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.database import UUID_TYPE, Base


class AgentCommissionSettlement(Base):
    __tablename__ = "agent_commission_settlements"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_node_id = Column(UUID_TYPE, nullable=False, index=True)
    period = Column(String(20), nullable=False, index=True)  # YYYY-MM
    revenue_cents = Column(Integer, default=0)
    commission_cents = Column(Integer, default=0)
    commission_rate_bp = Column(Integer, default=1000)  # 万分比，1000=10%
    status = Column(String(20), default="pending")  # pending | settled | cancelled
    note = Column(Text)
    settled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
