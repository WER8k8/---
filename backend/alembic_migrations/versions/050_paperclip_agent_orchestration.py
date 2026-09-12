"""Paperclip Agent 编排层数据表

Revision ID: 050_paperclip
Revises: 049_platform_survival_ledger
Create Date: 2026-07-18
"""

from alembic import op

def _uuid_col():
    """P0-B canonical：PG=native uuid（对齐模型 UUID_TYPE），其余=String(36)。"""
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID

        return UUID(as_uuid=False)
    return sa.String(36)

import sqlalchemy as sa

revision = "050_paperclip"
down_revision = "049_platform_survival_ledger"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "paperclip_companies",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("tenant_id", _uuid_col(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("mission", sa.Text, server_default=""),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "paperclip_agents",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("company_id", _uuid_col(), sa.ForeignKey("paperclip_companies.id"), nullable=False, index=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("title", sa.String(128), server_default=""),
        sa.Column("role", sa.String(64), server_default="worker"),
        sa.Column("provider", sa.String(64), server_default="hermes"),
        sa.Column("agent_ref", sa.String(128), server_default=""),
        sa.Column("parent_id", _uuid_col(), sa.ForeignKey("paperclip_agents.id"), nullable=True),
        sa.Column("heartbeat_interval_minutes", sa.Integer, server_default="240"),
        sa.Column("heartbeat_enabled", sa.Boolean, server_default="1"),
        sa.Column("monthly_budget_credits", sa.Float, server_default="1000.0"),
        sa.Column("used_credits", sa.Float, server_default="0.0"),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("skills_json", sa.Text, server_default="[]"),
        sa.Column("config_json", sa.Text, server_default="{}"),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "paperclip_goals",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("company_id", _uuid_col(), sa.ForeignKey("paperclip_companies.id"), nullable=False, index=True),
        sa.Column("parent_id", _uuid_col(), sa.ForeignKey("paperclip_goals.id"), nullable=True),
        sa.Column("owner_agent_id", _uuid_col(), sa.ForeignKey("paperclip_agents.id"), nullable=True),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("description", sa.Text, server_default=""),
        sa.Column("level", sa.String(20), server_default="task"),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("priority", sa.Integer, server_default="0"),
        sa.Column("progress", sa.Float, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "paperclip_heartbeats",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("agent_id", _uuid_col(), sa.ForeignKey("paperclip_agents.id"), nullable=False, index=True),
        sa.Column("company_id", _uuid_col(), sa.ForeignKey("paperclip_companies.id"), nullable=False, index=True),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("trigger", sa.String(20), server_default="schedule"),
        sa.Column("tasks_checked", sa.Integer, server_default="0"),
        sa.Column("tasks_executed", sa.Integer, server_default="0"),
        sa.Column("credits_used", sa.Float, server_default="0.0"),
        sa.Column("result_json", sa.Text, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "paperclip_approvals",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("company_id", _uuid_col(), sa.ForeignKey("paperclip_companies.id"), nullable=False, index=True),
        sa.Column("agent_id", _uuid_col(), sa.ForeignKey("paperclip_agents.id"), nullable=True),
        sa.Column("action_type", sa.String(64), nullable=False),
        sa.Column("action_payload_json", sa.Text, server_default="{}"),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("reviewer_id", _uuid_col(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("review_comment", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "paperclip_tasks",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("company_id", _uuid_col(), sa.ForeignKey("paperclip_companies.id"), nullable=False, index=True),
        sa.Column("goal_id", _uuid_col(), sa.ForeignKey("paperclip_goals.id"), nullable=True),
        sa.Column("assigned_agent_id", _uuid_col(), sa.ForeignKey("paperclip_agents.id"), nullable=True),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("description", sa.Text, server_default=""),
        sa.Column("intent", sa.String(64), server_default=""),
        sa.Column("status", sa.String(20), server_default="queued"),
        sa.Column("priority", sa.Integer, server_default="0"),
        sa.Column("deerflow_job_id", _uuid_col(), sa.ForeignKey("deerflow_jobs.id"), nullable=True),
        sa.Column("result_json", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("paperclip_tasks")
    op.drop_table("paperclip_approvals")
    op.drop_table("paperclip_heartbeats")
    op.drop_table("paperclip_goals")
    op.drop_table("paperclip_agents")
    op.drop_table("paperclip_companies")
