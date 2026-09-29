# -*- coding: utf-8 -*-
"""135 — W5 第二层缺口 E 成本事件表（cost_events）

记录 AI Token、Browser 运行时、IP 代理、第三方 API 等直接成本流水，支撑租户单位经济与毛利核算。
down_revision = "134_w5_api_marketplace"
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "135_w5_cost_events"
down_revision: Union[str, None] = "134_w5_api_marketplace"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_names() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    from app.core.database import UUID_TYPE

    tables = _table_names()

    if "cost_events" not in tables:
        op.create_table(
            "cost_events",
            sa.Column("id", UUID_TYPE, primary_key=True),
            sa.Column("tenant_id", UUID_TYPE, nullable=True),
            sa.Column("cost_code", sa.String(length=80), nullable=False),
            sa.Column("cost_category", sa.String(length=30), nullable=False),
            sa.Column("amount", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
            sa.Column("quantity", sa.Float(), nullable=False, server_default="1.0"),
            sa.Column("unit", sa.String(length=30), nullable=False, server_default="unit"),
            sa.Column("subject_type", sa.String(length=50), nullable=True),
            sa.Column("subject_id", sa.String(length=100), nullable=True),
            sa.Column("provider", sa.String(length=50), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_cost_events_tenant_id", "cost_events", ["tenant_id"])
        op.create_index("ix_cost_events_cost_code", "cost_events", ["cost_code"])
        op.create_index("ix_cost_events_subject_id", "cost_events", ["subject_id"])
        op.create_index("idx_cost_events_tenant_occurred", "cost_events", ["tenant_id", "occurred_at"])
        op.create_index("idx_cost_events_category", "cost_events", ["cost_category", "cost_code"])


def downgrade() -> None:
    tables = _table_names()
    if "cost_events" in tables:
        op.drop_table("cost_events")
