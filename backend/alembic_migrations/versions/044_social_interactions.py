"""Lane I: social_interactions 社媒评论/私信自动谈单

Revision ID: 044_social_interactions
Revises: 043_iproyal_long_term_support
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

revision = "044_social_interactions"
down_revision = "043_iproyal_long_term_support"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "social_interactions",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("platform", sa.String(32), nullable=False, server_default="douyin"),
        sa.Column("interaction_type", sa.String(16), nullable=False, server_default="comment"),
        sa.Column("platform_post_id", sa.String(128), nullable=True),
        sa.Column("platform_comment_id", sa.String(128), nullable=True),
        sa.Column("author_name", sa.String(120), nullable=False, server_default="访客"),
        sa.Column("author_platform_id", sa.String(128), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("intent", sa.String(32), nullable=False, server_default="general"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("draft_reply", sa.Text(), nullable=True),
        sa.Column("final_reply", sa.Text(), nullable=True),
        sa.Column("platform_send_receipt", sa.JSON(), nullable=True),
        sa.Column("inquiry_id", sa.String(36), nullable=True),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_social_interactions_platform_comment",
        "social_interactions",
        ["platform", "platform_comment_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_social_interactions_platform_comment", table_name="social_interactions")
    op.drop_table("social_interactions")
