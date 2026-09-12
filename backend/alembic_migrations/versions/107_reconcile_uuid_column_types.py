"""107：对齐 ORM 模型与 PostgreSQL 实际列类型（消除 schema 漂移）。

背景（2026-09-10 实测，命令 `tools/db_probe.py --column-drift`）：
线上库相对模型层共有 22 处漂移。本迁移只处理属于**数据库侧**的那一半：

* 12 个列在模型里声明为 `UUID_TYPE`，库里却被建成 `character varying`。
  PG 下模型类型是 `UUID(as_uuid=False)`，于是任何与真正 `uuid` 列的 JOIN 都会报
  `operator does not exist: uuid = character varying`。卡住编排链的就是
  `platform_accounts.platform_id` —— 它导致租户平台位分配失败，
  进而让 `seed_dev_tenant_demo.py` 在编排路径上跑不通。
* 7 个列模型里声明了、库里从未建过（`quotes` 的版本/审批字段、
  `ai_model_configs.model_metadata`、`content_versions.change_note`）。

剩下 3 处（`keyword_rankings.id`、`merchant_im_routing.id`、
`building_material_specs.id`）是**模型侧**的退化：迁移 009 当初刻意建成
`sa.Integer()`，`keyword_ranking_history` 依赖这个整型主键，Pydantic 响应也
已声明 `id: int`。因此这 3 处改模型、不改库。

受影响的 17 张表当前行数均为 0，类型转换不会丢数据。每一步都幂等：
先读回当前类型，已一致则跳过 DDL，可重复执行。

Revision ID: 107_reconcile_uuid_column_types
Revises: c6b6225da363
Create Date: 2026-09-10
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "107_reconcile_uuid_column_types"
down_revision: Union[str, None] = "c6b6225da363"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (table, column) declared UUID_TYPE by the model but stored as varchar in PG.
UUID_COLUMNS: list[tuple[str, str]] = [
    ("case_studies", "product_id"),
    ("platform_accounts", "platform_id"),
    ("ubrain_research_insights", "source_job_id"),
    ("ubrain_pipeline_runs", "trigger_job_id"),
    ("ubrain_action_audits", "tenant_id"),
    ("ubrain_action_audits", "user_id"),
    ("site_analytics_events", "tenant_id"),
    ("site_analytics_events", "inquiry_id"),
    ("platform_survival_ledger_entries", "recorded_by_user_id"),
    ("content_feedback_checks", "content_id"),
    ("industry_patterns", "content_id"),
    ("task_traces", "parent_trace_id"),
]

# varchar width each column had before conversion, used by downgrade().
_LEGACY_WIDTH = {
    "platform_accounts.platform_id": 50,
}


def _column_type(bind, table: str, column: str) -> str | None:
    row = bind.execute(sa.text(
        "SELECT udt_name FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = :t AND column_name = :c"
    ), {"t": table, "c": column}).first()
    return row[0] if row else None


def _table_columns(bind, table: str) -> set[str]:
    return {
        row[0]
        for row in bind.execute(sa.text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = :t"
        ), {"t": table})
    }


def _has_index(bind, name: str) -> bool:
    return bool(bind.execute(sa.text(
        "SELECT 1 FROM pg_class WHERE relname = :n AND relkind = 'i'"
    ), {"n": name}).first())


def _add_missing(bind, table: str, columns: dict[str, sa.Column], index_columns: Sequence[str]) -> None:
    existing = _table_columns(bind, table)
    for name, column in columns.items():
        if name in existing:
            continue
        op.add_column(table, column)
    for name in index_columns:
        if name not in existing:
            continue
        index_name = f"ix_{table}_{name}"
        if not _has_index(bind, index_name):
            op.create_index(index_name, table, [name])


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        # SQLite stores uuid as String(36) by design; nothing to reconcile.
        return

    for table, column in UUID_COLUMNS:
        if _column_type(bind, table, column) == "uuid":
            continue
        op.execute(sa.text(
            f'ALTER TABLE "{table}" ALTER COLUMN "{column}" TYPE UUID '
            f'USING NULLIF(btrim("{column}"), \'\')::uuid'
        ))

    _add_missing(
        bind,
        "ai_model_configs",
        {"model_metadata": sa.Column("model_metadata", sa.JSON(), nullable=True)},
        [],
    )
    _add_missing(
        bind,
        "content_versions",
        {"change_note": sa.Column("change_note", sa.String(500), nullable=True)},
        [],
    )
    _add_missing(
        bind,
        "quotes",
        {
            "rfq_id": sa.Column("rfq_id", sa.dialects.postgresql.UUID(), nullable=True),
            "opportunity_id": sa.Column("opportunity_id", sa.dialects.postgresql.UUID(), nullable=True),
            "version": sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            "approved_by": sa.Column("approved_by", sa.String(36), nullable=True),
            "approved_at": sa.Column(
                "approved_at", sa.DateTime(timezone=True), nullable=True
            ),
        },
        ["rfq_id", "opportunity_id"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    existing_quotes = _table_columns(bind, "quotes")
    for name in ("approved_at", "approved_by", "version", "opportunity_id", "rfq_id"):
        if name in existing_quotes:
            if _has_index(bind, f"ix_quotes_{name}"):
                op.drop_index(f"ix_quotes_{name}", table_name="quotes")
            op.drop_column("quotes", name)
    if "change_note" in _table_columns(bind, "content_versions"):
        op.drop_column("content_versions", "change_note")
    if "model_metadata" in _table_columns(bind, "ai_model_configs"):
        op.drop_column("ai_model_configs", "model_metadata")

    for table, column in UUID_COLUMNS:
        if _column_type(bind, table, column) == "uuid":
            width = _LEGACY_WIDTH.get(f"{table}.{column}", 36)
            op.execute(sa.text(
                f'ALTER TABLE "{table}" ALTER COLUMN "{column}" TYPE '
                f'VARCHAR({width}) USING "{column}"::text'
            ))
