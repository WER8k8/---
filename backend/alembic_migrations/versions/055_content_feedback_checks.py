"""content_feedback_checks + industry_patterns

Revision ID: 055_content_feedback_checks
Revises: 054_attribution_fields
Create Date: 2026-07-19
"""
from alembic import op

def _uuid_col():
    """P0-B canonical：PG=native uuid（对齐模型 UUID_TYPE），其余=String(36)。"""
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID

        return UUID(as_uuid=False)
    return sa.String(36)

import sqlalchemy as sa

revision = "055_content_feedback_checks"
down_revision = "054_attribution_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── content_feedback_checks ──
    op.create_table(
        "content_feedback_checks",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("content_id", sa.String(36), nullable=False, index=True),
        sa.Column("publish_url", sa.String(1000), nullable=False),
        sa.Column("platform", sa.String(100), server_default=""),
        sa.Column("tenant_id", sa.String(36), nullable=True, index=True),
        sa.Column("keyword", sa.String(500), server_default=""),
        sa.Column("tactics_version", sa.String(50), server_default=""),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending", index=True),
        sa.Column("check_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("is_indexed", sa.Boolean, nullable=True),
        sa.Column("rank_position", sa.Integer, nullable=True),
        sa.Column("rank_change", sa.Integer, nullable=True),
        sa.Column("probe_error", sa.Text, nullable=True),
        sa.Column("check_meta", sa.JSON, nullable=True),
        sa.Column("refresh_suggested", sa.Boolean, server_default=sa.false()),  # P0-B: 原 sa.text("0") 在 PG boolean 列 DatatypeMismatch
        sa.Column("refresh_reason", sa.String(200), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_cfc_status_check_at",
        "content_feedback_checks",
        ["status", "check_at"],
    )

    # ── industry_patterns ──
    op.create_table(
        "industry_patterns",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=True, index=True),
        sa.Column("content_id", sa.String(36), nullable=False, index=True),
        sa.Column("publish_url", sa.String(1000), nullable=False),
        sa.Column("platform", sa.String(100), server_default=""),
        sa.Column("pattern_type", sa.String(20), nullable=False, index=True),
        sa.Column("tactics_version", sa.String(50), server_default=""),
        sa.Column("rank_position", sa.Integer, nullable=True),
        sa.Column("rank_change", sa.Integer, nullable=True),
        sa.Column("details", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_ip_tenant_pattern_type",
        "industry_patterns",
        ["tenant_id", "pattern_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_ip_tenant_pattern_type", table_name="industry_patterns")
    op.drop_table("industry_patterns")
    op.drop_index("ix_cfc_status_check_at", table_name="content_feedback_checks")
    op.drop_table("content_feedback_checks")
