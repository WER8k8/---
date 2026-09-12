"""egress_suppliers 供应商注册表

Revision ID: 047_egress_suppliers
Revises: 046_tenant_wecom_push
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

revision = "047_egress_suppliers"
down_revision = "046_tenant_wecom_push"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "egress_suppliers",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("code", sa.String(50), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("subtitle", sa.String(200), nullable=True),
        sa.Column("adapter", sa.String(30), nullable=False, server_default="manual"),
        sa.Column("ip_type", sa.String(40), nullable=False, server_default="static_residential"),
        sa.Column("long_term_fixed", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("config_json", sa.JSON(), nullable=True),
        sa.Column(
            "supports_pool_replenish",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false(), index=True),
        sa.Column("is_builtin", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("egress_suppliers")
