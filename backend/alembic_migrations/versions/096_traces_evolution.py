"""trace + scorecards + experience stage

Revision ID: 096
Revises: 095
Create Date: 2026-09-03

总纲 §4.6-7 / §8 085_traces（实现承接）：统一 Trace 链式表 + 记分卡。
- task_traces：统一 Trace（TASK-013）。prompt 正文只存对象存储引用；吸收 Claude 的
  artifacts / validation_results 字段；人工反馈留证（§3.4）。
- skill_performance / agent_scorecards：版本/Agent 记分卡（吸收 §040 业务指标）。
- evolution_experiences.stage：经验成熟度分级 raw→validated→pattern→sop→skill（§4.6-7 阈值控制）。
约束：task_traces 租户隔离（tenant_id 关联 tenants.id，platform 级允许 NULL）；
skill_performance / agent_scorecards 唯一键防重复聚合。
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
revision: str = '096'
down_revision: Union[str, None] = '095'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TRACE_STATUSES = ('running', 'success', 'failed')
EXPERIENCE_STAGES = ('raw', 'validated', 'pattern', 'sop', 'skill')


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


def _column_exists(conn, table: str, column: str) -> bool:
    dialect = conn.dialect.name
    if dialect == "postgresql":
        row = conn.execute(
            sa.text(
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_name = :t AND column_name = :c"
            ),
            {"t": table, "c": column},
        ).fetchone()
    else:
        row = conn.execute(
            sa.text(
                "SELECT 1 FROM pragma_table_info(:t) WHERE name = :c"
            ),
            {"t": table, "c": column},
        ).fetchone()
    return row is not None


def upgrade() -> None:
    conn = op.get_bind()

    if not _table_exists(conn, "task_traces"):
        op.create_table(
            "task_traces",
            sa.Column("id", _uuid_col(), primary_key=True),
            sa.Column("tenant_id", _uuid_col(), sa.ForeignKey("tenants.id"), nullable=True),
            sa.Column("parent_trace_id", sa.String(length=36), nullable=True),
            sa.Column("trace_type", sa.String(length=30), nullable=False),
            sa.Column("source_id", sa.String(length=64), nullable=True),
            sa.Column("task_id", _uuid_col(), sa.ForeignKey("ai_tasks.id"), nullable=True),
            sa.Column("run_id", sa.String(length=36), nullable=True),
            sa.Column("skill_id", sa.String(length=100), nullable=True),
            sa.Column("skill_version", sa.String(length=20), nullable=True),
            sa.Column("model_name", sa.String(length=100), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="running"),
            sa.Column("success", sa.Boolean(), nullable=True),
            sa.Column("prompt_ref", sa.String(length=500), nullable=True),
            sa.Column("input_summary", sa.Text(), nullable=True),
            sa.Column("output_summary", sa.Text(), nullable=True),
            sa.Column("artifacts", sa.Text(), nullable=True),
            sa.Column("validation_results", sa.Text(), nullable=True),
            sa.Column("error_code", sa.String(length=50), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("cost", sa.Float(), nullable=False, server_default="0"),
            sa.Column("tokens_used", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("feedback", sa.Text(), nullable=True),
            sa.Column("metadata", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
            sa.CheckConstraint(
                "status IN (" + ", ".join(f"'{s}'" for s in TRACE_STATUSES) + ")",
                name="ck_task_traces_status",
            ),
        )
        op.create_index("ix_task_traces_parent", "task_traces", ["parent_trace_id"])
        op.create_index("ix_task_traces_source", "task_traces", ["trace_type", "source_id"])
        op.create_index("ix_task_traces_task", "task_traces", ["task_id"])
        op.create_index("ix_task_traces_tenant_created", "task_traces", ["tenant_id", "created_at"])
        op.create_index("ix_task_traces_status", "task_traces", ["status", "created_at"])

    if not _table_exists(conn, "skill_performance"):
        op.create_table(
            "skill_performance",
            sa.Column("id", _uuid_col(), primary_key=True),
            sa.Column("tenant_id", _uuid_col(), sa.ForeignKey("tenants.id"), nullable=True),
            sa.Column("skill_id", sa.String(length=100), nullable=False),
            sa.Column("skill_version", sa.String(length=20), nullable=False, server_default=""),
            sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
            sa.Column("window_end", sa.DateTime(timezone=True), nullable=False),
            sa.Column("total_invocations", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("success_rate", sa.Float(), nullable=False, server_default="0"),
            sa.Column("avg_duration_ms", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("avg_cost", sa.Float(), nullable=False, server_default="0"),
            sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint(
                "tenant_id", "skill_id", "skill_version", "window_start",
                name="uq_skill_performance_window",
            ),
        )
        op.create_index("ix_skill_performance_skill", "skill_performance", ["skill_id", "skill_version"])
        op.create_index("ix_skill_performance_tenant", "skill_performance", ["tenant_id"])

    if not _table_exists(conn, "agent_scorecards"):
        op.create_table(
            "agent_scorecards",
            sa.Column("id", _uuid_col(), primary_key=True),
            sa.Column("tenant_id", _uuid_col(), sa.ForeignKey("tenants.id"), nullable=True),
            sa.Column("agent_id", sa.String(length=100), nullable=False),
            sa.Column("agent_name", sa.String(length=200), nullable=True),
            sa.Column("task_type", sa.String(length=80), nullable=False),
            sa.Column("total_invocations", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("success_rate", sa.Float(), nullable=False, server_default="0"),
            sa.Column("avg_duration_ms", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("avg_cost", sa.Float(), nullable=False, server_default="0"),
            sa.Column("revenue_impact", sa.Numeric(precision=14, scale=2), nullable=False, server_default="0"),
            sa.Column("conversion_rate", sa.Float(), nullable=False, server_default="0"),
            sa.Column("efficiency", sa.Float(), nullable=False, server_default="0"),
            sa.Column("roi", sa.Float(), nullable=False, server_default="0"),
            sa.Column("evaluation_window_days", sa.Integer(), nullable=False, server_default="7"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint(
                "tenant_id", "agent_id", "task_type", name="uq_agent_scorecard_key"
            ),
        )
        op.create_index("ix_agent_scorecards_agent", "agent_scorecards", ["agent_id", "task_type"])
        op.create_index("ix_agent_scorecards_tenant", "agent_scorecards", ["tenant_id"])

    # evolution_experiences 增加成熟度分级列（幂等：列已存在则跳过）
    if _table_exists(conn, "evolution_experiences") and not _column_exists(
        conn, "evolution_experiences", "stage"
    ):
        op.add_column(
            "evolution_experiences",
            sa.Column("stage", sa.String(length=20), nullable=False, server_default="raw"),
        )
        op.create_index("ix_evolution_experiences_stage", "evolution_experiences", ["stage"])

    if conn.dialect.name == "postgresql":
        op.execute(
            "COMMENT ON TABLE task_traces IS "
            "'统一 Trace（总纲 §4.6-7/TASK-013）：链式追踪，prompt 正文只存对象存储引用，"
            "吸收 Claude artifacts/validation_results 字段。'"
        )


def downgrade() -> None:
    conn = op.get_bind()
    if _column_exists(conn, "evolution_experiences", "stage"):
        op.drop_index("ix_evolution_experiences_stage", table_name="evolution_experiences")
        op.drop_column("evolution_experiences", "stage")
    for t in ("task_traces", "skill_performance", "agent_scorecards"):
        if _table_exists(conn, t):
            op.drop_table(t)
