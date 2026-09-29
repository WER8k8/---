# -*- coding: utf-8 -*-
"""126 — W5 定价规则版本化：billing_pricing_rules（修正设计稿 模块14.2 / 第二层缺口 A）

解决的问题：账单必须能回答"当时为什么按这个价格结算"——
- (rule_code, version) 唯一；改价 = 新版本行（append-only，不改旧行）；
- status draft/active/retired + 生效窗口 effective_from/to；plan_id 空 = 通用价；
- 结算快照写 billing_reservations.pricing_snapshot（模块14.2），本表后续修改
  不影响已生成快照。

设计：幂等建表，与 119~125 同风格。依赖：down_revision = 125_w5_rls_first_batch
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "126_w5_pricing_rules"
down_revision: Union[str, None] = "125_w5_rls_first_batch"
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

    if "billing_pricing_rules" in _table_names():
        return
    op.create_table(
        "billing_pricing_rules",
        sa.Column("id", UUID_TYPE, primary_key=True),
        sa.Column("rule_code", sa.String(length=80), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("meter_code", sa.String(length=60), nullable=False),
        sa.Column("plan_id", UUID_TYPE, nullable=True),
        sa.Column("unit_price_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="CNY"),
        sa.Column("free_quota", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("minimum_charge_cents", sa.Integer(), nullable=True),
        sa.Column("maximum_charge_cents", sa.Integer(), nullable=True),
        sa.Column("conditions", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("rule_code", "version", name="uq_pricing_rule_code_version"),
    )
    op.create_index("ix_pricing_rule_meter_status", "billing_pricing_rules", ["meter_code", "status"])
    op.create_index("ix_pricing_rule_effective", "billing_pricing_rules", ["meter_code", "effective_from"])
    op.create_index("ix_billing_pricing_rules_plan_id", "billing_pricing_rules", ["plan_id"])


def downgrade() -> None:
    if "billing_pricing_rules" not in _table_names():
        return
    indexes = _index_names("billing_pricing_rules")
    for ix in (
        "ix_billing_pricing_rules_plan_id",
        "ix_pricing_rule_effective",
        "ix_pricing_rule_meter_status",
    ):
        if ix in indexes:
            op.drop_index(ix, table_name="billing_pricing_rules")
    op.drop_table("billing_pricing_rules")
