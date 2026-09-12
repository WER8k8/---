#!/usr/bin/env python3
"""COMM-QA-03 · 12 模块送检截图分工表校验。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / ".project/cert-screenshot-assignments-COMM-QA-03.json"
REPORT = ROOT / "docs/cert-screenshot-assignments-latest.json"


def main() -> int:
    if not MATRIX.is_file():
        print(json.dumps({"ok": False, "error": "missing matrix"}, ensure_ascii=False))
        return 1

    data = json.loads(MATRIX.read_text(encoding="utf-8"))
    modules = data.get("modules") or []
    issues = []
    if len(modules) != 12:
        issues.append(f"module_count={len(modules)} expected 12")
    for m in modules:
        if not m.get("owner"):
            issues.append(f"no_owner:{m.get('id')}")
        if m.get("status") == "blocked" and not m.get("blocked_by"):
            issues.append(f"blocked_without_reason:{m.get('id')}")

    summary = data.get("summary") or {}
    ok = not issues and summary.get("total") == 12
    report = {
        "ok": ok,
        "task": "COMM-QA-03",
        "total": len(modules),
        "pending": sum(1 for m in modules if m.get("status") == "pending"),
        "blocked": sum(1 for m in modules if m.get("status") == "blocked"),
        "issues": issues,
        "matrix_path": str(MATRIX.relative_to(ROOT)),
    }
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
