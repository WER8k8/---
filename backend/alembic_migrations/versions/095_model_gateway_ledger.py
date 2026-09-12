"""model gateway ledger: model_capabilities / model_call_ledger

Revision ID: 095
Revises: 094
Create Date: 2026-09-02

总纲 §4.6 / 迁移总表 084（实现承接）：Model Gateway 成本记账。
- model_capabilities：能力标签 → 提供商/模型 路由表（评分维度 Quality+Speed+Cost+Privacy 并入能力标签路由）。
- model_call_ledger：每次 LLM 调用明细，可汇总至既有 token_ledger_entries（聚合由 086 MeterEvent 负责）。
约束：租户隔离（tenant_id 关联 tenants.id，platform 级调用允许 NULL）；
model_call_ledger.status ∈ {success, failure}；能力标签源自 §4.6 八类。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

def _uuid_col():
    """P0-B canonical：PG=native uuid（对齐模型 UUID_TYPE），其余=String(36)。"""
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID

        return UUID(as_uuid=False)
    return sa.String(36)


# revision identifiers, used by Alembic.
revision: str = '095'
down_revision: Union[str, None] = '094'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CALL_STATUSES = ('success', 'failure')


def _table_exists(conn, name: str) -> bool:
    dialect = conn.dialect.name
    if dialect == "postgresql":
        row = conn.execute(
            sa.text("SELECT 1 FROM information_schema.tables WHERE table_name = :n"),
            {"n": name},
        ).fetchone()
    else:
        row = conn.execute(
            sa.text("SELECT 1 FROM sqlite_master WHERE type='table' AND name = :n"),
            {"n": name},
        ).fetchone()
    return row is not None


def upgrade() -> None:
    conn = op.get_bind()

    if not _table_exists(conn, "model_capabilities"):
        op.create_table(
            "model_capabilities",
            sa.Column("id", _uuid_col(), primary_key=True),
            sa.Column("tenant_id", _uuid_col(), sa.ForeignKey("tenants.id"), nullable=True),
            sa.Column("provider", sa.String(length=50), nullable=False),
            sa.Column("model_name", sa.String(length=100), nullable=False),
            sa.Column("capability_tag", sa.String(length=40), nullable=False),
            sa.Column("priority", sa.Integer(), nullable=False, server_default="50"),
            sa.Column("cost_per_1k_input", sa.Numeric(precision=10, scale=6), nullable=False, server_default="0"),
            sa.Column("cost_per_1k_output", sa.Numeric(precision=10, scale=6), nullable=False, server_default="0"),
            sa.Column("max_tokens", sa.Integer(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("tenant_id", "provider", "model_name", "capability_tag",
                                name="uq_model_capabilities_unique"),
        )
        op.create_index("ix_model_capabilities_tenant_cap", "model_capabilities",
                        ["tenant_id", "capability_tag"])
        op.create_index("ix_model_capabilities_active", "model_capabilities", ["is_active"])

    if not _table_exists(conn, "model_call_ledger"):
        op.create_table(
            "model_call_ledger",
            sa.Column("id", _uuid_col(), primary_key=True),
            sa.Column("tenant_id", _uuid_col(), sa.ForeignKey("tenants.id"), nullable=True),
            sa.Column("task_id", _uuid_col(), sa.ForeignKey("ai_tasks.id"), nullable=True),
            sa.Column("provider", sa.String(length=50), nullable=True),
            sa.Column("model_name", sa.String(length=100), nullable=True),
            sa.Column("capability_tag", sa.String(length=40), nullable=True),
            sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("cost_usd", sa.Numeric(precision=12, scale=6), nullable=False, server_default="0"),
            sa.Column("latency_ms", sa.Integer(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="success"),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("called_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("request_id", sa.String(length=128), nullable=True),
            sa.Column("metadata_json", sa.Text(), nullable=True),
            sa.CheckConstraint(
                "status IN (" + ", ".join(f"'{s}'" for s in CALL_STATUSES) + ")",
                name="ck_model_call_ledger_status",
            ),
        )
        op.create_index("ix_model_call_ledger_tenant_called", "model_call_ledger",
                        ["tenant_id", "called_at"])
        op.create_index("ix_model_call_ledger_task", "model_call_ledger", ["task_id"])
        op.create_index("ix_model_call_ledger_capability", "model_call_ledger", ["capability_tag"])

    if conn.dialect.name == "postgresql":
        op.execute(
            "COMMENT ON TABLE model_capabilities IS "
            "'Model Gateway 能力路由表（总纲 §4.6）：能力标签→提供商/模型，评分维度并入能力标签路由。'"
        )
        op.execute(
            "COMMENT ON TABLE model_call_ledger IS "
            "'Model Gateway 每次 LLM 调用明细，最佳努力写入，可汇总至 token_ledger_entries。'"
        )


def downgrade() -> None:
    conn = op.get_bind()
    for t in ("model_call_ledger", "model_capabilities"):
        if _table_exists(conn, t):
            op.drop_table(t)
