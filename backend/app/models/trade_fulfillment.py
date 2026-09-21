# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""外贸履约/触点/经验核心表（修复计划 P0-1 / A-1）。

补建 probe 探表点名但 PG 缺失的业务写路径表：
purchase_orders / logistics_shipments / whatsapp_messages /
experience_records / contact_events / knowledge_bases /
invoices / payments / pipelines。

与既有表的边界（勿重复造）：
- 平台订阅支付 → payment_orders；业务订单收款 → payments
- 开票申请 → invoice_applications；贸易业务发票/PI → invoices
- 物流进度文案配置 → shipping_timeline；实际发运单 → logistics_shipments
- IM 路由/会话 → merchant_im_routing / im_messages；WhatsApp 外发记录 → whatsapp_messages
- 进化经验 → evolution_experiences；业务结果经验闭环 → experience_records
- AI 知识向量条目 → ai_knowledge_base；租户知识库目录 → knowledge_bases
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)

from app.core.database import Base, UUID_TYPE


def _now():
    return datetime.now(timezone.utc)


class PurchaseOrder(Base):
    """采购/生产跟单（7 步履约第 5 步）。"""
    __tablename__ = "purchase_orders"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, nullable=True, index=True)
    order_id = Column(UUID_TYPE, ForeignKey("orders.id"), nullable=True, index=True)
    po_number = Column(String(100), nullable=False, unique=True, index=True)
    supplier_name = Column(String(200))
    product_desc = Column(Text)
    quantity = Column(Numeric(14, 3), default=0)
    unit = Column(String(30), default="pcs")
    unit_price = Column(Numeric(14, 4), default=0)
    currency = Column(String(10), default="USD", nullable=False)
    status = Column(
        String(30), nullable=False, default="draft", index=True
    )  # draft/confirmed/producing/ready/shipped/cancelled
    eta_date = Column(DateTime(timezone=True))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    provenance_metadata = Column(JSON, nullable=True)

    __table_args__ = (Index("ix_purchase_orders_tenant_status", "tenant_id", "status"),)


class LogisticsShipment(Base):
    """发运/物流轨迹单（7 步履约第 6–7 步）。"""
    __tablename__ = "logistics_shipments"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, nullable=True, index=True)
    order_id = Column(UUID_TYPE, ForeignKey("orders.id"), nullable=True, index=True)
    purchase_order_id = Column(UUID_TYPE, ForeignKey("purchase_orders.id"), nullable=True, index=True)
    tracking_no = Column(String(100), index=True)
    carrier = Column(String(80))
    origin_port = Column(String(100))
    dest_port = Column(String(100))
    status = Column(
        String(30), nullable=False, default="pending", index=True
    )  # pending/booked/in_transit/delivered/exception
    shipped_at = Column(DateTime(timezone=True))
    eta_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    payload_json = Column(Text, default="{}")
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    provenance_metadata = Column(JSON, nullable=True)

    __table_args__ = (Index("ix_logistics_shipments_tenant_status", "tenant_id", "status"),)


class WhatsappMessage(Base):
    """WhatsApp 外发/回执消息记录（Trade AI / GoodJob 触达落库）。"""
    __tablename__ = "whatsapp_messages"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, nullable=True, index=True)
    inquiry_id = Column(UUID_TYPE, ForeignKey("inquiries.id"), nullable=True, index=True)
    lead_id = Column(String(64), nullable=True, index=True)
    phone_e164 = Column(String(24), nullable=False, index=True)
    direction = Column(String(12), nullable=False, default="outbound")  # outbound/inbound
    message_body = Column(Text, nullable=False)
    template_id = Column(String(80))
    status = Column(
        String(20), nullable=False, default="queued", index=True
    )  # queued/sent/delivered/read/failed
    external_msg_id = Column(String(120), index=True)
    simulated = Column(Boolean, default=False, nullable=False)
    degraded = Column(Boolean, default=False, nullable=False)
    error = Column(Text)
    sent_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    provenance_metadata = Column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_whatsapp_messages_tenant_dir", "tenant_id", "direction", "created_at"),
    )


class ExperienceRecord(Base):
    """业务结果→经验闭环记录（莫比乌斯焊线数据面）。"""
    __tablename__ = "experience_records"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, nullable=True, index=True)
    source_type = Column(
        String(40), nullable=False, default="biz_outcome", index=True
    )  # biz_outcome/task/proposal/executor
    source_id = Column(String(100), index=True)
    experience_type = Column(String(40), nullable=False, default="pattern", index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text)
    score = Column(Numeric(6, 3), default=0)
    status = Column(
        String(20), nullable=False, default="raw", index=True
    )  # raw/validated/applied/rejected
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    provenance_metadata = Column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_experience_records_tenant_status", "tenant_id", "status"),
        Index("ix_experience_records_source", "source_type", "source_id"),
    )


class ContactEvent(Base):
    """客户触点事件（询盘/邮件/WhatsApp/社媒/站内）。"""
    __tablename__ = "contact_events"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, nullable=True, index=True)
    inquiry_id = Column(UUID_TYPE, ForeignKey("inquiries.id"), nullable=True, index=True)
    lead_id = Column(String(64), nullable=True, index=True)
    channel = Column(
        String(30), nullable=False, default="web", index=True
    )  # web/email/whatsapp/phone/social/im
    event_type = Column(
        String(40), nullable=False, default="view", index=True
    )  # view/inquiry/message/reply/meeting/order
    direction = Column(String(12), default="inbound")  # inbound/outbound/internal
    summary = Column(Text)
    payload_json = Column(Text, default="{}")
    occurred_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)

    provenance_metadata = Column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_contact_events_tenant_channel", "tenant_id", "channel", "occurred_at"),
    )


class KnowledgeBase(Base):
    """租户知识库目录（内容条目仍落 ai_knowledge_base / 文件库）。"""
    __tablename__ = "knowledge_bases"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, nullable=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    kb_type = Column(
        String(40), nullable=False, default="product", index=True
    )  # product/faq/sop/compliance/research
    source = Column(String(30), default="manual")  # manual/import/ai
    doc_count = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    provenance_metadata = Column(JSON, nullable=True)

    __table_args__ = (Index("ix_knowledge_bases_tenant_type", "tenant_id", "kb_type"),)


class Invoice(Base):
    """贸易业务发票/PI（区别于平台开票申请 invoice_applications）。"""
    __tablename__ = "invoices"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, nullable=True, index=True)
    order_id = Column(UUID_TYPE, ForeignKey("orders.id"), nullable=True, index=True)
    invoice_no = Column(String(80), nullable=False, unique=True, index=True)
    invoice_type = Column(
        String(30), nullable=False, default="pi", index=True
    )  # pi/proforma/commercial/credit_note
    buyer_name = Column(String(200))
    buyer_tax_id = Column(String(64))
    amount = Column(Numeric(14, 2), nullable=False, default=0)
    currency = Column(String(10), default="USD", nullable=False)
    status = Column(
        String(20), nullable=False, default="draft", index=True
    )  # draft/issued/sent/paid/void
    issued_at = Column(DateTime(timezone=True))
    due_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    provenance_metadata = Column(JSON, nullable=True)

    __table_args__ = (Index("ix_invoices_tenant_status", "tenant_id", "status"),)


class BusinessPayment(Base):
    """业务订单收款流水（T/T、L/C 等；平台订阅支付仍用 payment_orders）。"""
    __tablename__ = "payments"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, nullable=True, index=True)
    order_id = Column(UUID_TYPE, ForeignKey("orders.id"), nullable=True, index=True)
    invoice_id = Column(UUID_TYPE, ForeignKey("invoices.id"), nullable=True, index=True)
    amount = Column(Numeric(14, 2), nullable=False, default=0)
    currency = Column(String(10), default="USD", nullable=False)
    method = Column(
        String(30), nullable=False, default="tt", index=True
    )  # tt/lc/western_union/escrow/platform/other
    status = Column(
        String(20), nullable=False, default="pending", index=True
    )  # pending/received/confirmed/refunded/failed
    paid_at = Column(DateTime(timezone=True))
    reference_no = Column(String(100), index=True)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    provenance_metadata = Column(JSON, nullable=True)

    __table_args__ = (Index("ix_payments_tenant_status", "tenant_id", "status"),)


class Pipeline(Base):
    """CRM/履约管线（漏斗定义；阶段明细可后续扩 pipeline_stages）。"""
    __tablename__ = "pipelines"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, nullable=True, index=True)
    name = Column(String(120), nullable=False)
    pipeline_type = Column(
        String(30), nullable=False, default="sales", index=True
    )  # sales/fulfillment/custom
    stage_count = Column(Integer, default=0, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    config_json = Column(Text, default="{}")
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    provenance_metadata = Column(JSON, nullable=True)

    __table_args__ = (Index("ix_pipelines_tenant_type", "tenant_id", "pipeline_type"),)
