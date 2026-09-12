"""nurture cycles + scheduled publish + engagement records

Revision ID: 050_nurture_cycle
Revises: 049_platform_survival_ledger
"""

from alembic import op

def _uuid_col():
    """P0-B canonical：PG=native uuid（对齐模型 UUID_TYPE），其余=String(36)。"""
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID

        return UUID(as_uuid=False)
    return sa.String(36)

import sqlalchemy as sa
from sqlalchemy import inspect

revision = "050_nurture_cycle"
down_revision = "049_platform_survival_ledger"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    return name in inspect(bind).get_table_names()


def _has_index(name: str) -> bool:
    bind = op.get_bind()
    insp = inspect(bind)
    for tbl in insp.get_table_names():
        for idx in insp.get_indexes(tbl):
            if idx.get("name") == name:
                return True
    return False


def upgrade() -> None:
    if not _has_table("nurture_cycles"):
        op.create_table(
            "nurture_cycles",
            sa.Column("id", _uuid_col(), primary_key=True),
            sa.Column("tenant_id", sa.String(36), nullable=True, index=True),
            sa.Column("platform", sa.String(32), nullable=False, index=True),
            sa.Column("account_label", sa.String(120), nullable=False),
            sa.Column("platform_account_id", _uuid_col(), sa.ForeignKey("platform_accounts.id"), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
            sa.Column("rules", sa.JSON(), nullable=True),
            sa.Column("current_day", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_posts", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_likes", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_comments", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_follows", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("last_post_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_like_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_comment_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_follow_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("warning_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("cooldown_until", sa.DateTime(timezone=True), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    if not _has_index("ix_nurture_cycles_status"):
        op.create_index("ix_nurture_cycles_status", "nurture_cycles", ["status"])

    if not _has_table("scheduled_publishes"):
        op.create_table(
            "scheduled_publishes",
            sa.Column("id", _uuid_col(), primary_key=True),
            sa.Column("tenant_id", sa.String(36), nullable=True, index=True),
            sa.Column("platform_account_id", _uuid_col(), sa.ForeignKey("platform_accounts.id"), nullable=True),
            sa.Column("platform_name", sa.String(64), nullable=False, index=True),
            sa.Column("title", sa.String(500), nullable=False),
            sa.Column("body", sa.Text(), nullable=True),
            sa.Column("video_url", sa.String(1000), nullable=True),
            sa.Column("cover_url", sa.String(1000), nullable=True),
            sa.Column("tags", sa.JSON(), nullable=True),
            sa.Column("content_master_id", sa.String(36), nullable=True),
            sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
            sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
            sa.Column("published_url", sa.String(1000), nullable=True),
            sa.Column("published_post_id", sa.String(200), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("worker_chain", sa.JSON(), nullable=True),
            sa.Column("publish_task_id", _uuid_col(), sa.ForeignKey("publish_tasks.id"), nullable=True),
            sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
    if not _has_index("ix_scheduled_publishes_status"):
        op.create_index("ix_scheduled_publishes_status", "scheduled_publishes", ["status"])
    if not _has_index("ix_scheduled_publishes_scheduled_at"):
        op.create_index("ix_scheduled_publishes_scheduled_at", "scheduled_publishes", ["scheduled_at"])

    if not _has_table("engagement_records"):
        op.create_table(
            "engagement_records",
            sa.Column("id", _uuid_col(), primary_key=True),
            sa.Column("tenant_id", sa.String(36), nullable=True, index=True),
            sa.Column("platform", sa.String(32), nullable=False, index=True),
            sa.Column("platform_account_id", _uuid_col(), sa.ForeignKey("platform_accounts.id"), nullable=True),
            sa.Column("action_type", sa.String(20), nullable=False, index=True),
            sa.Column("target_post_id", sa.String(200), nullable=True),
            sa.Column("target_post_url", sa.String(1000), nullable=True),
            sa.Column("target_author", sa.String(200), nullable=True),
            sa.Column("target_comment_id", sa.String(200), nullable=True),
            sa.Column("content", sa.Text(), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("nurture_cycle_id", _uuid_col(), sa.ForeignKey("nurture_cycles.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    if not _has_index("ix_engagement_records_action_type"):
        op.create_index("ix_engagement_records_action_type", "engagement_records", ["action_type"])
    if not _has_index("ix_engagement_records_status"):
        op.create_index("ix_engagement_records_status", "engagement_records", ["status"])


def downgrade() -> None:
    for tbl in ("engagement_records", "scheduled_publishes", "nurture_cycles"):
        if _has_table(tbl):
            op.drop_table(tbl)
