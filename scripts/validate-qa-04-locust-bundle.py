#!/usr/bin/env python3
"""QA-04 · Locust 冒烟/干跑报告与脚本完整性校验."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/qa-locust/qa-04-bundle-validation-latest.json"
LOCUST_DIR = ROOT / "docs/qa-locust"

SCRIPTS = (
    ROOT / "scripts/qa-locust-smoke-with-backend.ps1",
    ROOT / "scripts/qa-locust-72h-dryrun.ps1",
    ROOT / "scripts/qa-locust-72h-production.ps1",
)


def _pass_report(path: Path) -> bool:
    if not path.is_file():
        return False
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return bool(data.get("smoke_pass")) and int(data.get("locust_exit", 1)) == 0


def main() -> int:
    smoke = LOCUST_DIR / "locust-smoke-latest.json"
    dryrun = LOCUST_DIR / "locust-72h-dryrun-latest.json"
    checks = {
        "smoke_report_pass": _pass_report(smoke),
        "dryrun_report_pass": _pass_report(dryrun),
        "schedule_md": (LOCUST_DIR / "QA-04-72h-schedule.md").is_file(),
        "locustfile": (ROOT / "backend/locustfile.py").is_file(),
    }
    checks.update({f"script_{p.stem}": p.is_file() for p in SCRIPTS})
    ok = all(checks.values())
    out = {"ok": ok, "task": "QA-04", "checks": checks, "human_pending": "HTTPS 域正式 72h"}
    REPORT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
