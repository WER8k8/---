"""payment ops audit table

Revision ID: 037_payment_ops_audit
Revises: 036_inquiry_assigned_to
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

revision = "037_payment_ops_audit"
down_revision = "036_inquiry_assigned_to"
branch_labels = None
depends_on = None


def _user_id_type():
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID

        return UUID(as_uuid=True)
    return sa.String(36)


def upgrade() -> None:
    op.create_table(
        "payment_ops_audit",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("actor_user_id", _user_id_type(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("ok", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_payment_ops_audit_actor_user_id", "payment_ops_audit", ["actor_user_id"])
    op.create_index("ix_payment_ops_audit_action", "payment_ops_audit", ["action"])
    op.create_index("ix_payment_ops_audit_created_at", "payment_ops_audit", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_payment_ops_audit_created_at", table_name="payment_ops_audit")
    op.drop_index("ix_payment_ops_audit_action", table_name="payment_ops_audit")
    op.drop_index("ix_payment_ops_audit_actor_user_id", table_name="payment_ops_audit")
    op.drop_table("payment_ops_audit")
