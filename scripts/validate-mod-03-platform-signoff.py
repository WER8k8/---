#!/usr/bin/env python3
"""MOD-03 · 40 平台 PM 签字记录与 catalog 对齐校验."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/mod-03-platform-signoff-latest.json"
RECORD = ROOT / "docs/compliance/mod-03-platform-signoff-record.json"
CHECKLIST = ROOT / "docs/compliance/MOD-03-forty-platform-signoff-checklist.md"

sys.path.insert(0, str(ROOT / "backend"))
from app.services.platform_catalog import PLATFORMS_CN, PLATFORMS_GLOBAL, all_catalog_rows  # noqa: E402


def ensure_record() -> dict:
    if RECORD.is_file():
        return json.loads(RECORD.read_text(encoding="utf-8"))
    rows = all_catalog_rows()
    data = {
        "task": "MOD-03",
        "status": "pending_pm_signoff",
        "catalog_source": "backend/app/services/platform_catalog.py",
        "expected_count": 40,
        "platforms_cn": [n for n, *_ in PLATFORMS_CN],
        "platforms_global": [n for n, *_ in PLATFORMS_GLOBAL],
        "checklist": str(CHECKLIST.relative_to(ROOT)).replace("\\", "/"),
        "signatory_role": "产品经理",
        "signed_by": None,
        "signed_at": None,
        "notes": "PM 确认 40 平台正式表与 catalog 一致后签字",
    }
    RECORD.parent.mkdir(parents=True, exist_ok=True)
    RECORD.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return data


def main() -> int:
    record = ensure_record()
    catalog_names = {n for n, *_ in all_catalog_rows()}
    listed = set(record.get("platforms_cn", [])) | set(record.get("platforms_global", []))
    checks = {
        "record_json": RECORD.is_file(),
        "checklist_md": CHECKLIST.is_file(),
        "catalog_count_40": len(catalog_names) == 40,
        "record_lists_40": len(listed) == 40,
        "record_matches_catalog": listed == catalog_names,
    }
    signed = bool(record.get("signed_by"))
    ok = all(checks.values())
    out = {
        "ok": ok,
        "task": "MOD-03",
        "checks": checks,
        "signed": signed,
        "human_pending": not signed,
        "record": str(RECORD.relative_to(ROOT)),
    }
    REPORT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
