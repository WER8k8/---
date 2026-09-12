#!/usr/bin/env python3
"""批量标记 backlog 任务为 done（蜂群收尾用）。"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKLOG = ROOT / "docs" / "dev-backlog-sprint.json"


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/backlog_mark_done.py A-04 B-06 ...")
        return 1
    ids = set(sys.argv[1:])
    data = json.loads(BACKLOG.read_text(encoding="utf-8"))
    n = 0
    for t in data["tasks"]:
        if t["id"] in ids:
            t["status"] = "done"
            t["assignee"] = t.get("assignee") or "swarm"
            n += 1
    BACKLOG.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"marked {n} tasks: {ids}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
