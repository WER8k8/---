"""出海参谋规则表 + App 设备注册

Revision ID: 023_trade_intel_app_devices
Revises: 022_add_missing_tables
"""

import sqlalchemy as sa
from alembic import op

def _uuid_col():
    """P0-B canonical：PG=native uuid（对齐模型 UUID_TYPE），其余=String(36)。"""
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID

        return UUID(as_uuid=False)
    return sa.String(36)


revision = "023_trade_intel_app_devices"
down_revision = "022_add_missing_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trade_country_category",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("category_key", sa.String(64), nullable=False),
        sa.Column("category_label", sa.String(120), nullable=False),
        sa.Column("hs_chapter", sa.String(16), nullable=False, server_default=""),
        sa.Column("country_code", sa.String(2), nullable=False),
        sa.Column("verdict", sa.String(16), nullable=False, server_default="caution"),
        sa.Column("growth", sa.String(32), nullable=True),
        sa.Column("competition", sa.String(32), nullable=True),
        sa.Column("certs_json", sa.Text(), server_default="[]"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_trade_country_category_lookup",
        "trade_country_category",
        ["category_key", "country_code"],
        unique=True,
    )

    op.create_table(
        "app_devices",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("tenant_id", sa.String(36), nullable=True),
        sa.Column("device_token", sa.String(512), nullable=False),
        sa.Column("platform", sa.String(32), server_default="web"),
        sa.Column("app_version", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_app_devices_user", "app_devices", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_app_devices_user", table_name="app_devices")
    op.drop_table("app_devices")
    op.drop_index("ix_trade_country_category_lookup", table_name="trade_country_category")
    op.drop_table("trade_country_category")
