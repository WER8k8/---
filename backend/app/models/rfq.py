"""RFQ Model - 买家需求单（B2B 询价请求，Finder→RFQ 核心转化闭环）"""

from __future__ import annotations

import json
import uuid

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text
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


class RFQ(SoftDeleteMixin, Base):
    """RFQ 需求单 — 访客/买家提交的结构化询价请求。

    字段依据三份规划文档（Master Spec §12 / V3 OS §21 / Technical Spec §6），
    覆盖 公司/国家/联系人/项目/应用/产品/数量/技术要求/项目阶段/交期/贸易条款。
    """
    __tablename__ = "rfqs"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    # ── 公司 / 项目 ──
    company = Column(String(200), nullable=False, index=True)
    company_domain = Column(String(300), nullable=True)
    country = Column(String(100), nullable=False, index=True)
    city = Column(String(100), nullable=True)
    project = Column(String(300), nullable=True)
    project_type = Column(String(100), nullable=True)
    project_stage = Column(String(50), nullable=True, index=True)  # Concept/Design/Tender/Procurement/Construction
    application = Column(String(200), nullable=False)
    # ── 联系人 ──
    contact_name = Column(String(100), nullable=False)
    email = Column(String(200), nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    wechat = Column(String(100), nullable=True)
    # ── 商业 ──
    quantity = Column(Float, nullable=True)
    quantity_unit = Column(String(20), nullable=True)  # m2 / m3 / kg / pcs
    delivery_date = Column(Date, nullable=True)
    incoterm = Column(String(20), nullable=True)  # EXW/FOB/CIF/DAP/DDP
    currency = Column(String(10), default="USD")
    # ── 状态 / 评分 ──
    status = Column(String(50), nullable=False, default="pending", index=True)
    rfq_score = Column(Integer, nullable=False, default=0)
    score_label = Column(String(32), nullable=True, index=True)  # 评分档位标签，由 score_to_label 派生并持久化（清理项）
    intent_score = Column(Integer, nullable=False, default=0)
    # ── 来源与归因 ──
    source = Column(String(50), nullable=True)  # finder / product / rfq_form / calculator / contact
    source_channel = Column(String(50), nullable=True)
    source_url = Column(String(1000), nullable=True)
    session_id = Column(String(64), nullable=True, index=True)
    tenant_id = Column(String(36), nullable=True, index=True)
    assigned_to = Column(String(36), nullable=True, index=True)
    matched_product_ids = Column(Text, nullable=True)  # Finder 推荐产品 JSON
    # ── 其他 ──
    notes = Column(Text, nullable=True)
    requirements_json = Column(Text, nullable=True)  # 结构化技术要求 JSON
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    items = relationship("RFQItem", back_populates="rfq", cascade="all, delete-orphan")
    requirements = relationship("RFQRequirement", back_populates="rfq", cascade="all, delete-orphan")
    documents = relationship("RFQDocument", back_populates="rfq", cascade="all, delete-orphan")
    def __repr__(self):
        """__repr__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return f"<RFQ(company={self.company}, status={self.status}, score={self.rfq_score})>"


class RFQItem(SoftDeleteMixin, Base):
    """RFQ 明细 — 申请的产品行（Finder/产品页自动带入）"""
    __tablename__ = "rfq_items"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    rfq_id = Column(UUID_TYPE, ForeignKey("rfqs.id"), nullable=False, index=True)
    product_id = Column(UUID_TYPE, nullable=True, index=True)
    product_name = Column(String(200), nullable=False)
    product_slug = Column(String(200), nullable=True)
    quantity = Column(Float, nullable=True)
    unit = Column(String(20), nullable=True)
    dimensions = Column(Text, nullable=True)  # JSON
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    rfq = relationship("RFQ", back_populates="items")


class RFQRequirement(SoftDeleteMixin, Base):
    """RFQ 技术要求 — 结构化技术约束（防火/导热/标准/基材/环境等）"""
    __tablename__ = "rfq_requirements"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    rfq_id = Column(UUID_TYPE, ForeignKey("rfqs.id"), nullable=False, index=True)
    req_key = Column(String(100), nullable=False)
    req_label = Column(String(200), nullable=True)
    req_value = Column(Text, nullable=True)
    required = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    rfq = relationship("RFQ", back_populates="requirements")


class RFQDocument(SoftDeleteMixin, Base):
    """RFQ 附件 — BOQ / 图纸 / specification"""
    __tablename__ = "rfq_documents"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    rfq_id = Column(UUID_TYPE, ForeignKey("rfqs.id"), nullable=False, index=True)
    doc_type = Column(String(50), nullable=True)  # boq / drawing / specification
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    rfq = relationship("RFQ", back_populates="documents")
