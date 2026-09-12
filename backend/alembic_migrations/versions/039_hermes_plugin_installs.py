"""hermes plugin installs per tenant

Revision ID: 039_hermes_plugin_installs
Revises: 038_referral_redemption
Create Date: 2026-06-02
"""

from alembic import op

def _uuid_col():
    """P0-B canonical：PG=native uuid（对齐模型 UUID_TYPE），其余=String(36)。"""
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID

        return UUID(as_uuid=False)
    return sa.String(36)

import sqlalchemy as sa

revision = "039_hermes_plugin_installs"
down_revision = "038_referral_redemption"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "hermes_plugin_installs",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("tenant_id", _uuid_col(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("plugin_id", sa.String(64), nullable=False),
        sa.Column("plugin_version", sa.String(32), nullable=False, server_default="1.0.0"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("config_json", sa.Text(), server_default="{}"),
        sa.Column("installed_by", _uuid_col(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("installed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "plugin_id", name="uq_hermes_plugin_tenant"),
    )
    op.create_index("ix_hermes_plugin_installs_tenant_id", "hermes_plugin_installs", ["tenant_id"])
    op.create_index("ix_hermes_plugin_installs_plugin_id", "hermes_plugin_installs", ["plugin_id"])


def downgrade() -> None:
    op.drop_index("ix_hermes_plugin_installs_plugin_id", table_name="hermes_plugin_installs")
    op.drop_index("ix_hermes_plugin_installs_tenant_id", table_name="hermes_plugin_installs")
    op.drop_table("hermes_plugin_installs")
