"""Migration: 添加 AI 内容模板表

Revision ID: 029_add_ai_template_table
Revises: 028_ubrain_action_audit
"""

import sqlalchemy as sa
from alembic import op

def _uuid_col():
    """P0-B canonical：PG=native uuid（对齐模型 UUID_TYPE），其余=String(36)。"""
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID

        return UUID(as_uuid=False)
    return sa.String(36)


revision = "029_add_ai_template_table"
down_revision = "028_ubrain_action_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if op.get_context().dialect.name == "postgresql":
        op.execute("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(128)")

    op.create_table(
        "ai_templates",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("task_type", sa.String(30), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=True),
        sa.Column("user_prompt_template", sa.Text(), nullable=False),
        sa.Column("variables_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("default_params_json", sa.Text(), nullable=False, server_default='{"temperature":0.7,"max_tokens":2000}'),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_ai_templates_task_type", "ai_templates", ["task_type"])
    op.create_index("ix_ai_templates_active", "ai_templates", ["is_active"])


def downgrade() -> None:
    op.drop_index("ix_ai_templates_active", table_name="ai_templates")
    op.drop_index("ix_ai_templates_task_type", table_name="ai_templates")
    op.drop_table("ai_templates")
