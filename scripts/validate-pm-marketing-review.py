#!/usr/bin/env python3
"""PM×营销联合审查交付物门禁。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "docs/pm-marketing-full-journey-review-charter.md",
    "docs/pm-marketing-journey-review-matrix.md",
    "docs/pm-marketing-journey-review-signoff.json",
    "docs/pm-marketing-review-screenshots/README.md",
]

MATRIX_MIN_ROWS = 30


def main() -> int:
    missing: list[str] = []

    for rel in REQUIRED:
        if not (ROOT / rel).is_file():
            missing.append(f"missing:{rel}")

    matrix = ROOT / "docs" / "pm-marketing-journey-review-matrix.md"
    if matrix.is_file():
        body = matrix.read_text(encoding="utf-8", errors="replace")
        row_ids = [line for line in body.splitlines() if line.startswith("| ") and "|" in line[2:]]
        # exclude header/separator rows
        data_rows = [r for r in row_ids if not r.startswith("| ID") and not r.startswith("|----") and not r.startswith("| 步")]
        if len(data_rows) < MATRIX_MIN_ROWS:
            missing.append(f"matrix_rows:{len(data_rows)}<{MATRIX_MIN_ROWS}")

    signoff_path = ROOT / "docs" / "pm-marketing-journey-review-signoff.json"
    signoff_status = "scheduled"
    segment_count = 0
    if signoff_path.is_file():
        data = json.loads(signoff_path.read_text(encoding="utf-8"))
        signoff_status = data.get("status", "scheduled")
        segment_count = len(data.get("segments") or [])

    inventory = ROOT / "docs" / "pm-marketing-route-inventory-latest.json"
    route_count = 0
    if inventory.is_file():
        route_count = json.loads(inventory.read_text(encoding="utf-8")).get("route_count", 0)
    else:
        missing.append("hint:run export-admin-route-inventory.py")

    out = {
        "task": "PM-MKT-01",
        "docs_ok": len([m for m in missing if m.startswith("missing:")]) == 0,
        "matrix_ok": not any(m.startswith("matrix_rows") for m in missing),
        "signoff_status": signoff_status,
        "segments_recorded": segment_count,
        "route_inventory_count": route_count,
        "missing": missing,
        "hint": "会议完成后更新 signoff.json status=completed 并填写 segments/blockers",
    }
    latest = ROOT / "docs" / "pm-marketing-review-validation-latest.json"
    latest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    if any(m.startswith("missing:") or m.startswith("matrix_rows") for m in missing):
        print("PM-MKT review FAIL (deliverables)")
        for m in missing:
            print(f"  - {m}")
        return 1

    print(f"PM-MKT review PASS deliverables · signoff={signoff_status} · segments={segment_count}")
    if signoff_status != "completed":
        print("  (会议未关账：status 仍为 scheduled — 预期 exit 0)")
    return 0 if signoff_status == "completed" else 2


if __name__ == "__main__":
    sys.exit(main())
