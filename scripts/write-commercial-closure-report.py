#!/usr/bin/env python3
"""Write docs/ops/commercial-closure-latest.json (honest commercial readiness)."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/ops/commercial-closure-latest.json"
ASSIGNMENTS = ROOT / ".project/cert-screenshot-assignments-COMM-QA-03.json"


def run(cmd: list[str]) -> tuple[bool, str]:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode == 0, out.strip()


def main() -> int:
    checks = [
        ("stub-matrix-sync", ["python", "scripts/validate-stub-matrix-sync.py"]),
        ("no-fake-delivery", ["python", "scripts/validate-no-fake-delivery.py"]),
        ("cert-screenshot-assignments", ["python", "scripts/validate-cert-screenshot-assignments.py"]),
    ]
    results = []
    for name, cmd in checks:
        ok, detail = run(cmd)
        results.append({"name": name, "ok": ok, "detail": detail[:2000]})

    assignments = json.loads(ASSIGNMENTS.read_text(encoding="utf-8"))
    summary = assignments.get("summary") or {}
    blocked = int(summary.get("blocked") or 0)
    captured = int(summary.get("captured") or 0)

    dev_ok = all(r["ok"] for r in results)
    commercial_ready = dev_ok and blocked == 0 and captured >= 12

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "task": "commercial-closure-gates",
        "dev_gates_ok": dev_ok,
        "commercial_ready": commercial_ready,
        "honest_note": "commercial_ready=false: Owner O-1~O-3 pending or blocked screenshots remain",
        "owner_blockers": [
            {"id": "O-1", "title": "HTTPS demo domain DNS", "status": "owner_pending"},
            {"id": "O-2", "title": "Inquiry IM / WeCom production secrets", "status": "owner_pending"},
            {"id": "O-3", "title": "5+5 platform table + pricing signoff", "status": "owner_pending"},
        ],
        "screenshot_summary": summary,
        "cert_gate_admin": str(ROOT / "docs/certification-gate-admin-latest.json"),
        "results": results,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"ok": dev_ok, "commercial_ready": commercial_ready, "out": str(OUT)}, ensure_ascii=False))
    return 0 if dev_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
