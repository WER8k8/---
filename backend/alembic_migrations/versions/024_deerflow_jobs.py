"""DeerFlow 异步任务表

Revision ID: 024_deerflow_jobs
Revises: 023_trade_intel_app_devices
"""

import sqlalchemy as sa
from alembic import op

def _uuid_col():
    """P0-B canonical：PG=native uuid（对齐模型 UUID_TYPE），其余=String(36)。"""
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID

        return UUID(as_uuid=False)
    return sa.String(36)


revision = "024_deerflow_jobs"
down_revision = "023_trade_intel_app_devices"
branch_labels = None
depends_on = None


def _user_id_type():
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID

        return UUID(as_uuid=True)
    return sa.String(36)


def upgrade() -> None:
    op.create_table(
        "deerflow_jobs",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("tenant_id", _uuid_col(), nullable=False),
        sa.Column("intent", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
        sa.Column("payload_json", sa.Text(), server_default="{}"),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("log_text", sa.Text(), server_default=""),
        sa.Column("created_by", _user_id_type(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
    )
    op.create_index("ix_deerflow_jobs_tenant_status", "deerflow_jobs", ["tenant_id", "status"])
    op.create_index("ix_deerflow_jobs_intent", "deerflow_jobs", ["intent"])


def downgrade() -> None:
    op.drop_index("ix_deerflow_jobs_intent", table_name="deerflow_jobs")
    op.drop_index("ix_deerflow_jobs_tenant_status", table_name="deerflow_jobs")
    op.drop_table("deerflow_jobs")
