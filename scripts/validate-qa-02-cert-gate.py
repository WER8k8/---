#!/usr/bin/env python3
"""QA-02 · 读取 cert:gate 最新报告（不重跑 npm，供 R1 gate 快速校验）."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/qa-02-cert-gate-validation-latest.json"
GATE = ROOT / "docs/certification-gate-admin-latest.json"


def main() -> int:
    if not GATE.is_file():
        out = {"ok": False, "task": "QA-02", "error": "missing certification-gate-admin-latest.json"}
        REPORT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 1

    data = json.loads(GATE.read_text(encoding="utf-8-sig"))
    gates = data.get("gates") or []
    blocking_fail = [g.get("script") for g in gates if g.get("blocking") and not g.get("ok")]
    ok = bool(data.get("ready")) and not bool(data.get("blocked")) and not blocking_fail
    out = {
        "ok": ok,
        "task": "QA-02",
        "ready": data.get("ready"),
        "blocked": data.get("blocked"),
        "blocking_failures": blocking_fail,
        "generated_at": data.get("generatedAt"),
        "source": str(GATE.relative_to(ROOT)),
        "full_rerun": "cd frontend/admin && npm run cert:gate",
    }
    REPORT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
