"""pipeline core: pipeline_runs / pipeline_steps

Revision ID: 090
Revises: 087
Create Date: 2026-08-31

总纲 §6.5/§8 定稿：四链路（文章/视频/邮件/多平台）强制流水线主表。
状态集 11 态：generated→cleansing→cleansed→reviewing→approved→
distributing→verifying→done；异常支路 failed / wait_human / retrying。
约束：租户隔离（tenant_id NOT NULL）；(tenant_id, idempotency_key) 唯一；
lease 单泳道锁字段（§6.4-5）；source_task_id 关联 ai_tasks（082）。
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
revision: str = '090'
down_revision: Union[str, None] = '087'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PIPELINE_TYPES = ('article', 'video', 'email', 'multi_channel')
RUN_STATUSES = (
    'generated', 'cleansing', 'cleansed', 'reviewing', 'approved',
    'distributing', 'verifying', 'done', 'failed', 'wait_human', 'retrying',
)
STEP_STATUSES = ('pending', 'running', 'done', 'failed', 'skipped')


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

    if not _table_exists(conn, "pipeline_runs"):
        op.create_table(
            "pipeline_runs",
            sa.Column("id", _uuid_col(), primary_key=True),
            sa.Column("tenant_id", _uuid_col(), sa.ForeignKey("tenants.id"), nullable=False),
            sa.Column("pipeline_type", sa.String(length=20), nullable=False),
            sa.Column("source_task_id", _uuid_col(), sa.ForeignKey("ai_tasks.id"), nullable=True),
            sa.Column("subject_ref", sa.String(length=200), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="generated"),
            sa.Column("checkpoint_json", sa.Text(), nullable=True),
            sa.Column("lease_owner", sa.String(length=100), nullable=True),
            sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("idempotency_key", sa.String(length=128), nullable=True),
            sa.Column("skill_version", sa.String(length=40), nullable=True),
            sa.Column("rule_pack_version", sa.String(length=40), nullable=True),
            sa.Column("budget_used", sa.Numeric(precision=12, scale=4), nullable=False, server_default="0"),
            sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.CheckConstraint(
                "pipeline_type IN (" + ", ".join(f"'{s}'" for s in PIPELINE_TYPES) + ")",
                name="ck_pipeline_runs_type",
            ),
            sa.CheckConstraint(
                "status IN (" + ", ".join(f"'{s}'" for s in RUN_STATUSES) + ")",
                name="ck_pipeline_runs_status",
            ),
        )
        op.create_index("ix_pipeline_runs_tenant_status", "pipeline_runs", ["tenant_id", "status"])
        op.create_index("ix_pipeline_runs_source_task", "pipeline_runs", ["source_task_id"])
        op.create_index("ix_pipeline_runs_lease_expires", "pipeline_runs", ["lease_expires_at"])
        op.create_index(
            "uq_pipeline_runs_tenant_idempotency", "pipeline_runs",
            ["tenant_id", "idempotency_key"], unique=True,
        )

    if not _table_exists(conn, "pipeline_steps"):
        op.create_table(
            "pipeline_steps",
            sa.Column("id", _uuid_col(), primary_key=True),
            sa.Column("run_id", _uuid_col(), sa.ForeignKey("pipeline_runs.id"), nullable=False),
            sa.Column("seq", sa.Integer(), nullable=False),
            sa.Column("step_type", sa.String(length=50), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
            sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("input_ref", sa.String(length=500), nullable=True),
            sa.Column("output_ref", sa.String(length=500), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("error", sa.Text(), nullable=True),
            sa.CheckConstraint(
                "status IN (" + ", ".join(f"'{s}'" for s in STEP_STATUSES) + ")",
                name="ck_pipeline_steps_status",
            ),
            sa.UniqueConstraint("run_id", "seq", name="uq_pipeline_steps_run_seq"),
        )
        op.create_index("ix_pipeline_steps_run", "pipeline_steps", ["run_id"])

    if conn.dialect.name == "postgresql":
        op.execute(
            "COMMENT ON TABLE pipeline_runs IS "
            "'四链路强制流水线（总纲 §6.5）：清洗→复核→审批→分发→验证→留证，不可跳过。'"
        )


def downgrade() -> None:
    conn = op.get_bind()
    for t in ("pipeline_steps", "pipeline_runs"):
        if _table_exists(conn, t):
            op.drop_table(t)
