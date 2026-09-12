"""Add publish_tasks table

Revision ID: 031
Revises: 030_add_egress_and_browser_profile
Create Date: 2026-05-27
"""
from alembic import op
import sqlalchemy as sa

revision = "031_add_publish_task"
down_revision = "030_add_egress_and_browser_profile"
branch_labels = None
depends_on = None


def _uuid_type():
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID

        return UUID(as_uuid=True)
    return sa.String(36)


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing = set(insp.get_table_names())

    if "publish_tasks" not in existing:
        op.create_table(
            "publish_tasks",
            sa.Column("id", _uuid_type(), primary_key=True),
            sa.Column("content_master_id", _uuid_type(), nullable=True),
            sa.Column("content_id", _uuid_type(), nullable=True),
            sa.Column("region", sa.String(20), server_default="cn"),
            sa.Column("primary_url", sa.String(1000), nullable=True),
            sa.Column("secondary_url", sa.String(1000), nullable=True),
            sa.Column("platform_id", _uuid_type(), nullable=False),
            sa.Column("account_id", _uuid_type(), nullable=False),
            sa.Column("status", sa.String(20), server_default="pending"),
            sa.Column("publish_type", sa.String(20), server_default="immediate"),
            sa.Column("scheduled_time", sa.DateTime(timezone=True), nullable=True),
            sa.Column("retry_count", sa.Integer(), server_default="0"),
            sa.Column("max_retries", sa.Integer(), server_default="3"),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("published_url", sa.String(1000), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_publish_tasks_status", "publish_tasks", ["status"])
        return

    cols = {c["name"] for c in insp.get_columns("publish_tasks")}
    uuid_t = _uuid_type()
    additions = (
        ("content_master_id", sa.Column("content_master_id", uuid_t, nullable=True)),
        ("region", sa.Column("region", sa.String(20), server_default="cn")),
        ("primary_url", sa.Column("primary_url", sa.String(1000), nullable=True)),
        ("secondary_url", sa.Column("secondary_url", sa.String(1000), nullable=True)),
    )
    for name, col in additions:
        if name not in cols:
            op.add_column("publish_tasks", col)


def downgrade() -> None:
    op.drop_index("ix_publish_tasks_status", table_name="publish_tasks")
    op.drop_table("publish_tasks")
