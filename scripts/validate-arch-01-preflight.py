#!/usr/bin/env python3
"""ARCH-01 · 读取最新 staging preflight 报告（不重跑，供 R1 gate 快速校验）."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/arch-01-preflight-validation-latest.json"
STAGING = ROOT / "docs/staging-preflight-auto-latest.json"


def main() -> int:
    if not STAGING.is_file():
        out = {"ok": False, "task": "ARCH-01", "error": "missing staging-preflight-auto-latest.json"}
        REPORT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 1

    data = json.loads(STAGING.read_text(encoding="utf-8-sig"))
    ok = data.get("status") == "PASS" and int(data.get("fail_count", 1)) == 0
    out = {
        "ok": ok,
        "task": "ARCH-01",
        "status": data.get("status"),
        "fail_count": data.get("fail_count"),
        "finished_at": data.get("finished_at"),
        "source": str(STAGING.relative_to(ROOT)),
        "note": "Fast read; full rerun: scripts/run-arch-01-cert-gate.ps1",
    }
    REPORT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
