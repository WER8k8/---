#!/usr/bin/env python3
"""将 PM-01～07 在交付物就绪后标为 done。"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "docs" / "dev-sprint-all-in-one.json"
DEL = ROOT / "docs" / "pm-deliverables"


def main() -> None:
    if not DEL.is_dir():
        raise SystemExit("run export-pm-deliverables.py first")
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    n = 0
    for t in data.get("tasks", []):
        if t.get("id", "").startswith("PM-") and DEL.glob(f"{t['id']}*"):
            if t.get("status") != "done":
                t["status"] = "done"
                n += 1
    JSON_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"marked {n} PM tasks done")


if __name__ == "__main__":
    main()
