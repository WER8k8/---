"""Lane P: push_events 企微推送事件表

Revision ID: 045_push_events
Revises: 044_social_interactions
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

revision = "045_push_events"
down_revision = "044_social_interactions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "push_events",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=True),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("ref_type", sa.String(50), nullable=False),
        sa.Column("ref_id", sa.String(36), nullable=False),
        sa.Column("channel", sa.String(32), nullable=False, server_default="wecom_app"),
        sa.Column("recipient", sa.String(200), nullable=True),
        sa.Column("title", sa.String(200), nullable=False, server_default=""),
        sa.Column("body", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("upstream_msgid", sa.String(128), nullable=True),
        sa.Column("upstream_receipt", sa.JSON(), nullable=True),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_push_events_tenant_id", "push_events", ["tenant_id"])
    op.create_index("ix_push_events_event_type", "push_events", ["event_type"])
    op.create_index("ix_push_events_ref_id", "push_events", ["ref_id"])
    op.create_index("ix_push_events_status", "push_events", ["status"])


def downgrade() -> None:
    op.drop_index("ix_push_events_status", table_name="push_events")
    op.drop_index("ix_push_events_ref_id", table_name="push_events")
    op.drop_index("ix_push_events_event_type", table_name="push_events")
    op.drop_index("ix_push_events_tenant_id", table_name="push_events")
    op.drop_table("push_events")
