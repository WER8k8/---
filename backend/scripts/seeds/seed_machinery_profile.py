# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""machinery（机械）行业参数包播种 —— 修正设计稿 模块2 / §6 非建材端到端验收。

纯数据操作（不改运行时）：写入 code="machinery" version=1 status="active" 的
IndustryProfile 及其最小必备 boq_rules（计价 6 键 + 材料识别 2 键）。

幂等性保证：按 (code, version) 判存，已存在则跳过，重复执行不产生重复行。

用法：
    .venv/Scripts/python.exe scripts/seeds/seed_machinery_profile.py
"""
from __future__ import annotations

import io
import json
import os
import sys
import uuid

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from sqlalchemy import text

from app.core.database import engine

MACHINERY_CODE = "machinery"
MACHINERY_VERSION = 1

# §6.1 最小必备键：计价 6 键（base_prices/densities/surface/edge/grade/moq）
# + 材料识别 2 键（material_tokens/default_material）。
MACHINERY_BOQ_RULES = {
    "material_base_prices": {"steel_plate": 420.0, "aluminum": 560.0, "cast_iron": 300.0},
    "material_densities": {"steel_plate": 7850, "aluminum": 2700, "cast_iron": 7200},
    "surface_fees": {"raw": 0.0, "painted": 8.0, "galvanized": 12.0},
    "edge_fees": {"none": 0.0, "machined": 15.0},
    "grade_multipliers": {"standard": 1.0, "precision": 1.25},
    "moq_tiers": [{"min_quantity_sqm": 100, "discount_rate": 0.03}],
    "material_tokens": {
        "steel_plate": ["steel plate", "钢板", "q235", "carbon steel"],
        "aluminum": ["aluminum", "铝", "6061"],
        "cast_iron": ["cast iron", "铸铁"],
    },
    "default_material": "steel_plate",
}


def run_seed() -> None:
    print("🚀 开始执行 [machinery 行业参数包播种]...")
    with engine.begin() as conn:
        exists = conn.execute(
            text(
                "SELECT 1 FROM industry_profiles WHERE code=:c AND version=:v"
            ),
            {"c": MACHINERY_CODE, "v": MACHINERY_VERSION},
        ).fetchone()
        if exists:
            print(f"⏭  {MACHINERY_CODE} v{MACHINERY_VERSION} 已存在，跳过（幂等）")
            return

        conn.execute(
            text(
                "INSERT INTO industry_profiles (id, code, name, version, status, unit_system, "
                "currency_defaults, incoterm_defaults, boq_rules, ui_labels, metadata, "
                "created_at, updated_at) "
                "VALUES (:id, :code, :name, :version, 'active', 'metric', "
                ":cur, :inc, :rules, :labels, :meta, NOW(), NOW())"
            ),
            {
                "id": str(uuid.uuid4()),
                "code": MACHINERY_CODE,
                "name": "机械制造（板材/结构件）",
                "version": MACHINERY_VERSION,
                "cur": json.dumps({"base": "USD"}, ensure_ascii=False),
                "inc": json.dumps(["FOB", "CIF", "DDP"], ensure_ascii=False),
                "rules": json.dumps(MACHINERY_BOQ_RULES, ensure_ascii=False),
                "labels": json.dumps({"unit_sqm": "平方米"}, ensure_ascii=False),
                "meta": json.dumps(
                    {"seeded_by": "seed_machinery_profile", "source": "模块2 §6.1"},
                    ensure_ascii=False,
                ),
            },
        )
        print(f"✅ 已播种 {MACHINERY_CODE} v{MACHINERY_VERSION}（active，纯数据）")


if __name__ == "__main__":
    run_seed()
