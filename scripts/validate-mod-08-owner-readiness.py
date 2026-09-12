#!/usr/bin/env python3
"""MOD-08 · Owner 交接就绪度汇总（dev 脚本齐 + blocker 待办）."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/mod-08-owner-readiness-latest.json"
BLOCKERS = ROOT / "docs/compliance/mod-08-owner-blockers.json"

DEV_SCRIPTS = (
    "scripts/pilot-acme-ssl-issue.ps1",
    "scripts/qa-locust-72h-production.ps1",
    "scripts/run-mod-04-recording-rehearsal.ps1",
    "scripts/validate-mod-04-https-step.py",
    "scripts/apply-pat-02-report-number.py",
    "scripts/apply-comp-06-lawyer-signoff.py",
    "scripts/sync-owner-blockers-from-records.py",
    "docs/r1-owner-handoff-pack.md",
)


def main() -> int:
    blockers = json.loads(BLOCKERS.read_text(encoding="utf-8-sig")) if BLOCKERS.is_file() else {"items": []}
    items = blockers.get("items", [])
    pending = [i for i in items if not i.get("done")]
    cleared = [i for i in items if i.get("done")]
    dev_ok = {p: (ROOT / p).is_file() for p in DEV_SCRIPTS}
    dev_pct = round(100 * sum(dev_ok.values()) / max(len(dev_ok), 1))
    owner_pct = round(100 * len(cleared) / max(len(items), 1))
    ok = all(dev_ok.values()) and bool(items)
    out = {
        "ok": ok,
        "task": "MOD-08-owner-readiness",
        "dev_ready_pct": dev_pct,
        "owner_cleared_pct": owner_pct,
        "owner_pending": [i["id"] for i in pending],
        "owner_cleared": [i["id"] for i in cleared],
        "dev_scripts": dev_ok,
        "handoff": "docs/r1-owner-handoff-pack.md",
    }
    REPORT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
