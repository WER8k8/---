#!/usr/bin/env python3
"""PAT-02 · 代理机构回填检索号（PM/代理执行）.

Usage:
  python scripts/apply-pat-02-report-number.py --number CN2026XXXX --agency "某某专利代理"
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "docs/专利/PAT-02-report-number.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Fill PAT-02 search report number")
    parser.add_argument("--number", required=True, help="检索报告编号")
    parser.add_argument("--agency", default=None, help="代理机构名称")
    parser.add_argument("--notes", default=None, help="备注")
    args = parser.parse_args()

    data = json.loads(RECORD.read_text(encoding="utf-8"))
    data["search_report_number"] = args.number.strip()
    if args.agency:
        data["agency_name"] = args.agency.strip()
    if args.notes:
        data["notes"] = args.notes.strip()
    data["status"] = "complete"
    data["received_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    RECORD.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "record": str(RECORD.relative_to(ROOT)), "status": data["status"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
