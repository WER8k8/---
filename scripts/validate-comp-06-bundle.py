#!/usr/bin/env python3
"""COMP-06 · 律师复审附件包完整性校验."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "docs/compliance/comp-evidence-bundle.json"
REPORT = ROOT / "docs/compliance/comp-06-validation-latest.json"


def main() -> int:
    bundle = json.loads(BUNDLE.read_text(encoding="utf-8"))
    checks: dict[str, bool] = {}

    for key in ("soft_copyright_catalog", "rz_60_pages", "forbidden_list"):
        rel = bundle.get(key, "")
        path = ROOT / rel
        checks[key] = path.exists()

    notices = bundle.get("open_source_notices", "docs/OPEN-SOURCE-NOTICES.md")
    notices_path = ROOT / notices if not (ROOT / notices).exists() else ROOT / notices
    if not notices_path.exists():
        notices_path = ROOT / "docs" / notices
    checks["open_source_notices"] = notices_path.exists()

    rz_dir = ROOT / bundle.get("rz_60_pages", "docs/compliance/rz-60-pages")
    page_count = len(list(rz_dir.glob("page-*.txt"))) if rz_dir.is_dir() else 0
    checks["rz_60_page_count"] = page_count >= 60

    meta = rz_dir / "meta.json"
    if meta.exists():
        m = json.loads(meta.read_text(encoding="utf-8"))
        checks["rz_meta_exported_60"] = m.get("exported") == 60
    else:
        checks["rz_meta_exported_60"] = False

    draft = ROOT / "docs/compliance/comp-06-lawyer-review-draft-20260602.md"
    checks["lawyer_draft"] = draft.exists()
    signoff = ROOT / "docs/compliance/comp-06-lawyer-signoff-record.json"
    checks["lawyer_signoff_record"] = signoff.is_file()

    ok = all(checks.values())
    report = {"ok": ok, "task": "COMP-06", "checks": checks, "bundle": str(BUNDLE.relative_to(ROOT))}
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
