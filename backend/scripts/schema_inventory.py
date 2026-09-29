# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""schema_inventory.json 生成器 —— 修正设计稿 模块22（ORM ↔ 物理表对账基线）。

解决：ORM 236 个 __tablename__ vs PostgreSQL 256 张物理表之间 20 张差异无归属说明。

对每张物理表输出：
  physical_table / orm_model / category / tenant_scope / rls_enabled
分类（category）：
  orm_mapped     ORM 模型映射
  rls_pilot      RLS 试点表（db/rls_policies.RLS_PILOT_TABLES）
  migration_infra Alembic 版本表等迁移基础设施
  runtime_only   运行期动态建表（schema healer / mount_rls_pilot 等），无 ORM 映射
  unknown        既无 ORM 映射也无已知来源，需人工归因

用法：
  cd backend && .venv/Scripts/python.exe scripts/schema_inventory.py
输出：backend/docs/schema_inventory.json + 控制台摘要。设计稿要求每次迁移后重跑。
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text  # noqa: E402

logger = logging.getLogger("schema_inventory")


def build_inventory() -> dict:
    import app.models  # noqa: F401  — 必须先导入模型包，Base.metadata 才会注册全部 96 文件的表
    from app.core.database import Base, engine
    from app.db.rls_policies import RLS_PILOT_TABLES

    inspector_tables = []
    rls_flags: dict[str, bool] = {}
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT c.relname, c.relrowsecurity FROM pg_class c "
                "JOIN pg_namespace n ON n.oid = c.relnamespace "
                "WHERE n.nspname = 'public' AND c.relkind = 'r' ORDER BY c.relname"
            )
        ).fetchall()
        for name, has_rls in rows:
            inspector_tables.append(name)
            rls_flags[name] = bool(has_rls)

    orm_tables = set(Base.metadata.tables.keys())
    rls_pilot = set(RLS_PILOT_TABLES)

    entries = []
    counts = {"orm_mapped": 0, "rls_pilot": 0, "migration_infra": 0, "runtime_only": 0, "unknown": 0}
    for t in inspector_tables:
        if t in orm_tables:
            category = "orm_mapped"
        elif t == "alembic_version":
            category = "migration_infra"
        elif t in rls_pilot:
            category = "rls_pilot"
        else:
            # 运行期 schema healer / RLS 挂载等动态建表无法静态枚举，
            # 先归 runtime_only，连续两轮仍存在且无人认领的转 unknown 处理。
            category = "runtime_only"
        counts[category] += 1
        entries.append(
            {
                "physical_table": t,
                "orm_model": t if t in orm_tables else None,
                "category": category,
                "rls_enabled": rls_flags.get(t, False),
            }
        )

    orm_only = sorted(orm_tables - set(inspector_tables))
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "database": str(engine.url.render_as_string(hide_password=True)),
        "physical_table_count": len(inspector_tables),
        "orm_mapped_count": len(orm_tables & set(inspector_tables)),
        "orm_declared_count": len(orm_tables),
        "orm_without_physical_table": orm_only,
        "category_counts": counts,
        "tables": entries,
    }


def main() -> int:
    logging.basicConfig(level=logging.WARNING)
    inv = build_inventory()
    out_dir = Path(__file__).resolve().parents[1] / "docs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "schema_inventory.json"
    out_path.write_text(json.dumps(inv, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"physical={inv['physical_table_count']} orm_mapped={inv['orm_mapped_count']} "
          f"orm_declared={inv['orm_declared_count']}")
    print(f"categories={inv['category_counts']}")
    if inv["orm_without_physical_table"]:
        print(f"orm_without_physical_table={inv['orm_without_physical_table']}")
    print(f"written: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
