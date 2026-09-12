"""Add AI config tables for model provider configuration

Revision ID: 016_add_ai_config_tables
Revises: 015_add_news_tables
Create Date: 2026-05-04 12:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.exc import OperationalError

from alembic import op

def _uuid_col():
    """P0-B canonical：PG=native uuid（对齐模型 UUID_TYPE），其余=String(36)。"""
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID

        return UUID(as_uuid=False)
    return sa.String(36)


# revision identifiers, used by Alembic.
revision = "016_add_ai_config_tables"
down_revision = "015_add_news_tables"
branch_labels = None
depends_on = None


def table_exists(table_name):
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        result = conn.execute(sa.text(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"))
        return result.fetchone() is not None
    return False


def create_table_safe(table_name, *args, **kwargs):
    if not table_exists(table_name):
        try:
            op.create_table(table_name, *args, **kwargs)
        except OperationalError:
            pass


def create_index_safe(index_name, table_name, columns, unique=False):
    try:
        op.create_index(index_name, table_name, columns, unique=unique)
    except OperationalError:
        pass


def upgrade():
    # Create ai_model_providers table
    create_table_safe(
        "ai_model_providers",
        sa.Column("id", _uuid_col(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("provider_type", sa.String(length=30), nullable=False),
        sa.Column("api_key", sa.String(length=255), nullable=False),
        sa.Column("base_url", sa.String(length=255), nullable=True),
        sa.Column("default_model", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # Create indexes for ai_model_providers
    create_index_safe(
        op.f("ix_ai_model_providers_provider_type"),
        "ai_model_providers",
        ["provider_type"],
        unique=False)
    create_index_safe(
        op.f("ix_ai_model_providers_is_active"),
        "ai_model_providers",
        ["is_active"],
        unique=False)
    create_index_safe(
        op.f("ix_ai_model_providers_is_default"),
        "ai_model_providers",
        ["is_default"],
        unique=False)

    # Create ai_model_configs table
    create_table_safe(
        "ai_model_configs",
        sa.Column("id", _uuid_col(), nullable=False),
        sa.Column("provider_id", _uuid_col(), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("model_type", sa.String(length=30), nullable=False),
        sa.Column("temperature", sa.String(length=10), nullable=False),
        sa.Column("max_tokens", sa.String(length=10), nullable=False),
        sa.Column("context_window", sa.String(length=10), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["provider_id"],
            ["ai_model_providers.id"],
        ),
    )

    # Create indexes for ai_model_configs
    create_index_safe(
        op.f("ix_ai_model_configs_provider_id"),
        "ai_model_configs",
        ["provider_id"],
        unique=False)
    create_index_safe(
        op.f("ix_ai_model_configs_model_type"),
        "ai_model_configs",
        ["model_type"],
        unique=False)
    create_index_safe(
        op.f("ix_ai_model_configs_is_active"),
        "ai_model_configs",
        ["is_active"],
        unique=False)
    create_index_safe(
        op.f("ix_ai_model_configs_is_default"),
        "ai_model_configs",
        ["is_default"],
        unique=False)

    # Create ai_usage_logs table
    create_table_safe(
        "ai_usage_logs",
        sa.Column("id", _uuid_col(), nullable=False),
        sa.Column("provider_id", _uuid_col(), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("task_type", sa.String(length=50), nullable=False),
        sa.Column("prompt_tokens", sa.String(length=10), nullable=True),
        sa.Column("completion_tokens", sa.String(length=10), nullable=True),
        sa.Column("total_tokens", sa.String(length=10), nullable=True),
        sa.Column("cost", sa.String(length=20), nullable=True),
        sa.Column("duration_ms", sa.String(length=20), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["provider_id"],
            ["ai_model_providers.id"],
        ),
    )

    # Create indexes for ai_usage_logs
    create_index_safe(
        op.f("ix_ai_usage_logs_provider_id"),
        "ai_usage_logs",
        ["provider_id"],
        unique=False)
    create_index_safe(
        op.f("ix_ai_usage_logs_model_name"),
        "ai_usage_logs",
        ["model_name"],
        unique=False)
    create_index_safe(
        op.f("ix_ai_usage_logs_task_type"),
        "ai_usage_logs",
        ["task_type"],
        unique=False)
    create_index_safe(
        op.f("ix_ai_usage_logs_created_at"),
        "ai_usage_logs",
        ["created_at"],
        unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(
        op.f("ix_ai_usage_logs_created_at"),
        table_name="ai_usage_logs")
    op.drop_index(
        op.f("ix_ai_usage_logs_task_type"),
        table_name="ai_usage_logs")
    op.drop_index(
        op.f("ix_ai_usage_logs_model_name"),
        table_name="ai_usage_logs")
    op.drop_index(
        op.f("ix_ai_usage_logs_provider_id"),
        table_name="ai_usage_logs")
    op.drop_table("ai_usage_logs")

    op.drop_index(
        op.f("ix_ai_model_configs_is_default"),
        table_name="ai_model_configs")
    op.drop_index(
        op.f("ix_ai_model_configs_is_active"),
        table_name="ai_model_configs")
    op.drop_index(
        op.f("ix_ai_model_configs_model_type"),
        table_name="ai_model_configs")
    op.drop_index(
        op.f("ix_ai_model_configs_provider_id"),
        table_name="ai_model_configs")
    op.drop_table("ai_model_configs")

    op.drop_index(
        op.f("ix_ai_model_providers_is_default"),
        table_name="ai_model_providers")
    op.drop_index(
        op.f("ix_ai_model_providers_is_active"),
        table_name="ai_model_providers")
    op.drop_index(
        op.f("ix_ai_model_providers_provider_type"),
        table_name="ai_model_providers")
    op.drop_table("ai_model_providers")
