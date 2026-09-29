# -*- coding: utf-8 -*-
"""128 — W5 物流真实化：tracking_events + tracking_accounts + shipment_stage 增列

背景（修正设计稿 模块8.4/8.5 / Gate G8）：
- tracking_events：真实承运商事件落库，(provider, external_event_id) 幂等唯一，
  规范化状态不可回退（秩序守卫在服务层）。
- tracking_accounts：Provider 账户登记（凭据引用不落明文）。
- logistics_shipments 增列 shipment_stage（履约子状态，booking/shipped/in_transit/
  delivered/exception），由真实事件推导；无事件时保持 NULL = tracking_unavailable。

设计：幂等（先 inspect 表/列/索引），与 119~127 同风格。
依赖：down_revision = 127_w5_boq_pipeline
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "128_w5_tracking_events"
down_revision: Union[str, None] = "127_w5_boq_pipeline"
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

    if "tracking_events" not in tables:
        op.create_table(
            "tracking_events",
            sa.Column("id", UUID_TYPE, primary_key=True),
            sa.Column("shipment_id", UUID_TYPE, sa.ForeignKey("logistics_shipments.id"), nullable=True),
            sa.Column("tracking_no", sa.String(length=100), nullable=True),
            sa.Column("tenant_id", UUID_TYPE, nullable=True),
            sa.Column("provider", sa.String(length=40), nullable=False),
            sa.Column("external_event_id", sa.String(length=150), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False, server_default="unknown"),
            sa.Column("location", sa.String(length=200), nullable=True),
            sa.Column("event_time", sa.DateTime(timezone=True), nullable=True),
            sa.Column("raw_payload_ref", sa.String(length=255), nullable=True),
            sa.Column("normalized_payload", sa.JSON(), nullable=True),
            sa.Column("raw_payload", sa.JSON(), nullable=True),
            sa.Column("source", sa.String(length=20), nullable=False, server_default="provider"),
            sa.Column("operator", sa.String(length=100), nullable=True),
            sa.Column("operator_reason", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("provider", "external_event_id", name="uq_tracking_events_provider_event"),
        )
        op.create_index("ix_tracking_events_shipment", "tracking_events", ["shipment_id"])
        op.create_index("ix_tracking_events_tracking_no", "tracking_events", ["tracking_no"])
        op.create_index("ix_tracking_events_tenant_id", "tracking_events", ["tenant_id"])

    if "tracking_accounts" not in tables:
        op.create_table(
            "tracking_accounts",
            sa.Column("id", UUID_TYPE, primary_key=True),
            sa.Column("tenant_id", UUID_TYPE, nullable=True),
            sa.Column("provider", sa.String(length=40), nullable=False),
            sa.Column("account_ref", sa.String(length=150), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="not_configured"),
            sa.Column("last_health_check_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("tenant_id", "provider", name="uq_tracking_accounts_tenant_provider"),
        )
        op.create_index("ix_tracking_accounts_tenant_id", "tracking_accounts", ["tenant_id"])

    if "logistics_shipments" in tables and "shipment_stage" not in _column_names("logistics_shipments"):
        op.add_column(
            "logistics_shipments",
            sa.Column("shipment_stage", sa.String(length=30), nullable=True),
        )


def downgrade() -> None:
    tables = _table_names()
    if "logistics_shipments" in tables and "shipment_stage" in _column_names("logistics_shipments"):
        op.drop_column("logistics_shipments", "shipment_stage")
    if "tracking_accounts" in tables:
        indexes = _index_names("tracking_accounts")
        if "ix_tracking_accounts_tenant_id" in indexes:
            op.drop_index("ix_tracking_accounts_tenant_id", table_name="tracking_accounts")
        op.drop_table("tracking_accounts")
    if "tracking_events" in tables:
        indexes = _index_names("tracking_events")
        for ix in ("ix_tracking_events_tenant_id", "ix_tracking_events_tracking_no", "ix_tracking_events_shipment"):
            if ix in indexes:
                op.drop_index(ix, table_name="tracking_events")
        op.drop_table("tracking_events")
