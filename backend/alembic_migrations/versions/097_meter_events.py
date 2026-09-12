"""meter events: meter_events append-only 计量表

Revision ID: 097
Revises: 096
Create Date: 2026-09-03

总纲 §4.6-8 / §6.6 P4 / 迁移总表 086（实现承接）：统一计量埋点。
- meter_events：append-only 计量事件表，7 类埋点动作（ai_generation / content_publish /
  lead_generated / rfq_created / api_call / export / video_job）。
- event_key 幂等去重；aggregated_at 标记并入计费账本（对账 pending 依据）。
- 红线 R3：计费复用既有四表（wallet/token_ledger/payment/finance_ledger），禁止重建——
  本迁移只建计量表，不建任何新的计费账本。
约束：tenant_id 关联 tenants.id（platform 级调用允许 NULL）；meter_type 受限 7 类。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

def _uuid_col():
    """P0-B canonical：PG=native uuid（对齐模型 UUID_TYPE），其余=String(36)。"""
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID

        return UUID(as_uuid=False)
    return sa.String(36)


# revision identifiers, used by Alembic.
revision: str = '097'
down_revision: Union[str, None] = '096'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

METER_TYPES = (
    'ai_generation', 'content_publish', 'lead_generated',
    'rfq_created', 'api_call', 'export', 'video_job',
)


def _table_exists(conn, name: str) -> bool:
    dialect = conn.dialect.name
    if dialect == "postgresql":
        row = conn.execute(
            sa.text("SELECT 1 FROM information_schema.tables WHERE table_name = :n"),
            {"n": name},
        ).fetchone()
    else:
        row = conn.execute(
            sa.text("SELECT 1 FROM sqlite_master WHERE type='table' AND name = :n"),
            {"n": name},
        ).fetchone()
    return row is not None


def upgrade() -> None:
    conn = op.get_bind()

    if not _table_exists(conn, "meter_events"):
        op.create_table(
            "meter_events",
            sa.Column("id", _uuid_col(), primary_key=True),
            sa.Column("tenant_id", _uuid_col(), sa.ForeignKey("tenants.id"), nullable=True),
            sa.Column("event_key", sa.String(length=100), nullable=True),
            sa.Column("meter_type", sa.String(length=30), nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("unit", sa.String(length=20), nullable=False, server_default="count"),
            sa.Column("token_delta", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("cost_cents", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("currency", sa.String(length=8), nullable=False, server_default="CNY"),
            sa.Column("source_ref_type", sa.String(length=30), nullable=True),
            sa.Column("source_ref_id", sa.String(length=100), nullable=True),
            sa.Column("model_name", sa.String(length=100), nullable=True),
            sa.Column("metadata", sa.Text(), nullable=True),
            sa.Column("aggregated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("event_key", name="uq_meter_events_event_key"),
            sa.CheckConstraint(
                "meter_type IN (" + ", ".join(f"'{m}'" for m in METER_TYPES) + ")",
                name="ck_meter_events_type",
            ),
        )
        op.create_index("ix_meter_events_tenant_occurred", "meter_events",
                        ["tenant_id", "occurred_at"])
        op.create_index("ix_meter_events_type_occurred", "meter_events",
                        ["meter_type", "occurred_at"])
        op.create_index("ix_meter_events_source", "meter_events",
                        ["source_ref_type", "source_ref_id"])
        op.create_index("ix_meter_events_occurred_at", "meter_events", ["occurred_at"])
        op.create_index("ix_meter_events_aggregated_at", "meter_events", ["aggregated_at"])

    if conn.dialect.name == "postgresql":
        op.execute(
            "COMMENT ON TABLE meter_events IS "
            "'统一计量埋点（总纲 §4.6-8）：append-only，7 类动作，周期汇总进既有计费四表。'"
        )


def downgrade() -> None:
    conn = op.get_bind()
    if _table_exists(conn, "meter_events"):
        op.drop_table("meter_events")
