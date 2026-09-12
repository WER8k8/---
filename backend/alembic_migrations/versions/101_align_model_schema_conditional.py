"""101: 模型-Schema 对齐迁移（条件化加列，幂等）。

背景：
    模型层新增的部分列（inquiries 归因字段、products 多语言列、tenants.custom_domains、
    users.is_default_password 等）未及时写入迁移，导致 `create_all` 之外的存量库
    （如 uj_test@5432）查询时报 UndefinedColumn → 接口 500「服务器内部错误」。

设计：
    - 本迁移同时合并两个 head（097 与 100_rls_batch1_trade_core），统一迁移线。
    - 每列先通过 inspector 检查 information_schema，**缺失才加**（幂等），
      对已手动补列 / create_all 建过的库是安全 no-op。
    - 兼容 PostgreSQL 与 SQLite（UUID 列在非 PG 方言退化为 VARCHAR(36)）。

downgrade：
    仅删除本清单中存在的列（IF 存在才 drop）。会丢失这些列的数据，慎用。
"""
from __future__ import annotations

import logging
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect

# revision identifiers, used by Alembic.
revision: str = "101_align_model_schema_conditional"
# 合并当前全部 head：主线终点 100_rls_batch1_trade_core（088→089→100，088 挂 097）
# 与独立分支终点 060_merge_all_heads
down_revision: Union[str, Sequence[str], None] = (
    "100_rls_batch1_trade_core",
    "060_merge_all_heads",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger("alembic.env.align_model_schema")

# (表, 列名, 类型工厂, server_default, nullable)
# 类型工厂接收 bool is_postgresql，返回 sa 类型实例
UUID_PG = sa.dialects.postgresql.UUID(as_uuid=False)


def _uuid_type(is_pg: bool):
    return UUID_PG if is_pg else sa.String(length=36)


def _bool_default(is_pg: bool) -> str:
    return sa.text("TRUE") if is_pg else sa.text("1")


TARGET_COLUMNS: list[tuple[str, str, object, object, bool]] = [
    # ── content_pages ──
    ("content_pages", "featured_image", lambda pg: sa.String(length=500), None, True),
    ("content_pages", "deleted_at", lambda pg: sa.DateTime(timezone=True), None, True),
    # ── seo_metadata ──
    ("seo_metadata", "hreflang_tags", lambda pg: sa.Text(), None, True),
    ("seo_metadata", "structured_data", lambda pg: sa.Text(), None, True),
    # ── inquiries（归因 / MEDDPICC / 软删）──
    ("inquiries", "source_channel", lambda pg: sa.String(length=50), None, True),
    ("inquiries", "source_utm", lambda pg: sa.Text(), None, True),
    ("inquiries", "publish_task_id", lambda pg: sa.String(length=36), None, True),
    ("inquiries", "meddpicc_json", lambda pg: sa.Text(), None, True),
    ("inquiries", "source_url", lambda pg: sa.String(length=1000), None, True),
    ("inquiries", "source_keyword", lambda pg: sa.String(length=300), None, True),
    ("inquiries", "ai_search_engine", lambda pg: sa.String(length=50), None, True),
    ("inquiries", "attribution_channel", lambda pg: sa.String(length=50), None, True),
    ("inquiries", "attribution_data", lambda pg: sa.Text(), None, True),
    ("inquiries", "customer_finder_id", lambda pg: sa.String(length=36), None, True),
    ("inquiries", "deleted_at", lambda pg: sa.DateTime(timezone=True), None, True),
    # ── products（多语言字段 / 软删）──
    ("products", "specifications_text", lambda pg: sa.String(length=200), None, True),
    ("products", "name_en", lambda pg: sa.String(length=200), None, True),
    ("products", "subtitle_en", lambda pg: sa.String(length=300), None, True),
    ("products", "description_en", lambda pg: sa.Text(), None, True),
    ("products", "technical_params_en", lambda pg: sa.Text(), None, True),
    ("products", "advantages_en", lambda pg: sa.Text(), None, True),
    ("products", "application_scenarios_en", lambda pg: sa.Text(), None, True),
    ("products", "meta_title_en", lambda pg: sa.String(length=200), None, True),
    ("products", "meta_description_en", lambda pg: sa.String(length=500), None, True),
    ("products", "deleted_at", lambda pg: sa.DateTime(timezone=True), None, True),
    # ── tenants ──
    ("tenants", "custom_domains", lambda pg: sa.Text(), None, True),
    ("tenants", "purchased_token_bonus", lambda pg: sa.Integer(), sa.text("0"), False),
    # ── users ──
    ("users", "role_id", _uuid_type, None, True),
    ("users", "is_default_password", lambda pg: sa.Boolean(), _bool_default, False),
]


def _existing_columns(bind, table: str) -> set[str]:
    insp = sa_inspect(bind)
    if not insp.has_table(table):
        return set()
    return {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"
    for table, col, type_fn, srv_default, nullable in TARGET_COLUMNS:
        existing = _existing_columns(bind, table)
        if col in existing:
            logger.info("skip %s.%s (already exists)", table, col)
            continue
        if not existing:
            logger.warning("table %s missing entirely; skip column %s", table, col)
            continue
        default = srv_default(is_pg) if callable(srv_default) else srv_default
        op.add_column(
            table,
            sa.Column(col, type_fn(is_pg), nullable=nullable, server_default=default),
        )
        logger.info("added %s.%s", table, col)


def downgrade() -> None:
    bind = op.get_bind()
    for table, col, _type_fn, _srv_default, _nullable in TARGET_COLUMNS:
        if col in _existing_columns(bind, table):
            op.drop_column(table, col)
            logger.info("dropped %s.%s", table, col)
