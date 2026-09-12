#!/usr/bin/env python3
"""校验 B2B 拓客开源清单是否已登记进 foreign_trade_ecosystem_catalog.json。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "backend" / "app" / "data" / "foreign_trade_ecosystem_catalog.json"

REQUIRED_BENCHMARK_IDS = (
    "ai_find_customer",
    "linkedin_scraper",
    "media_crawler",
    "customs_data_spider",
    "openclaw",
    "mymailclaw",
    "b2b_lead_generator_apify",
    "domain_email_extractor",
)

REQUIRED_SKILL_IDS = (
    "domain_email_extract",
    "linkedin_decision_maker",
    "social_lead_intel",
    "customs_trade_intel",
)


def main() -> int:
    if not CATALOG.is_file():
        print(f"FAIL missing catalog: {CATALOG}")
        return 1
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    bench_ids = {b.get("id") for b in data.get("benchmark_sources", [])}
    skill_ids = {s.get("id") for s in data.get("skills_registry", [])}
    missing_b = [i for i in REQUIRED_BENCHMARK_IDS if i not in bench_ids]
    missing_s = [i for i in REQUIRED_SKILL_IDS if i not in skill_ids]
    if missing_b or missing_s:
        if missing_b:
            print("FAIL benchmark_sources missing:", ", ".join(missing_b))
        if missing_s:
            print("FAIL skills_registry missing:", ", ".join(missing_s))
        return 1
    version = data.get("catalog_version", "?")
    print(f"OK b2b-opensource-matrix catalog_version={version}")
    print(f"  benchmarks={len(bench_ids)} skills={len(skill_ids)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
