# -*- coding: utf-8 -*-
"""129 — W5 DSH 沙箱安全审计：harness_security_events（修正设计稿 模块15.6 / Gate G10）

背景：DSH 此前仅 tenant_id 参数级校验（代码约定隔离）。本表承接沙箱治理审计：
网络 allowlist 放行/拒绝、生产模式违规、令牌验签失败等（append-only），
字段对齐设计稿 15.6：tenant_id/task_id/network_target/operation/policy/decision/trace_id。

幂等建表（先 inspect），与 119~128 同风格。
依赖：down_revision = 128_w5_tracking_events
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "129_w5_harness_security_events"
down_revision: Union[str, None] = "128_w5_tracking_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_names() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _index_names(table: str) -> set[str]:
    try:
        return {i["name"] for i in sa.inspect(op.get_bind()).get_indexes(table)}
    except Exception:  # noqa: BLE001
        return set()


def upgrade() -> None:
    from app.core.database import UUID_TYPE

    if "harness_security_events" in _table_names():
        return
    op.create_table(
        "harness_security_events",
        sa.Column("id", UUID_TYPE, primary_key=True),
        sa.Column("tenant_id", UUID_TYPE, nullable=True),
        sa.Column("task_id", sa.String(length=100), nullable=True),
        sa.Column("network_target", sa.String(length=255), nullable=True),
        sa.Column("operation", sa.String(length=60), nullable=False),
        sa.Column("policy", sa.String(length=60), nullable=False),
        sa.Column("decision", sa.String(length=20), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("trace_id", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_harness_sec_tenant_created", "harness_security_events", ["tenant_id", "created_at"])
    op.create_index("ix_harness_sec_decision", "harness_security_events", ["decision"])
    op.create_index("ix_harness_security_events_tenant_id", "harness_security_events", ["tenant_id"])


def downgrade() -> None:
    if "harness_security_events" not in _table_names():
        return
    indexes = _index_names("harness_security_events")
    for ix in ("ix_harness_security_events_tenant_id", "ix_harness_sec_decision", "ix_harness_sec_tenant_created"):
        if ix in indexes:
            op.drop_index(ix, table_name="harness_security_events")
    op.drop_table("harness_security_events")
