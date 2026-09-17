# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Opportunity Model - CRM 销售机会（Lead → RFQ → Quote → Opportunity → Won）"""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base, UUID_TYPE
from app.models.soft_delete import SoftDeleteMixin


class Opportunity(SoftDeleteMixin, Base):
    """销售机会 — 记录从 RFQ/报价转化而来的商业机会与销售管道阶段。"""
    __tablename__ = "opportunities"
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    rfq_id = Column(UUID_TYPE, ForeignKey("rfqs.id"), nullable=True, index=True)
    quote_id = Column(UUID_TYPE, nullable=True, index=True)
    name = Column(String(300), nullable=False)
    company = Column(String(200), nullable=True, index=True)
    contact_name = Column(String(100), nullable=True)
    contact_email = Column(String(200), nullable=True)
    value = Column(Float, nullable=True)
    currency = Column(String(10), default="USD")
    stage = Column(String(50), nullable=False, default="Lead", index=True)
    probability = Column(Integer, nullable=False, default=10)  # 0-100
    expected_close_date = Column(DateTime(timezone=True), nullable=True)
    country = Column(String(100), nullable=True)
    application = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    assigned_to = Column(String(36), nullable=True, index=True)
    tenant_id = Column(String(36), nullable=True, index=True)
    company_id = Column(String(36), nullable=True, index=True)   # BUG-05 修复：CRM 管线落库关联企业 ID
    contact_id = Column(String(36), nullable=True)               # BUG-05 修复：关联联系人 ID
    created_by = Column(String(36), nullable=True)               # BUG-05 修复：创建人
    source = Column(String(50), nullable=True)  # rfq / quote / manual / outbound
    source_url = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    stages = relationship("OpportunityStage", back_populates="opportunity", cascade="all, delete-orphan")
    def __repr__(self):
        """__repr__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return f"<Opportunity(name={self.name}, stage={self.stage}, value={self.value})>"


class OpportunityStage(SoftDeleteMixin, Base):
    """机会阶段流转历史。"""
    __tablename__ = "opportunity_stages"
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    opportunity_id = Column(UUID_TYPE, ForeignKey("opportunities.id"), nullable=False, index=True)
    stage = Column(String(50), nullable=False)
    changed_by = Column(String(36), nullable=True)
    notes = Column(Text, nullable=True)
    changed_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    opportunity = relationship("Opportunity", back_populates="stages")
