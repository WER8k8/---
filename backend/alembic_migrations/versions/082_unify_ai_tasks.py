"""unify ai tasks control plane

Revision ID: 082
Revises: 081
Create Date: 2026-08-31

总纲 §4.6-1/§8 定稿：统一任务控制面 ai_tasks。
收编 DeerflowJob/PaperclipTask 的任务真相源（双写过渡 2 迭代后降级为从表）。
字段依据：
- 状态机 10 态（9 态基线 + PAUSED，对齐 §4.6-2 与 §5.2 Trade AI 移植）；
- 幂等/断点/预算：idempotency_key / checkpoint_json / budget_used（§4.6-1）；
- GoodJob 执行可靠性模式：lease_owner / lease_expires / throttle_key（§5.1.4）。
约束：租户隔离（tenant_id NOT NULL + 索引）；本迁移不改写既有表。
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
revision: str = '082'
down_revision: Union[str, None] = '081'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 统一状态机（§4.6-2 基线 9 态 + §5.2 增补 paused）
TASK_STATUSES = (
    'created', 'planning', 'executing', 'review', 'paused',
    'retrying', 'wait_human', 'done', 'failed', 'cancelled', 'timeout',
)


def _table_exists(conn, name: str) -> bool:
    dialect = conn.dialect.name
    if dialect == "postgresql":
        row = conn.execute(
            sa.text(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_name = :n"
            ),
            {"n": name},
        ).fetchone()
    else:
        row = conn.execute(
            sa.text(
                "SELECT 1 FROM sqlite_master "
                "WHERE type='table' AND name = :n"
            ),
            {"n": name},
        ).fetchone()
    return row is not None


def upgrade() -> None:
    conn = op.get_bind()

    if not _table_exists(conn, "ai_tasks"):
        op.create_table(
            "ai_tasks",
            sa.Column("id", _uuid_col(), primary_key=True),
            sa.Column("tenant_id", _uuid_col(), sa.ForeignKey("tenants.id"), nullable=False),
            sa.Column("parent_task_id", sa.String(length=36), nullable=True),
            sa.Column("task_type", sa.String(length=100), nullable=False),
            sa.Column(
                "status", sa.String(length=30), nullable=False,
                server_default="created",
            ),
            sa.Column("priority", sa.Integer(), nullable=False, server_default="5"),
            # 输入 / 输出 / 断点
            sa.Column("input_json", sa.Text(), nullable=True),
            sa.Column("output_json", sa.Text(), nullable=True),
            sa.Column("checkpoint_json", sa.Text(), nullable=True),
            # 幂等与预算
            sa.Column("idempotency_key", sa.String(length=128), nullable=True),
            sa.Column("budget_used", sa.Numeric(precision=12, scale=4), nullable=False, server_default="0"),
            sa.Column("budget_limit", sa.Numeric(precision=12, scale=4), nullable=True),
            # 有界重试（§4.8 红线：≤3 次，超限转 wait_human）
            sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
            # GoodJob 模式：单泳道锁 + 节流键（§5.1.4）
            sa.Column("lease_owner", sa.String(length=100), nullable=True),
            sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("throttle_key", sa.String(length=128), nullable=True),
            # 追踪与归属
            sa.Column("trace_id", sa.String(length=64), nullable=True),
            sa.Column("source", sa.String(length=50), nullable=True),
            sa.Column("created_by", sa.String(length=36), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.CheckConstraint(
                "status IN (" + ", ".join(f"'{s}'" for s in TASK_STATUSES) + ")",
                name="ck_ai_tasks_status",
            ),
        )
        op.create_index("ix_ai_tasks_tenant_status", "ai_tasks", ["tenant_id", "status"])
        op.create_index("ix_ai_tasks_tenant_type", "ai_tasks", ["tenant_id", "task_type"])
        op.create_index("ix_ai_tasks_parent", "ai_tasks", ["parent_task_id"])
        op.create_index("ix_ai_tasks_lease_expires", "ai_tasks", ["lease_expires_at"])
        op.create_index(
            "uq_ai_tasks_tenant_idempotency", "ai_tasks",
            ["tenant_id", "idempotency_key"], unique=True,
        )

    # 状态注释（仅 PostgreSQL）
    if conn.dialect.name == "postgresql":
        op.execute(
            "COMMENT ON TABLE ai_tasks IS "
            "'统一任务控制面（总纲 §4.6-1）。双写过渡期与 deerflow_jobs/paperclip_tasks 并行，"
            "2 个迭代后降级为从表。'"
        )


def downgrade() -> None:
    conn = op.get_bind()
    if _table_exists(conn, "ai_tasks"):
        op.drop_index("uq_ai_tasks_tenant_idempotency", table_name="ai_tasks")
        op.drop_index("ix_ai_tasks_lease_expires", table_name="ai_tasks")
        op.drop_index("ix_ai_tasks_parent", table_name="ai_tasks")
        op.drop_index("ix_ai_tasks_tenant_type", table_name="ai_tasks")
        op.drop_index("ix_ai_tasks_tenant_status", table_name="ai_tasks")
        op.drop_table("ai_tasks")
