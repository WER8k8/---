"""租户企微推送配置（客户自有接收人）

Revision ID: 046_tenant_wecom_push
Revises: 045_push_events
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

revision = "046_tenant_wecom_push"
down_revision = "045_push_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenant_wecom_push_configs",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("tenant_id", _uuid_col(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("corp_id", sa.String(64), nullable=True),
        sa.Column("agent_id", sa.String(32), nullable=True),
        sa.Column("agent_secret", sa.String(200), nullable=True),
        sa.Column("push_userids", sa.Text(), nullable=True),
        sa.Column("webhook_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_tenant_wecom_push_tenant_id", "tenant_wecom_push_configs", ["tenant_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_tenant_wecom_push_tenant_id", table_name="tenant_wecom_push_configs")
    op.drop_table("tenant_wecom_push_configs")
