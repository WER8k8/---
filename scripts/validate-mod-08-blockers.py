#!/usr/bin/env python3
"""MOD-08 · Owner blocker JSON + 研发就绪项校验."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/mod-08-blockers-validation-latest.json"
BLOCKERS = ROOT / "docs/compliance/mod-08-owner-blockers.json"

DEV_READY = (
    ROOT / "docs/compliance/owner-blocker-checklist-mod-08.md",
    ROOT / "docs/compliance/pm-06-blocked-written-template.md",
    ROOT / "docs/r1-owner-handoff-pack.md",
    ROOT / "scripts/validate-arch-04-certbot-preflight.py",
    ROOT / "scripts/validate-arch-04-staging-https.py",
    ROOT / "scripts/qa-locust-72h-production.ps1",
    ROOT / "scripts/apply-pat-02-report-number.py",
    ROOT / "scripts/apply-comp-06-lawyer-signoff.py",
    ROOT / "scripts/run-owner-unblock-rehearsal.ps1",
    ROOT / "scripts/validate-mod-08-owner-readiness.py",
)


def main() -> int:
    blockers = json.loads(BLOCKERS.read_text(encoding="utf-8"))
    items = blockers.get("items", [])
    pending = [i["id"] for i in items if not i.get("done")]
    dev_ok = {str(p.relative_to(ROOT)): p.is_file() for p in DEV_READY}
    ok = bool(items) and all(dev_ok.values())
    report = {
        "ok": ok,
        "task": "MOD-08",
        "owner_pending_count": len(pending),
        "owner_pending_ids": pending,
        "dev_ready_files": dev_ok,
        "all_owner_cleared": len(pending) == 0,
    }
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
