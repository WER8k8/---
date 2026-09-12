#!/usr/bin/env python3
"""PAT-02 · 新颖性检索 memo + 代理交接占位校验."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/pat-02-handoff-validation-latest.json"

REQUIRED = [
    ROOT / "docs/专利/PAT-02-novelty-search-memo.md",
    ROOT / "docs/专利/PAT-02-agency-handoff-checklist.md",
    ROOT / "docs/专利/PAT-02-report-number.json",
    ROOT / "docs/专利/PAT-01-claims-code-mapping.md",
]


def main() -> int:
    files_ok = {str(p.relative_to(ROOT)): p.is_file() for p in REQUIRED}
    report_num = json.loads((ROOT / "docs/专利/PAT-02-report-number.json").read_text(encoding="utf-8"))
    agency_number_filled = bool(report_num.get("search_report_number"))
    ok = all(files_ok.values())
    out = {
        "ok": ok,
        "task": "PAT-02",
        "files": files_ok,
        "search_report_number_filled": agency_number_filled,
        "human_pending": not agency_number_filled,
    }
    REPORT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
