# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""客户裂变推荐系统模型"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String

from app.core.database import UUID_TYPE, Base

# 邀请记录状态（模块12 轨6 反滥用）：
#   pending    —— 已注册待判定（未证明有效付费）
#   rewarded   —— 判定有效并已发放奖励（= 收入确认时点，轨6 计量）
#   fraud_hold —— 反滥用挂起：可疑邀请冻结，既不发放也不计量
#   expired    —— 超期作废
# 硬约束：fraud_hold **不可直接 rewarded**（防绕过风控直接确认收入），
#         必须先 release → pending，再经正常判定路径发放。
REFERRAL_STATUSES: tuple[str, ...] = ("pending", "rewarded", "fraud_hold", "expired")

REFERRAL_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "pending": ("rewarded", "fraud_hold", "expired"),
    "rewarded": ("fraud_hold",),        # 已发放后查实欺诈 → 挂起待处置
    "fraud_hold": ("pending", "expired"),  # 解封回待判定 / 判废
    "expired": (),
}


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
    status = Column(String(20), default="pending", nullable=False, index=True)  # pending/rewarded/fraud_hold/expired（见 REFERRAL_STATUSES）
    reward_type = Column(String(50))
    reward_amount = Column(Integer, default=0)
    invited_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    rewarded_at = Column(DateTime(timezone=True))
    redemption_status = Column(String(32), nullable=True, index=True)
    redeemed_at = Column(DateTime(timezone=True))
    redeem_note = Column(String(500))
