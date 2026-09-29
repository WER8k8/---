# -*- coding: utf-8 -*-
"""124 — W5 计费预占状态机：billing_reservations + meter_events 业务主体增列

背景（修正设计稿 模块18 / 模块10.2 / Gate G9）：
- 重复扣费防线：业务幂等身份（tenant+meter_code+subject+event_version）唯一约束落库，
  状态机 created→reserved→settled|released；settled→reversed；非法跃迁服务层拒绝。
- settle 落 finance_ledger 恰好一条营收分录；reverse 写负向冲正（红线 R3：不新建账本）。
- meter_events 增列（模块10.2，全部可空、向后兼容）：meter_code / subject_type /
  subject_id / pricing_rule_version / pricing_snapshot / bill_status。

设计：幂等（inspect 后再建/加列），与 119~123 同风格。
依赖：down_revision = 123_w5_tenant_domains
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "124_w5_billing_reservations"
down_revision: Union[str, None] = "123_w5_tenant_domains"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_names() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _column_names(table: str) -> set[str]:
    try:
        return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)}
    except Exception:  # noqa: BLE001
        return set()


def _index_names(table: str) -> set[str]:
    try:
        return {i["name"] for i in sa.inspect(op.get_bind()).get_indexes(table)}
    except Exception:  # noqa: BLE001
        return set()


def upgrade() -> None:
    from app.core.database import UUID_TYPE

    tables = _table_names()

    # ── 1) billing_reservations ─────────────────────────────────
    if "billing_reservations" not in tables:
        op.create_table(
            "billing_reservations",
            sa.Column("id", UUID_TYPE, primary_key=True),
            sa.Column("tenant_id", UUID_TYPE, nullable=False),
            sa.Column("meter_code", sa.String(length=60), nullable=False),
            sa.Column("subject_type", sa.String(length=40), nullable=False),
            sa.Column("subject_id", sa.String(length=100), nullable=False),
            sa.Column("event_version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("idempotency_key", sa.String(length=200), nullable=False),
            sa.Column("pricing_rule_version", sa.String(length=30), nullable=False, server_default="v0"),
            sa.Column("pricing_snapshot", sa.JSON(), nullable=True),
            sa.Column("amount_cents", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("currency", sa.String(length=8), nullable=False, server_default="CNY"),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="created"),
            sa.Column("history_json", sa.JSON(), nullable=True),
            sa.Column("last_reason", sa.Text(), nullable=True),
            sa.Column("trace_id", sa.String(length=100), nullable=True),
            sa.Column("finance_entry_id", UUID_TYPE, nullable=True),
            sa.Column("reversal_entry_id", UUID_TYPE, nullable=True),
            sa.Column("reserved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("reversed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("idempotency_key", name="uq_billing_reservation_idem_key"),
        )
        op.create_index(
            "ix_billing_reservations_tenant_status", "billing_reservations", ["tenant_id", "status"]
        )
        op.create_index(
            "ix_billing_reservations_subject", "billing_reservations", ["subject_type", "subject_id"]
        )
        op.create_index("ix_billing_reservations_tenant_id", "billing_reservations", ["tenant_id"])
        op.create_index("ix_billing_reservations_status", "billing_reservations", ["status"])

    # ── 2) meter_events 增列（模块10.2，全部可空向后兼容）─────────
    if "meter_events" in tables:
        cols = _column_names("meter_events")
        additions = [
            ("meter_code", sa.String(length=60)),
            ("subject_type", sa.String(length=40)),
            ("subject_id", sa.String(length=100)),
            ("pricing_rule_version", sa.String(length=30)),
            ("pricing_snapshot", sa.JSON()),
            ("bill_status", sa.String(length=20)),
        ]
        for name, col_type in additions:
            if name not in cols:
                op.add_column("meter_events", sa.Column(name, col_type, nullable=True))
        if "meter_code" in _column_names("meter_events") and "ix_meter_events_meter_code" not in _index_names("meter_events"):
            op.create_index("ix_meter_events_meter_code", "meter_events", ["meter_code"])


def downgrade() -> None:
    tables = _table_names()
    if "meter_events" in tables:
        indexes = _index_names("meter_events")
        if "ix_meter_events_meter_code" in indexes:
            op.drop_index("ix_meter_events_meter_code", table_name="meter_events")
        cols = _column_names("meter_events")
        for name in ("bill_status", "pricing_snapshot", "pricing_rule_version", "subject_id", "subject_type", "meter_code"):
            if name in cols:
                op.drop_column("meter_events", name)
    if "billing_reservations" in tables:
        indexes = _index_names("billing_reservations")
        for ix in (
            "ix_billing_reservations_status",
            "ix_billing_reservations_tenant_id",
            "ix_billing_reservations_subject",
            "ix_billing_reservations_tenant_status",
        ):
            if ix in indexes:
                op.drop_index(ix, table_name="billing_reservations")
        op.drop_table("billing_reservations")
