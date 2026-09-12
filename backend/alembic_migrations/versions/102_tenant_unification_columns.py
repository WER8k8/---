"""102: 租户归一 P0-4 —— 核心商业表补 tenant_id 列（条件化、幂等）。

背景（审计 2026-09-05 P0-4「租户身份双轨制」）：
    products / orders / quotes 三张核心商业表无 tenant_id 列，与
    rfqs/opportunities/campaigns/companies 等既有 tenant_id 体系并存，
    构成双轨制——RLS 蓝图（app/db/rls_policies.py 以 tenant_id 为主键）
    无法覆盖这三张表，跨租户隔离只靠人工过滤纪律。

裁决（ADR-001，见 docs/adr/ADR-001-tenant-unification.md）：
    以 tenant_id 为唯一租户维度；merchant_id/buyer_id 保留为交易对手
    用户外键（非租户维度）；三表补 tenant_id（nullable=True，存量数据
    不背书租户归属，写入方逐步补真值；非空约束留待数据回填后的独立迁移）。

设计（沿用 101 的条件化模式）：
    - 每列先 inspector 查 information_schema，缺失才加（幂等）。
    - PostgreSQL 用 UUID，非 PG 退化为 VARCHAR(36)。
    - 同时建索引（idx_<table>_tenant_id，条件化，已存在则跳过）。
    - 不设 server_default：租户归属必须由写入方显式提供。

downgrade：
    条件化删除本迁移新增的列与索引。
"""
from __future__ import annotations

import logging
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect

# revision identifiers, used by Alembic.
revision: str = "102_tenant_unification_columns"
down_revision: Union[str, Sequence[str], None] = "101_align_model_schema_conditional"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger("alembic.env.tenant_unification")

UUID_PG = sa.dialects.postgresql.UUID(as_uuid=False)


def _uuid_type(is_pg: bool):
    return UUID_PG if is_pg else sa.String(length=36)


# (表, 列名, 是否建索引)
TARGET_COLUMNS: list[tuple[str, str, bool]] = [
    ("products", "tenant_id", True),
    ("orders", "tenant_id", True),
    ("quotes", "tenant_id", True),
]


def _existing_columns(bind, table: str) -> set[str]:
    insp = sa_inspect(bind)
    if table not in insp.get_table_names():
        return set()
    return {c["name"] for c in insp.get_columns(table)}


def _existing_indexes(bind, table: str) -> set[str]:
    insp = sa_inspect(bind)
    if table not in insp.get_table_names():
        return set()
    return {idx["name"] for idx in insp.get_indexes(table)}


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"
    for table, col, build_index in TARGET_COLUMNS:
        existing = _existing_columns(bind, table)
        if not existing:
            logger.warning("table %s missing entirely; skip column %s", table, col)
            continue
        if col in existing:
            logger.info("skip %s.%s (already exists)", table, col)
        else:
            op.add_column(table, sa.Column(col, _uuid_type(is_pg), nullable=True))
            logger.info("added %s.%s", table, col)
        if build_index:
            idx_name = f"ix_{table}_{col}"
            if idx_name not in _existing_indexes(bind, table):
                op.create_index(idx_name, table, [col])
                logger.info("created index %s", idx_name)


def downgrade() -> None:
    bind = op.get_bind()
    for table, col, build_index in TARGET_COLUMNS:
        existing = _existing_columns(bind, table)
        if not existing:
            continue
        if build_index:
            idx_name = f"ix_{table}_{col}"
            if idx_name in _existing_indexes(bind, table):
                op.drop_index(idx_name, table_name=table)
        if col in existing:
            op.drop_column(table, col)
