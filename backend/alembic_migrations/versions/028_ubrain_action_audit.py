"""Accio A5：UBrain 动作审计表

Revision ID: 028_ubrain_action_audit
Revises: 027_inquiry_source_channel
"""

import sqlalchemy as sa
from alembic import op

def _uuid_col():
    """P0-B canonical：PG=native uuid（对齐模型 UUID_TYPE），其余=String(36)。"""
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID

        return UUID(as_uuid=False)
    return sa.String(36)


revision = "028_ubrain_action_audit"
down_revision = "027_inquiry_source_channel"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ubrain_action_audits",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=True),
        sa.Column("action_type", sa.String(40), nullable=False),
        sa.Column("intent", sa.String(64), nullable=True),
        sa.Column("tool", sa.String(64), nullable=True),
        sa.Column("message_preview", sa.String(400), nullable=True),
        sa.Column("needs_confirmation", sa.String(5), nullable=False, server_default="false"),
        sa.Column("outcome", sa.String(20), nullable=False, server_default="ok"),
        sa.Column("meta_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_ubrain_action_audits_tenant_created",
        "ubrain_action_audits",
        ["tenant_id", "created_at"],
    )
    op.create_index(
        "ix_ubrain_action_audits_action_type",
        "ubrain_action_audits",
        ["action_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_ubrain_action_audits_action_type", table_name="ubrain_action_audits")
    op.drop_index(
        "ix_ubrain_action_audits_tenant_created", table_name="ubrain_action_audits"
    )
    op.drop_table("ubrain_action_audits")
