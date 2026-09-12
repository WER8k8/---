"""客户裂变推荐系统模型"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String

from app.core.database import UUID_TYPE, Base


class ReferralCode(Base):
    """邀请码"""
    __tablename__ = "referral_codes"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=False, index=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    total_referred = Column(Integer, default=0)
    total_earned = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class ReferralRecord(Base):
    """邀请记录"""
    __tablename__ = "referral_records"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    code_id = Column(UUID_TYPE, ForeignKey("referral_codes.id"), nullable=False, index=True)
    inviter_tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=False, index=True)
    invited_tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=False, index=True)
    status = Column(String(20), default="pending", nullable=False, index=True)  # pending/rewarded/expired
    reward_type = Column(String(50))
    reward_amount = Column(Integer, default=0)
    invited_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    rewarded_at = Column(DateTime(timezone=True))
    redemption_status = Column(String(32), nullable=True, index=True)
    redeemed_at = Column(DateTime(timezone=True))
    redeem_note = Column(String(500))
