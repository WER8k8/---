"""add agent_commission_rules table

Revision ID: 034_agent_commission_rules
Revises: 033_add_site_analytics_events
Create Date: 2026-05-31
"""

from alembic import op

def _uuid_col():
    """P0-B canonical：PG=native uuid（对齐模型 UUID_TYPE），其余=String(36)。"""
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID

        return UUID(as_uuid=False)
    return sa.String(36)

import sqlalchemy as sa

revision = "034_agent_commission_rules"
down_revision = "033_add_site_analytics"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_commission_rules",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("payment_kind", sa.String(20), nullable=False),
        sa.Column("agent_level", sa.String(10), nullable=False),
        sa.Column("rate_bp", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("label", sa.String(100)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("payment_kind", "agent_level", name="uq_commission_rule_kind_level"),
    )
    op.create_index("ix_agent_commission_rules_payment_kind", "agent_commission_rules", ["payment_kind"])
    op.create_index("ix_agent_commission_rules_agent_level", "agent_commission_rules", ["agent_level"])


def downgrade() -> None:
    op.drop_table("agent_commission_rules")
