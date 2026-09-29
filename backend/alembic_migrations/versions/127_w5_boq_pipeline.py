# -*- coding: utf-8 -*-
"""127 — W5 BOQ 导入管道：boq_import_jobs + boq_line_items（修正设计稿 模块3 / Gate G6）

背景：22 参数核价引擎已存在（services/boq_calculator.py），但
「标书 → 抽取 → 单位归一 → 产品匹配 → 人工复核 → 核价」前置管道缺失。
本迁移建立管道两表 + 状态机（禁止 extracted → quote 跳步，门控在服务层）。

幂等建表（先 inspect），与 119~126 同风格。
依赖：down_revision = 126_w5_pricing_rules
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "127_w5_boq_pipeline"
down_revision: Union[str, None] = "126_w5_pricing_rules"
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

    if "boq_import_jobs" not in tables:
        op.create_table(
            "boq_import_jobs",
            sa.Column("id", UUID_TYPE, primary_key=True),
            sa.Column("tenant_id", UUID_TYPE, nullable=False),
            sa.Column("source_name", sa.String(length=255), nullable=True),
            sa.Column("source_artifact_id", sa.String(length=100), nullable=True),
            sa.Column("status", sa.String(length=30), nullable=False, server_default="uploaded"),
            sa.Column("extractor", sa.String(length=40), nullable=True),
            sa.Column("extractor_version", sa.String(length=30), nullable=True),
            sa.Column("confidence", sa.Float(), nullable=True),
            sa.Column("defaults_json", sa.JSON(), nullable=True),
            sa.Column("result_json", sa.JSON(), nullable=True),
            sa.Column("error_code", sa.String(length=60), nullable=True),
            sa.Column("error_detail", sa.Text(), nullable=True),
            sa.Column("trace_id", sa.String(length=100), nullable=True),
            sa.Column("created_by", sa.String(length=100), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_boq_jobs_tenant_status", "boq_import_jobs", ["tenant_id", "status"])
        op.create_index("ix_boq_import_jobs_tenant_id", "boq_import_jobs", ["tenant_id"])
        op.create_index("ix_boq_import_jobs_status", "boq_import_jobs", ["status"])

    if "boq_line_items" not in tables:
        op.create_table(
            "boq_line_items",
            sa.Column("id", UUID_TYPE, primary_key=True),
            sa.Column("boq_job_id", UUID_TYPE, sa.ForeignKey("boq_import_jobs.id"), nullable=False),
            sa.Column("source_row", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("raw_description", sa.Text(), nullable=True),
            sa.Column("raw_quantity", sa.String(length=50), nullable=True),
            sa.Column("raw_unit", sa.String(length=30), nullable=True),
            sa.Column("normalized_description", sa.Text(), nullable=True),
            sa.Column("normalized_quantity", sa.Float(), nullable=True),
            sa.Column("normalized_unit", sa.String(length=20), nullable=True),
            sa.Column("candidate_products", sa.JSON(), nullable=True),
            sa.Column("selected_product_id", UUID_TYPE, nullable=True),
            sa.Column("match_confidence", sa.Float(), nullable=True),
            sa.Column("review_status", sa.String(length=30), nullable=False, server_default="pending"),
            sa.Column("reject_reason", sa.String(length=255), nullable=True),
            sa.Column("source_evidence_ref", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_boq_line_items_boq_job_id", "boq_line_items", ["boq_job_id"])
        op.create_index("ix_boq_line_items_review_status", "boq_line_items", ["review_status"])


def downgrade() -> None:
    tables = _table_names()
    if "boq_line_items" in tables:
        indexes = _index_names("boq_line_items")
        for ix in ("ix_boq_line_items_review_status", "ix_boq_line_items_boq_job_id"):
            if ix in indexes:
                op.drop_index(ix, table_name="boq_line_items")
        op.drop_table("boq_line_items")
    if "boq_import_jobs" in tables:
        indexes = _index_names("boq_import_jobs")
        for ix in ("ix_boq_import_jobs_status", "ix_boq_import_jobs_tenant_id", "ix_boq_jobs_tenant_status"):
            if ix in indexes:
                op.drop_index(ix, table_name="boq_import_jobs")
        op.drop_table("boq_import_jobs")
