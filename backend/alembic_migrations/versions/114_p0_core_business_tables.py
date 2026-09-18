"""114: P0-1 外贸履约/触点/经验核心表落库.

修复计划 A-1：probe 点名但 PG 缺失的核心业务表建成，业务写路径可落库。
与既有表边界见 app/models/trade_fulfillment.py 模块 docstring。

Revision ID: 114_p0_core_business_tables
Revises: 113_inquiries_phone_nullable
Create Date: 2026-09-18
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "114_p0_core_business_tables"
down_revision: Union[str, None] = "113_inquiries_phone_nullable"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _uuid_col():
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID

        return UUID(as_uuid=False)
    return sa.String(36)


def _now_default():
    return sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    op.create_table(
        "purchase_orders",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("tenant_id", _uuid_col(), nullable=True),
        sa.Column("order_id", _uuid_col(), sa.ForeignKey("orders.id"), nullable=True),
        sa.Column("po_number", sa.String(100), nullable=False),
        sa.Column("supplier_name", sa.String(200)),
        sa.Column("product_desc", sa.Text()),
        sa.Column("quantity", sa.Numeric(14, 3), server_default="0"),
        sa.Column("unit", sa.String(30), server_default="pcs"),
        sa.Column("unit_price", sa.Numeric(14, 4), server_default="0"),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("eta_date", sa.DateTime(timezone=True)),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_now_default()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=_now_default()),
    )
    op.create_index("ix_purchase_orders_po_number", "purchase_orders", ["po_number"], unique=True)
    op.create_index("ix_purchase_orders_order_id", "purchase_orders", ["order_id"])
    op.create_index("ix_purchase_orders_tenant_id", "purchase_orders", ["tenant_id"])
    op.create_index("ix_purchase_orders_status", "purchase_orders", ["status"])
    op.create_index("ix_purchase_orders_tenant_status", "purchase_orders", ["tenant_id", "status"])

    op.create_table(
        "logistics_shipments",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("tenant_id", _uuid_col(), nullable=True),
        sa.Column("order_id", _uuid_col(), sa.ForeignKey("orders.id"), nullable=True),
        sa.Column("purchase_order_id", _uuid_col(), sa.ForeignKey("purchase_orders.id"), nullable=True),
        sa.Column("tracking_no", sa.String(100)),
        sa.Column("carrier", sa.String(80)),
        sa.Column("origin_port", sa.String(100)),
        sa.Column("dest_port", sa.String(100)),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("shipped_at", sa.DateTime(timezone=True)),
        sa.Column("eta_at", sa.DateTime(timezone=True)),
        sa.Column("delivered_at", sa.DateTime(timezone=True)),
        sa.Column("payload_json", sa.Text(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_now_default()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=_now_default()),
    )
    op.create_index("ix_logistics_shipments_tracking_no", "logistics_shipments", ["tracking_no"])
    op.create_index("ix_logistics_shipments_order_id", "logistics_shipments", ["order_id"])
    op.create_index("ix_logistics_shipments_purchase_order_id", "logistics_shipments", ["purchase_order_id"])
    op.create_index("ix_logistics_shipments_tenant_id", "logistics_shipments", ["tenant_id"])
    op.create_index("ix_logistics_shipments_status", "logistics_shipments", ["status"])
    op.create_index("ix_logistics_shipments_tenant_status", "logistics_shipments", ["tenant_id", "status"])

    op.create_table(
        "whatsapp_messages",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("tenant_id", _uuid_col(), nullable=True),
        sa.Column("inquiry_id", _uuid_col(), sa.ForeignKey("inquiries.id"), nullable=True),
        sa.Column("lead_id", sa.String(64)),
        sa.Column("phone_e164", sa.String(24), nullable=False),
        sa.Column("direction", sa.String(12), nullable=False, server_default="outbound"),
        sa.Column("message_body", sa.Text(), nullable=False),
        sa.Column("template_id", sa.String(80)),
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
        sa.Column("external_msg_id", sa.String(120)),
        sa.Column("simulated", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("degraded", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("error", sa.Text()),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_now_default()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=_now_default()),
    )
    op.create_index("ix_whatsapp_messages_phone_e164", "whatsapp_messages", ["phone_e164"])
    op.create_index("ix_whatsapp_messages_inquiry_id", "whatsapp_messages", ["inquiry_id"])
    op.create_index("ix_whatsapp_messages_lead_id", "whatsapp_messages", ["lead_id"])
    op.create_index("ix_whatsapp_messages_tenant_id", "whatsapp_messages", ["tenant_id"])
    op.create_index("ix_whatsapp_messages_status", "whatsapp_messages", ["status"])
    op.create_index("ix_whatsapp_messages_external_msg_id", "whatsapp_messages", ["external_msg_id"])
    op.create_index(
        "ix_whatsapp_messages_tenant_dir",
        "whatsapp_messages",
        ["tenant_id", "direction", "created_at"],
    )

    op.create_table(
        "experience_records",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("tenant_id", _uuid_col(), nullable=True),
        sa.Column("source_type", sa.String(40), nullable=False, server_default="biz_outcome"),
        sa.Column("source_id", sa.String(100)),
        sa.Column("experience_type", sa.String(40), nullable=False, server_default="pattern"),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text()),
        sa.Column("score", sa.Numeric(6, 3), server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="raw"),
        sa.Column("metadata_json", sa.Text(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_now_default()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=_now_default()),
    )
    op.create_index("ix_experience_records_tenant_id", "experience_records", ["tenant_id"])
    op.create_index("ix_experience_records_source_type", "experience_records", ["source_type"])
    op.create_index("ix_experience_records_status", "experience_records", ["status"])
    op.create_index(
        "ix_experience_records_tenant_status", "experience_records", ["tenant_id", "status"]
    )
    op.create_index(
        "ix_experience_records_source", "experience_records", ["source_type", "source_id"]
    )

    op.create_table(
        "contact_events",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("tenant_id", _uuid_col(), nullable=True),
        sa.Column("inquiry_id", _uuid_col(), sa.ForeignKey("inquiries.id"), nullable=True),
        sa.Column("lead_id", sa.String(64)),
        sa.Column("channel", sa.String(30), nullable=False, server_default="web"),
        sa.Column("event_type", sa.String(40), nullable=False, server_default="view"),
        sa.Column("direction", sa.String(12), server_default="inbound"),
        sa.Column("summary", sa.Text()),
        sa.Column("payload_json", sa.Text(), server_default="{}"),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=_now_default()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_now_default()),
    )
    op.create_index("ix_contact_events_inquiry_id", "contact_events", ["inquiry_id"])
    op.create_index("ix_contact_events_lead_id", "contact_events", ["lead_id"])
    op.create_index("ix_contact_events_tenant_id", "contact_events", ["tenant_id"])
    op.create_index("ix_contact_events_channel", "contact_events", ["channel"])
    op.create_index("ix_contact_events_event_type", "contact_events", ["event_type"])
    op.create_index(
        "ix_contact_events_tenant_channel",
        "contact_events",
        ["tenant_id", "channel", "occurred_at"],
    )

    op.create_table(
        "knowledge_bases",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("tenant_id", _uuid_col(), nullable=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("kb_type", sa.String(40), nullable=False, server_default="product"),
        sa.Column("source", sa.String(30), server_default="manual"),
        sa.Column("doc_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_now_default()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=_now_default()),
    )
    op.create_index("ix_knowledge_bases_tenant_id", "knowledge_bases", ["tenant_id"])
    op.create_index("ix_knowledge_bases_kb_type", "knowledge_bases", ["kb_type"])
    op.create_index("ix_knowledge_bases_tenant_type", "knowledge_bases", ["tenant_id", "kb_type"])

    op.create_table(
        "invoices",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("tenant_id", _uuid_col(), nullable=True),
        sa.Column("order_id", _uuid_col(), sa.ForeignKey("orders.id"), nullable=True),
        sa.Column("invoice_no", sa.String(80), nullable=False),
        sa.Column("invoice_type", sa.String(30), nullable=False, server_default="pi"),
        sa.Column("buyer_name", sa.String(200)),
        sa.Column("buyer_tax_id", sa.String(64)),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("issued_at", sa.DateTime(timezone=True)),
        sa.Column("due_at", sa.DateTime(timezone=True)),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_now_default()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=_now_default()),
    )
    op.create_index("ix_invoices_invoice_no", "invoices", ["invoice_no"], unique=True)
    op.create_index("ix_invoices_order_id", "invoices", ["order_id"])
    op.create_index("ix_invoices_tenant_id", "invoices", ["tenant_id"])
    op.create_index("ix_invoices_invoice_type", "invoices", ["invoice_type"])
    op.create_index("ix_invoices_status", "invoices", ["status"])
    op.create_index("ix_invoices_tenant_status", "invoices", ["tenant_id", "status"])

    op.create_table(
        "payments",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("tenant_id", _uuid_col(), nullable=True),
        sa.Column("order_id", _uuid_col(), sa.ForeignKey("orders.id"), nullable=True),
        sa.Column("invoice_id", _uuid_col(), sa.ForeignKey("invoices.id"), nullable=True),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("method", sa.String(30), nullable=False, server_default="tt"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("paid_at", sa.DateTime(timezone=True)),
        sa.Column("reference_no", sa.String(100)),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_now_default()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=_now_default()),
    )
    op.create_index("ix_payments_order_id", "payments", ["order_id"])
    op.create_index("ix_payments_invoice_id", "payments", ["invoice_id"])
    op.create_index("ix_payments_tenant_id", "payments", ["tenant_id"])
    op.create_index("ix_payments_method", "payments", ["method"])
    op.create_index("ix_payments_status", "payments", ["status"])
    op.create_index("ix_payments_reference_no", "payments", ["reference_no"])
    op.create_index("ix_payments_tenant_status", "payments", ["tenant_id", "status"])

    op.create_table(
        "pipelines",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("tenant_id", _uuid_col(), nullable=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("pipeline_type", sa.String(30), nullable=False, server_default="sales"),
        sa.Column("stage_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("config_json", sa.Text(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_now_default()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=_now_default()),
    )
    op.create_index("ix_pipelines_tenant_id", "pipelines", ["tenant_id"])
    op.create_index("ix_pipelines_pipeline_type", "pipelines", ["pipeline_type"])
    op.create_index("ix_pipelines_tenant_type", "pipelines", ["tenant_id", "pipeline_type"])


def downgrade() -> None:
    for table in (
        "pipelines",
        "payments",
        "invoices",
        "knowledge_bases",
        "contact_events",
        "experience_records",
        "whatsapp_messages",
        "logistics_shipments",
        "purchase_orders",
    ):
        op.drop_table(table)
