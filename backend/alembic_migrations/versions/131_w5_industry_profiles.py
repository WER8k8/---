# -*- coding: utf-8 -*-
"""131 — W5 Industry Profile 行业参数包表（修正设计稿 模块2 / 第一章去行业化）

- industry_profiles：(code, version) 唯一，版本化；status draft/active/retired。
- boq_rules 携带核价引擎参数包（材料基价/密度/工艺费/等级系数/MOQ 档），
  由 boq_calculator.calculate(params, industry_profile=...) 可选注入；
  未传 → 建材默认，行为零漂移。
- 幂等建表 + 幂等播种 code="building_materials" v1（active）。

依赖：down_revision = 130_w5_attribution_fulfillment_substates

⚠ 冻结副本（勿改）：本文件在 upgrade 中内联的建材默认 boq_rules（基价表 / MOQ 档）
  已冻结。真源见 `app/services/boq_calculator._MATERIAL_BASE_PRICES` /
  `_DEFAULT_MOQ_TIERS`（服务层 seed_default_building_materials 亦复用这两个常量）。
  如需变更这些数值，须走**新迁移**，不要就地改本文件（历史迁移一经执行即不可变）。
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "131_w5_industry_profiles"
down_revision: Union[str, None] = "130_w5_attribution_fulfillment_substates"
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
    import json
    import uuid

    from app.core.database import UUID_TYPE

    tables = _table_names()

    if "industry_profiles" not in tables:
        op.create_table(
            "industry_profiles",
            sa.Column("id", UUID_TYPE, primary_key=True),
            sa.Column("code", sa.String(length=60), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
            sa.Column("unit_system", sa.String(length=30), nullable=False, server_default="metric"),
            sa.Column("currency_defaults", sa.JSON(), nullable=True),
            sa.Column("incoterm_defaults", sa.JSON(), nullable=True),
            sa.Column("product_schema", sa.JSON(), nullable=True),
            sa.Column("technical_fields", sa.JSON(), nullable=True),
            sa.Column("commercial_fields", sa.JSON(), nullable=True),
            sa.Column("certification_schema", sa.JSON(), nullable=True),
            sa.Column("boq_rules", sa.JSON(), nullable=True),
            sa.Column("seo_taxonomy", sa.JSON(), nullable=True),
            sa.Column("content_taxonomy", sa.JSON(), nullable=True),
            sa.Column("fulfillment_rules", sa.JSON(), nullable=True),
            sa.Column("ui_labels", sa.JSON(), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("code", "version", name="uq_industry_profile_code_version"),
        )
        op.create_index("ix_industry_profiles_code", "industry_profiles", ["code"])
        op.create_index("ix_industry_profiles_status", "industry_profiles", ["status"])

    # 幂等播种建材默认包 v1（active）——boq_rules 与引擎内置默认一致，行为零漂移
    # （冻结副本：真源见 boq_calculator._MATERIAL_BASE_PRICES / _DEFAULT_MOQ_TIERS；变更须走新迁移）
    bind = op.get_bind()
    exists = bind.execute(
        sa.text("SELECT 1 FROM industry_profiles WHERE code=:c AND version=1"),
        {"c": "building_materials"},
    ).fetchone()
    if not exists:
        boq_rules = {
            "material_base_prices": {"marble": 80.0, "granite": 60.0, "ceramic": 25.0, "wood": 45.0, "metal": 120.0},
            "material_densities": {"marble": 2700, "granite": 2800, "ceramic": 2200, "wood": 800, "metal": 7850},
            "surface_fees": {"polished": 0.0, "honed": 2.0, "flamed": 4.0, "bush_hammered": 6.0, "sandblasted": 5.0, "brushed": 3.5},
            "edge_fees": {"flat": 0.0, "eased": 0.0, "beveled": 2.0, "half_bullnose": 3.5, "full_bullnose": 5.0, "ogee": 7.0},
            "grade_multipliers": {"a": 1.15, "premium": 1.15, "first_choice": 1.10, "standard": 1.0, "commercial": 0.90, "b": 0.85},
            "moq_tiers": [
                {"min_quantity_sqm": 1000, "discount_rate": 0.05},
                {"min_quantity_sqm": 3000, "discount_rate": 0.08},
            ],
        }
        bind.execute(
            sa.text(
                "INSERT INTO industry_profiles (id, code, name, version, status, unit_system, "
                "currency_defaults, incoterm_defaults, boq_rules, ui_labels, metadata, created_at, updated_at) "
                "VALUES (:id, :code, :name, 1, 'active', 'metric', :cur, :inc, :rules, :labels, :meta, NOW(), NOW())"
            ),
            {
                "id": str(uuid.uuid4()),
                "code": "building_materials",
                "name": "建材（默认行业包）",
                "cur": '{"base": "USD"}',
                "inc": '["FOB", "CIF", "DDP"]',
                "rules": json.dumps(boq_rules),
                "labels": '{"unit_sqm": "平方米"}',
                "meta": '{"seeded_by": "131_w5_industry_profiles"}',
            },
        )


def downgrade() -> None:
    if "industry_profiles" not in _table_names():
        return
    indexes = _index_names("industry_profiles")
    for ix in ("ix_industry_profiles_status", "ix_industry_profiles_code"):
        if ix in indexes:
            op.drop_index(ix, table_name="industry_profiles")
    op.drop_table("industry_profiles")
