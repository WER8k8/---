"""IPRoyal 长期养号支持：endpoint 新字段 + 成本记录 + 补充任务表

Revision ID: 043_iproyal_long_term_support
Revises: 042_egress_jit_provision
Create Date: 2026-06-04
"""

from alembic import op

def _uuid_col():
    """P0-B canonical：PG=native uuid（对齐模型 UUID_TYPE），其余=String(36)。"""
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID

        return UUID(as_uuid=False)
    return sa.String(36)

import sqlalchemy as sa

revision = "043_iproyal_long_term_support"
down_revision = "042_egress_jit_provision"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── egress_endpoints 新增字段 ──
    op.add_column(
        "egress_endpoints",
        sa.Column("iproyal_order_id", sa.Integer(), nullable=True, index=True),
    )
    op.add_column(
        "egress_endpoints",
        sa.Column("expire_date", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "egress_endpoints",
        sa.Column("renew_count", sa.Integer(), nullable=False, server_default="0"),
    )

    # ── 成本/续费记录表 ──
    op.create_table(
        "egress_cost_records",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column(
            "endpoint_id",
            _uuid_col(),
            sa.ForeignKey("egress_endpoints.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("provider", sa.String(50), nullable=False, server_default="iproyal"),
        sa.Column("operation", sa.String(20), nullable=False, server_default="purchase"),
        sa.Column("iproyal_order_id", sa.Integer(), nullable=True, index=True),
        sa.Column("quantity", sa.Integer(), server_default="1"),
        sa.Column("unit_price_cents", sa.Integer(), server_default="0"),
        sa.Column("total_price_cents", sa.Integer(), server_default="0"),
        sa.Column("currency", sa.String(10), server_default="USD"),
        sa.Column("plan_days", sa.Integer(), server_default="60"),
        sa.Column("raw_response", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # ── 缓冲池批量补充任务表 ──
    op.create_table(
        "egress_pool_replenish_jobs",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="queued",
        ),
        sa.Column("batch_size", sa.Integer(), server_default="5"),
        sa.Column("iproyal_order_id", sa.Integer(), nullable=True),
        sa.Column("endpoints_created", sa.Integer(), server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("egress_pool_replenish_jobs")
    op.drop_table("egress_cost_records")
    op.drop_column("egress_endpoints", "renew_count")
    op.drop_column("egress_endpoints", "expire_date")
    op.drop_column("egress_endpoints", "iproyal_order_id")
