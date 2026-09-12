"""wangcai sessions and qa log

Revision ID: 094
Revises: 091
Create Date: 2026-08-31

总纲 §7A.3 / 实施指南 3.4 定稿：旺财访客会话与问答日志。
- chat_sessions 不可复用（user_id NOT NULL，公开访客无账号，实测 models/chat_session.py L18）；
- wangcai_sessions 用匿名 visitor_ref；会话与租户绑定（访客串站=数据事故，指南 3.6）；
- wangcai_qa_log 一表两用：N3 多轮上下文 + N7 经验证据（citation_refs/lead_converted）；
- 隐私：访客会话属个人数据，90 天过期清理走现有 gdpr 策略（指南 3.1）。
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
revision: str = '094'
down_revision: Union[str, None] = '091'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


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

    if not _table_exists(conn, "wangcai_sessions"):
        op.create_table(
            "wangcai_sessions",
            sa.Column("id", _uuid_col(), primary_key=True),
            sa.Column("tenant_id", _uuid_col(), sa.ForeignKey("tenants.id"), nullable=False),
            sa.Column("visitor_ref", sa.String(length=128), nullable=False),
            sa.Column("language", sa.String(length=10), nullable=True),
            sa.Column("intent_history", sa.Text(), nullable=True),  # JSON 数组
            sa.Column("summary", sa.Text(), nullable=True),          # 超窗摘要（指南 3.2）
            sa.Column("turn_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(
            "uq_wangcai_sessions_tenant_visitor", "wangcai_sessions",
            ["tenant_id", "visitor_ref"], unique=True,
        )
        op.create_index("ix_wangcai_sessions_last_active", "wangcai_sessions", ["last_active_at"])

    if not _table_exists(conn, "wangcai_qa_log"):
        op.create_table(
            "wangcai_qa_log",
            sa.Column("id", _uuid_col(), primary_key=True),
            sa.Column("tenant_id", _uuid_col(), sa.ForeignKey("tenants.id"), nullable=False),
            sa.Column("session_id", _uuid_col(), sa.ForeignKey("wangcai_sessions.id"), nullable=True),
            sa.Column("role", sa.String(length=12), nullable=False),  # user | assistant
            sa.Column("intent", sa.String(length=40), nullable=True),
            sa.Column("content", sa.Text(), nullable=True),
            sa.Column("citation_refs", sa.Text(), nullable=True),     # JSON 数组（来源引用，Evidence）
            sa.Column("model", sa.String(length=60), nullable=True),  # N4/N8 计量
            sa.Column("tokens", sa.Integer(), nullable=True),
            sa.Column("lead_converted", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.CheckConstraint(
                "role IN ('user', 'assistant')", name="ck_wangcai_qa_log_role",
            ),
        )
        op.create_index("ix_wangcai_qa_log_session", "wangcai_qa_log", ["session_id"])
        op.create_index("ix_wangcai_qa_log_tenant_created", "wangcai_qa_log", ["tenant_id", "created_at"])

    if conn.dialect.name == "postgresql":
        op.execute(
            "COMMENT ON TABLE wangcai_qa_log IS "
            "'旺财问答日志（总纲 §7A.3）：N3 上下文 + N7 证据一表两用；90 天清理走 gdpr 策略。'"
        )


def downgrade() -> None:
    conn = op.get_bind()
    for t in ("wangcai_qa_log", "wangcai_sessions"):
        if _table_exists(conn, t):
            op.drop_table(t)
