# -*- coding: utf-8 -*-
"""130 — W5 归因两表 + orders 履约子状态列（修正设计稿 模块6 / 模块8.2 / Gate G5、G7）

- marketing_touchpoints：回站触点 append-only（platform/content/utm/external_post_id）。
- inquiry_attributions：询盘归因快照（first/last/conversion touch；snapshot 不可变）。
- orders 增列（可空向后兼容）：payment_stage / fulfillment_stage / document_stage
  （模块8.2：CRM 七阶段不扩，付款/生产/单证用子状态；shipment_stage 已在 128 落于
  logistics_shipments）。

设计：幂等（先 inspect 表/列/索引）。依赖：down_revision = 129_w5_harness_security_events
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "130_w5_attribution_fulfillment_substates"
down_revision: Union[str, None] = "129_w5_harness_security_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_names() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _column_names(table: str) -> set[str]:
    try:
        return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)}
    except Exception:  # noqa: BLE001
        return set()


def _index_names(table: str) -> set[str]:
    try:
        return {i["name"] for i in sa.inspect(op.get_bind()).get_indexes(table)}
    except Exception:  # noqa: BLE001
        return set()


def upgrade() -> None:
    from app.core.database import UUID_TYPE

    tables = _table_names()

    if "marketing_touchpoints" not in tables:
        op.create_table(
            "marketing_touchpoints",
            sa.Column("id", UUID_TYPE, primary_key=True),
            sa.Column("tenant_id", UUID_TYPE, nullable=False),
            sa.Column("visitor_id", sa.String(length=64), nullable=True),
            sa.Column("session_id", sa.String(length=64), nullable=True),
            sa.Column("channel", sa.String(length=40), nullable=True),
            sa.Column("platform", sa.String(length=40), nullable=True),
            sa.Column("campaign_id", sa.String(length=64), nullable=True),
            sa.Column("content_id", sa.String(length=64), nullable=True),
            sa.Column("landing_url", sa.String(length=500), nullable=True),
            sa.Column("referrer", sa.String(length=500), nullable=True),
            sa.Column("utm_source", sa.String(length=80), nullable=True),
            sa.Column("utm_medium", sa.String(length=80), nullable=True),
            sa.Column("utm_campaign", sa.String(length=120), nullable=True),
            sa.Column("utm_content", sa.String(length=120), nullable=True),
            sa.Column("utm_term", sa.String(length=120), nullable=True),
            sa.Column("gclid", sa.String(length=120), nullable=True),
            sa.Column("external_post_id", sa.String(length=150), nullable=True),
            sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_mtp_tenant_session", "marketing_touchpoints", ["tenant_id", "session_id"])
        op.create_index("ix_mtp_platform_content", "marketing_touchpoints", ["platform", "content_id"])
        op.create_index("ix_mtp_occurred", "marketing_touchpoints", ["occurred_at"])
        op.create_index("ix_marketing_touchpoints_tenant_id", "marketing_touchpoints", ["tenant_id"])

    if "inquiry_attributions" not in tables:
        op.create_table(
            "inquiry_attributions",
            sa.Column("id", UUID_TYPE, primary_key=True),
            sa.Column("inquiry_id", UUID_TYPE, sa.ForeignKey("inquiries.id"), nullable=False),
            sa.Column("tenant_id", UUID_TYPE, nullable=False),
            sa.Column("first_touch_id", UUID_TYPE, nullable=True),
            sa.Column("last_touch_id", UUID_TYPE, nullable=True),
            sa.Column("conversion_touch_id", UUID_TYPE, nullable=True),
            sa.Column("attribution_model", sa.String(length=30), nullable=False, server_default="last_touch"),
            sa.Column("snapshot_json", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_inq_attr_inquiry", "inquiry_attributions", ["inquiry_id"])
        op.create_index("ix_inquiry_attributions_tenant_id", "inquiry_attributions", ["tenant_id"])

    if "orders" in tables:
        cols = _column_names("orders")
        for name in ("payment_stage", "fulfillment_stage", "document_stage"):
            if name not in cols:
                op.add_column("orders", sa.Column(name, sa.String(length=30), nullable=True))
        indexes = _index_names("orders")
        for name, ix in (
            ("payment_stage", "ix_orders_payment_stage"),
            ("fulfillment_stage", "ix_orders_fulfillment_stage"),
            ("document_stage", "ix_orders_document_stage"),
        ):
            if name in _column_names("orders") and ix not in indexes:
                op.create_index(ix, "orders", [name])


def downgrade() -> None:
    tables = _table_names()
    if "orders" in tables:
        cols = _column_names("orders")
        indexes = _index_names("orders")
        for name, ix in (
            ("payment_stage", "ix_orders_payment_stage"),
            ("fulfillment_stage", "ix_orders_fulfillment_stage"),
            ("document_stage", "ix_orders_document_stage"),
        ):
            if name in cols:
                if ix in indexes:
                    op.drop_index(ix, table_name="orders")
                op.drop_column("orders", name)
    if "inquiry_attributions" in tables:
        indexes = _index_names("inquiry_attributions")
        for ix in ("ix_inquiry_attributions_tenant_id", "ix_inq_attr_inquiry"):
            if ix in indexes:
                op.drop_index(ix, table_name="inquiry_attributions")
        op.drop_table("inquiry_attributions")
    if "marketing_touchpoints" in tables:
        indexes = _index_names("marketing_touchpoints")
        for ix in (
            "ix_marketing_touchpoints_tenant_id",
            "ix_mtp_occurred",
            "ix_mtp_platform_content",
            "ix_mtp_tenant_session",
        ):
            if ix in indexes:
                op.drop_index(ix, table_name="marketing_touchpoints")
        op.drop_table("marketing_touchpoints")
