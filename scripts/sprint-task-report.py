#!/usr/bin/env python3
"""统计一口气冲刺任务开放数。Usage: python scripts/sprint-task-report.py"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "docs" / "dev-sprint-all-in-one.json"
OUT = ROOT / "docs" / "sprint-task-report-latest.json"


def main() -> int:
    data = json.loads(TASKS.read_text(encoding="utf-8"))
    tasks = data["tasks"]
    by_status: dict[str, int] = {}
    by_sprint: dict[str, dict[str, int]] = {}
    open_ids: list[str] = []

    for t in tasks:
        st = t.get("status", "todo")
        by_status[st] = by_status.get(st, 0) + 1
        sp = t.get("sprint", "?")
        by_sprint.setdefault(sp, {})
        by_sprint[sp][st] = by_sprint[sp].get(st, 0) + 1
        if st not in ("done", "pm_blocked"):
            open_ids.append(t["id"])

    gates = data.get("gates", [])
    gate_open = [g for g in gates if any(
        t["id"] == g and t.get("status") != "done" for t in tasks
    )]

    report = {
        "total": len(tasks),
        "open_engineering": len(open_ids),
        "open_ids": open_ids,
        "by_status": by_status,
        "by_sprint": by_sprint,
        "gates_open": gate_open,
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
