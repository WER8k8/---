"""商业 OS 飞轮：研究洞察 / 编排 / 反馈

Revision ID: 026_ubrain_commercial_os
Revises: 025_ubrain_accio_sales
"""

import sqlalchemy as sa
from alembic import op

def _uuid_col():
    """P0-B canonical：PG=native uuid（对齐模型 UUID_TYPE），其余=String(36)。"""
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID

        return UUID(as_uuid=False)
    return sa.String(36)


revision = "026_ubrain_commercial_os"
down_revision = "025_ubrain_accio_sales"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ubrain_research_insights",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("tenant_id", _uuid_col(), nullable=False),
        sa.Column("source", sa.String(40), nullable=False, server_default="deerflow"),
        sa.Column("source_job_id", sa.String(36), nullable=True),
        sa.Column("intent", sa.String(64), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("entities_json", sa.Text(), server_default="[]"),
        sa.Column("tags_json", sa.Text(), server_default="[]"),
        sa.Column("regions_json", sa.Text(), server_default="[]"),
        sa.Column("categories_json", sa.Text(), server_default="[]"),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
    )
    op.create_index(
        "ix_ubrain_insights_tenant_created",
        "ubrain_research_insights",
        ["tenant_id", "created_at"],
    )

    op.create_table(
        "ubrain_pipeline_runs",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("tenant_id", _uuid_col(), nullable=False),
        sa.Column("trigger_job_id", sa.String(36), nullable=True),
        sa.Column("insight_id", _uuid_col(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("steps_json", sa.Text(), server_default="[]"),
        sa.Column("created_job_ids_json", sa.Text(), server_default="[]"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["insight_id"], ["ubrain_research_insights.id"]),
    )

    op.create_table(
        "ubrain_feedback_snapshots",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("tenant_id", _uuid_col(), nullable=False),
        sa.Column("period_days", sa.Integer(), nullable=False, server_default="7"),
        sa.Column("metrics_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("recommendations_json", sa.Text(), server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
    )


def downgrade() -> None:
    op.drop_table("ubrain_feedback_snapshots")
    op.drop_table("ubrain_pipeline_runs")
    op.drop_index("ix_ubrain_insights_tenant_created", table_name="ubrain_research_insights")
    op.drop_table("ubrain_research_insights")
