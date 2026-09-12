"""多级代理分润规则表（首单 / 续费 × 层级）。"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String, UniqueConstraint

from app.core.database import UUID_TYPE, Base


class AgentCommissionRule(Base):
    __tablename__ = "agent_commission_rules"
    __table_args__ = (
        UniqueConstraint("payment_kind", "agent_level", name="uq_commission_rule_kind_level"),
    )
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    payment_kind = Column(String(20), nullable=False, index=True)  # first | renewal
    agent_level = Column(String(10), nullable=False, index=True)  # l5..l1
    rate_bp = Column(Integer, nullable=False, default=0)  # 订单金额万分比
    label = Column(String(100))
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
