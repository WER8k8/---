"""UBrain Accio：租户记忆 + 采购商候选线索

Revision ID: 025_ubrain_accio_sales
Revises: 024_deerflow_jobs
"""

import sqlalchemy as sa
from alembic import op

def _uuid_col():
    """P0-B canonical：PG=native uuid（对齐模型 UUID_TYPE），其余=String(36)。"""
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID

        return UUID(as_uuid=False)
    return sa.String(36)


revision = "025_ubrain_accio_sales"
down_revision = "024_deerflow_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ubrain_tenant_memory",
        sa.Column("tenant_id", _uuid_col(), primary_key=True),
        sa.Column("memory_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("tool_use_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
    )
    op.create_table(
        "buyer_prospect_leads",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("tenant_id", _uuid_col(), nullable=False),
        sa.Column("region_label", sa.String(80), nullable=False),
        sa.Column("country_code", sa.String(8), nullable=True),
        sa.Column("buyer_type", sa.String(40), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("fit_score", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("suggested_channel", sa.String(40), server_default="email"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("outreach_draft", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="discovered"),
        sa.Column("source_tool", sa.String(64), server_default="find_buyers"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
    )
    op.create_index(
        "ix_buyer_prospect_tenant_status",
        "buyer_prospect_leads",
        ["tenant_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_buyer_prospect_tenant_status", table_name="buyer_prospect_leads")
    op.drop_table("buyer_prospect_leads")
    op.drop_table("ubrain_tenant_memory")
