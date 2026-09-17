# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Project Intelligence 数据模型 — 项目/招标信号（Phase 4）"""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base, UUID_TYPE
from app.models.soft_delete import SoftDeleteMixin


class Project(SoftDeleteMixin, Base):
    """公开项目/招标情报。"""
    __tablename__ = "projects"
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    name = Column(String(500), nullable=False, index=True)
    company = Column(String(300), nullable=True)
    company_id = Column(String(36), nullable=True, index=True)
    country = Column(String(100), nullable=True, index=True)
    city = Column(String(100), nullable=True)
    project_type = Column(String(100), nullable=True)  # Factory/Warehouse/Data Center/Commercial/Industrial
    stage = Column(String(50), nullable=True, index=True)  # Announced/Design/Tender/Procurement/Construction
    estimated_value = Column(Float, nullable=True)
    currency = Column(String(10), default="USD")
    requirements = Column(Text, nullable=True)  # 材料/标准/性能 JSON
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    # 产品匹配
    matched_product_ids = Column(Text, nullable=True)  # JSON
    product_match_score = Column(Integer, nullable=True)
    # 来源可信度
    source = Column(String(50), nullable=True)
    source_url = Column(String(1000), nullable=True)
    retrieved_at = Column(DateTime(timezone=True), nullable=True)
    confidence = Column(Float, nullable=True)  # 0-1
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    signals = relationship("ProjectSignal", back_populates="project", cascade="all, delete-orphan")


class ProjectSignal(SoftDeleteMixin, Base):
    """项目信号（招标/扩建/新建等）。"""
    __tablename__ = "project_signals"
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID_TYPE, ForeignKey("projects.id"), nullable=False, index=True)
    signal_type = Column(String(50), nullable=False, index=True)  # NEW_PROJECT / NEW_TENDER / NEW_FACTORY / NEW_WAREHOUSE
    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    source = Column(String(50), nullable=True)
    source_url = Column(String(1000), nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    project = relationship("Project", back_populates="signals")
