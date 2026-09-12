#!/usr/bin/env python3
"""MOD-05 · staging DB 表存在性校验（025/026 迁移产物）."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/mod-05-staging-migrate-latest.json"

TABLES = (
    "ubrain_tenant_memory",
    "buyer_prospect_leads",
    "ubrain_research_insights",
    "ubrain_pipeline_runs",
    "ubrain_feedback_snapshots",
)


def main() -> int:
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql://youding:youding@127.0.0.1:5433/youding_dev",
    )
    try:
        from sqlalchemy import create_engine, inspect

        names = set(inspect(create_engine(url)).get_table_names())
    except Exception as exc:
        report = {"ok": False, "task": "MOD-05-staging-tables", "error": str(exc)}
        REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1

    missing = [t for t in TABLES if t not in names]
    ok = not missing
    report = {
        "ok": ok,
        "task": "MOD-05-staging-tables",
        "missing": missing,
        "checked": list(TABLES),
        "database_url": url.split("@")[-1] if "@" in url else "local",
    }
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
