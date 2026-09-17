# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Campaign / ABM 数据模型 — AI Outbound 序列（Phase 5）"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base, UUID_TYPE
from app.models.soft_delete import SoftDeleteMixin


class Campaign(SoftDeleteMixin, Base):
    """营销活动（Outbound / ABM / Nurture）。"""
    __tablename__ = "campaigns"
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    name = Column(String(300), nullable=False)
    campaign_type = Column(String(50), nullable=False, index=True)  # outbound / abm / nurture
    tier = Column(String(10), nullable=True)  # A / B / C
    status = Column(String(50), nullable=False, default="draft", index=True)  # draft / active / paused / completed
    target_count = Column(Integer, nullable=True)
    sent_count = Column(Integer, nullable=True, default=0)
    reply_count = Column(Integer, nullable=True, default=0)
    positive_reply_count = Column(Integer, nullable=True, default=0)
    tenant_id = Column(String(36), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    steps = relationship("CampaignStep", back_populates="campaign", cascade="all, delete-orphan")
    recipients = relationship("CampaignRecipient", back_populates="campaign", cascade="all, delete-orphan")


class CampaignStep(SoftDeleteMixin, Base):
    """活动序列步骤。"""
    __tablename__ = "campaign_steps"
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID_TYPE, ForeignKey("campaigns.id"), nullable=False, index=True)
    step_order = Column(Integer, nullable=False, default=0)
    day_delay = Column(Integer, nullable=False, default=0)  # 第几天执行
    subject = Column(String(500), nullable=True)
    content_template = Column(Text, nullable=True)
    action_type = Column(String(50), nullable=False, default="email")  # email / followup / case_study / final
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    campaign = relationship("Campaign", back_populates="steps")


class CampaignRecipient(SoftDeleteMixin, Base):
    """活动收件人。"""
    __tablename__ = "campaign_recipients"
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID_TYPE, ForeignKey("campaigns.id"), nullable=False, index=True)
    company_id = Column(String(36), nullable=True, index=True)
    contact_id = Column(String(36), nullable=True, index=True)
    email = Column(String(200), nullable=True)
    status = Column(String(50), nullable=False, default="pending", index=True)
    # pending / sent / delivered / bounced / replied / positive_reply / negative_reply / unsubscribed / stopped
    last_step_sent = Column(Integer, nullable=True, default=0)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    replied_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    campaign = relationship("Campaign", back_populates="recipients")


class CampaignEvent(SoftDeleteMixin, Base):
    """活动事件（发送/打开/点击/回复）。"""
    __tablename__ = "campaign_events"
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID_TYPE, ForeignKey("campaigns.id"), nullable=False, index=True)
    recipient_id = Column(UUID_TYPE, ForeignKey("campaign_recipients.id"), nullable=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # sent / delivered / opened / clicked / replied / bounced / unsubscribed
    step_order = Column(Integer, nullable=True)
    metadata_json = Column(Text, nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
