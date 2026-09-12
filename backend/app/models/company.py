"""Company 360 - B2B 公司主数据 + 联系人 + 采购信号（Phase 3 地基）"""

from __future__ import annotations

import json
import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import TypeDecorator

from app.core.database import Base, UUID_TYPE
from app.models.soft_delete import SoftDeleteMixin


class JSONType(TypeDecorator):
    impl = Text
    def process_bind_param(self, value, dialect):
        """process_bind_param。

        参数说明：
        :param self: 参数 self
        :param value: 参数 value
        :param dialect: 参数 dialect
        :return: 返回处理结果。
        """
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        """process_result_value。

        参数说明：
        :param self: 参数 self
        :param value: 参数 value
        :param dialect: 参数 dialect
        :return: 返回处理结果。
        """
        if value is None:
            return {}
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {}


class Company(SoftDeleteMixin, Base):
    """B2B 买家公司主数据。"""
    __tablename__ = "companies"
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    name = Column(String(300), nullable=False, index=True)
    legal_name = Column(String(300), nullable=True)
    domain = Column(String(300), nullable=True, index=True)
    website = Column(String(500), nullable=True)
    country = Column(String(100), nullable=True, index=True)
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    sub_industry = Column(String(100), nullable=True)
    employees = Column(String(50), nullable=True)
    revenue_range = Column(String(50), nullable=True)
    linkedin = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    technologies = Column(Text, nullable=True)  # JSON
    certifications = Column(Text, nullable=True)  # JSON
    # 评分
    icp_score = Column(Integer, nullable=False, default=0)
    intent_score = Column(Integer, nullable=False, default=0)
    account_score = Column(Integer, nullable=False, default=0)
    # 数据来源可信度
    source = Column(String(50), nullable=True)
    source_url = Column(String(1000), nullable=True)
    retrieved_at = Column(DateTime(timezone=True), nullable=True)
    confidence = Column(Float, nullable=True)  # 0-1
    tenant_id = Column(String(36), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    contacts = relationship("CompanyContact", back_populates="company", cascade="all, delete-orphan")
    signals = relationship("CompanySignal", back_populates="company", cascade="all, delete-orphan")
    def __repr__(self):
        """__repr__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return f"<Company(name={self.name}, icp={self.icp_score}, intent={self.intent_score})>"


class CompanyContact(SoftDeleteMixin, Base):
    """公司联系人。"""
    __tablename__ = "company_contacts"
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID_TYPE, ForeignKey("companies.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    title = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    seniority = Column(String(50), nullable=True)
    email = Column(String(200), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    linkedin = Column(String(500), nullable=True)
    influence_score = Column(Integer, nullable=False, default=0)
    contactability_score = Column(Integer, nullable=False, default=0)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    company = relationship("Company", back_populates="contacts")


class CompanySignal(SoftDeleteMixin, Base):
    """公司采购信号（Intent 引擎输入）。"""
    __tablename__ = "company_signals"
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID_TYPE, ForeignKey("companies.id"), nullable=True, index=True)
    signal_type = Column(String(50), nullable=False, index=True)
    # WEBSITE_VISIT / PRODUCT_VIEW / DOCUMENT_DOWNLOAD / RFQ_SUBMITTED / NEW_PROJECT /
    # NEW_TENDER / NEW_FACTORY / NEW_WAREHOUSE / SEARCH_INTENT / AI_MENTION / ...
    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    source = Column(String(50), nullable=True)
    source_url = Column(String(1000), nullable=True)
    project_id = Column(String(36), nullable=True)
    product_id = Column(String(36), nullable=True)
    weight = Column(Integer, nullable=False, default=0)
    confidence = Column(Float, nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    company = relationship("Company", back_populates="signals")


class IntentEngineRun(SoftDeleteMixin, Base):
    """Intent 引擎计算记录（可审计）。"""
    __tablename__ = "intent_engine_runs"
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID_TYPE, ForeignKey("companies.id"), nullable=True, index=True)
    intent_score = Column(Integer, nullable=False, default=0)
    icp_score = Column(Integer, nullable=False, default=0)
    account_score = Column(Integer, nullable=False, default=0)
    signal_breakdown = Column(Text, nullable=True)  # JSON
    run_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
