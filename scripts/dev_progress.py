#!/usr/bin/env python3
"""开发进度条 — 读取 dev-backlog-sprint.json，打印并写入快照。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKLOG = ROOT / "docs" / "dev-backlog-sprint.json"
SNAPSHOT = ROOT / "docs" / "dev-progress-latest.txt"


def _configure_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def bar(done: int, total: int, width: int = 32) -> str:
    if total <= 0:
        return "[" + "?" * width + "]"
    filled = int(width * done / total)
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def render(data: dict) -> str:
    tasks = data.get("tasks", [])
    by_sprint: dict[str, list] = {}
    for t in tasks:
        by_sprint.setdefault(t.get("sprint", "?"), []).append(t)

    total = len(tasks)
    done = sum(1 for t in tasks if t.get("status") == "done")
    pct = (100 * done / total) if total else 0

    lines = [
        "",
        "=== MVP 开发进度 ===",
        f"{bar(done, total)} {done}/{total} ({pct:.0f}%)",
        "",
    ]
    for sprint in data.get("sprints", []):
        sid = sprint["id"]
        items = by_sprint.get(sid, [])
        d = sum(1 for t in items if t.get("status") == "done")
        lines.append(f"  {sprint['name']}: {bar(d, len(items), 20)} {d}/{len(items)}")

    pending = [t for t in tasks if t.get("status") != "done"]
    if pending:
        lines.append("\n待开发（前 8 条）:")
        for t in pending[:8]:
            lines.append(f"  - [{t['id']}] {t['title']}")
        if len(pending) > 8:
            lines.append(f"  ... 另有 {len(pending) - 8} 条")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    _configure_stdout()
    if not BACKLOG.is_file():
        print(f"ERROR: missing {BACKLOG}", file=sys.stderr)
        return 1
    try:
        data = json.loads(BACKLOG.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON in backlog: {e}", file=sys.stderr)
        return 1

    text = render(data)
    print(text)
    SNAPSHOT.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
