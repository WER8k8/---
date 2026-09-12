"""pipeline evidence: step_evidence / review_tasks

Revision ID: 091
Revises: 090
Create Date: 2026-08-31

总纲 §6.5/§8 定稿：步级证据 + 人工复核任务表。
step_evidence：发布类步骤必须外部状态核验才置 verified（§6.4-8，Evidence 机制 §1.2-5）。
review_tasks：复核三态 approved/rejected/revise（§6.4-2），decided_at 为空=待复核。
约束：两表均带 tenant_id（RLS 批次候选）。
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
revision: str = '091'
down_revision: Union[str, None] = '090'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EVIDENCE_TYPES = ('platform_id', 'url_check', 'screenshot', 'score', 'human_approval')
REVIEW_DECISIONS = ('approved', 'rejected', 'revise')


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

    if not _table_exists(conn, "step_evidence"):
        op.create_table(
            "step_evidence",
            sa.Column("id", _uuid_col(), primary_key=True),
            sa.Column("tenant_id", _uuid_col(), sa.ForeignKey("tenants.id"), nullable=False),
            sa.Column("step_id", _uuid_col(), sa.ForeignKey("pipeline_steps.id"), nullable=False),
            sa.Column("claim", sa.Text(), nullable=True),
            sa.Column("evidence_type", sa.String(length=30), nullable=False),
            sa.Column("evidence_ref", sa.String(length=500), nullable=True),
            sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("validator_version", sa.String(length=40), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.CheckConstraint(
                "evidence_type IN (" + ", ".join(f"'{s}'" for s in EVIDENCE_TYPES) + ")",
                name="ck_step_evidence_type",
            ),
        )
        op.create_index("ix_step_evidence_step", "step_evidence", ["step_id"])
        op.create_index("ix_step_evidence_tenant", "step_evidence", ["tenant_id"])

    if not _table_exists(conn, "review_tasks"):
        op.create_table(
            "review_tasks",
            sa.Column("id", _uuid_col(), primary_key=True),
            sa.Column("tenant_id", _uuid_col(), sa.ForeignKey("tenants.id"), nullable=False),
            sa.Column("run_id", _uuid_col(), sa.ForeignKey("pipeline_runs.id"), nullable=False),
            sa.Column("step_id", _uuid_col(), sa.ForeignKey("pipeline_steps.id"), nullable=True),
            sa.Column("reviewer_id", sa.String(length=36), nullable=True),
            # decided_at 为空 = 待复核；decision 三态（§6.4-2）
            sa.Column("decision", sa.String(length=20), nullable=True),
            sa.Column("comments", sa.Text(), nullable=True),
            sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("sla_due_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.CheckConstraint(
                "decision IS NULL OR decision IN ("
                + ", ".join(f"'{s}'" for s in REVIEW_DECISIONS) + ")",
                name="ck_review_tasks_decision",
            ),
        )
        op.create_index("ix_review_tasks_run", "review_tasks", ["run_id"])
        op.create_index("ix_review_tasks_tenant_pending", "review_tasks", ["tenant_id", "decision"])

    if conn.dialect.name == "postgresql":
        op.execute(
            "COMMENT ON TABLE step_evidence IS "
            "'步级证据（总纲 §6.4-8）：发布类步骤必须外部核验（平台ID/URL/截图）才置 verified。'"
        )


def downgrade() -> None:
    conn = op.get_bind()
    for t in ("review_tasks", "step_evidence"):
        if _table_exists(conn, t):
            op.drop_table(t)
