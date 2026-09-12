#!/usr/bin/env python3
"""COMP-06 · 律师 S2 签字回填."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "docs/compliance/comp-06-lawyer-signoff-record.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Fill COMP-06 lawyer signoff")
    parser.add_argument("--name", required=True, help="签字律师姓名")
    parser.add_argument("--firm", required=True, help="律所名称")
    parser.add_argument("--notes", default=None)
    args = parser.parse_args()

    data = json.loads(RECORD.read_text(encoding="utf-8-sig")) if RECORD.is_file() else {"task": "COMP-06"}
    data["signed_by"] = args.name.strip()
    data["law_firm"] = args.firm.strip()
    data["status"] = "signed_s2"
    data["signed_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if args.notes:
        data["notes"] = args.notes.strip()
    RECORD.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "record": str(RECORD.relative_to(ROOT))}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
