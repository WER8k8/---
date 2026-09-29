# -*- coding: utf-8 -*-
"""122 — W5 统一消息可靠性层：Outbox / Inbox / DLQ 三表

背景（修正设计稿 模块17 / Production Gate G11）：
- 业务成功与消息投递解耦：业务事务内追加写 outbox_events（与业务同 commit/rollback），
  派发器（services/outbox_service.dispatch_pending，Celery beat 周期调用）异步投递。
- 消费幂等：inbox_events 以 (consumer, event_id) 唯一约束去重，重试/重放不产生重复副作用。
- 死信可运营：超过最大重试的事件留档 dead_letter_events，可人工复核后重放。

新增表：
    1. outbox_events       待投递业务事件（append-only；status: pending/processing/published/dead）
    2. inbox_events        消费幂等登记（(consumer, event_id) 唯一）
    3. dead_letter_events  死信留档（payload 内嵌，运营可重放）

设计：
- 全部操作幂等（先 inspect 表/索引是否存在），与 119/120/121 同风格。
- 列型经 app.core.database.UUID_TYPE（PG=原生 UUID / SQLite=String(36)），与 ORM 模型一致。
- downgrade 仅删本迁移新建对象。

依赖：down_revision = 121_w4_identity_attribution_persistence
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "122_w5_outbox_inbox_dlq"
down_revision: Union[str, None] = "121_w4_identity_attribution_persistence"
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

    tables = _table_names()

    # ── 1) outbox_events ─────────────────────────────────────────
    if "outbox_events" not in tables:
        op.create_table(
            "outbox_events",
            sa.Column("id", UUID_TYPE, primary_key=True),
            sa.Column("tenant_id", UUID_TYPE, nullable=True),
            sa.Column("event_type", sa.String(length=100), nullable=False),
            sa.Column("aggregate_type", sa.String(length=60), nullable=True),
            sa.Column("aggregate_id", sa.String(length=100), nullable=True),
            sa.Column("payload", sa.JSON(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
            sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_error", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_outbox_events_tenant_id", "outbox_events", ["tenant_id"])
        op.create_index("ix_outbox_events_event_type", "outbox_events", ["event_type"])
        op.create_index(
            "ix_outbox_status_next_retry", "outbox_events", ["status", "next_retry_at"]
        )
        op.create_index(
            "ix_outbox_aggregate", "outbox_events", ["aggregate_type", "aggregate_id"]
        )

    # ── 2) inbox_events ──────────────────────────────────────────
    if "inbox_events" not in tables:
        op.create_table(
            "inbox_events",
            sa.Column("id", UUID_TYPE, primary_key=True),
            sa.Column("consumer", sa.String(length=100), nullable=False),
            sa.Column("event_id", sa.String(length=100), nullable=False),
            sa.Column("event_type", sa.String(length=100), nullable=True),
            sa.Column("result", sa.String(length=255), nullable=True),
            sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("consumer", "event_id", name="uq_inbox_consumer_event"),
        )

    # ── 3) dead_letter_events ────────────────────────────────────
    if "dead_letter_events" not in tables:
        op.create_table(
            "dead_letter_events",
            sa.Column("id", UUID_TYPE, primary_key=True),
            sa.Column("event_id", sa.String(length=100), nullable=False),
            sa.Column("event_type", sa.String(length=100), nullable=True),
            sa.Column("tenant_id", UUID_TYPE, nullable=True),
            sa.Column("reason", sa.String(length=255), nullable=True),
            sa.Column("payload", sa.JSON(), nullable=True),
            sa.Column("last_error", sa.Text(), nullable=True),
            sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_dead_letter_events_event_id", "dead_letter_events", ["event_id"])


def downgrade() -> None:
    tables = _table_names()
    if "dead_letter_events" in tables:
        indexes = _index_names("dead_letter_events")
        if "ix_dead_letter_events_event_id" in indexes:
            op.drop_index("ix_dead_letter_events_event_id", table_name="dead_letter_events")
        op.drop_table("dead_letter_events")
    if "inbox_events" in tables:
        op.drop_table("inbox_events")
    if "outbox_events" in tables:
        indexes = _index_names("outbox_events")
        for ix in (
            "ix_outbox_aggregate",
            "ix_outbox_status_next_retry",
            "ix_outbox_events_event_type",
            "ix_outbox_events_tenant_id",
        ):
            if ix in indexes:
                op.drop_index(ix, table_name="outbox_events")
        op.drop_table("outbox_events")
