#!/usr/bin/env python3
"""MOD-05 · 生产迁移 runbook + staging 证据校验."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/mod-05-prod-runbook-validation-latest.json"

REQUIRED = (
    ROOT / "docs/compliance/MOD-05-prod-migrate-runbook.md",
    ROOT / "docs/mod-05-staging-migrate-latest.json",
    ROOT / "scripts/run-mod-05-staging-migrate.ps1",
    ROOT / "scripts/validate-mod-05-staging-tables.py",
)


def main() -> int:
    files = {str(p.relative_to(ROOT)): p.is_file() for p in REQUIRED}
    staging_pass = False
    staging_path = ROOT / "docs/mod-05-staging-migrate-latest.json"
    if staging_path.is_file():
        staging_pass = bool(json.loads(staging_path.read_text(encoding="utf-8-sig")).get("pass"))
    ok = all(files.values()) and staging_pass
    out = {
        "ok": ok,
        "task": "MOD-05-prod-runbook",
        "files": files,
        "staging_migrate_pass": staging_pass,
        "human_pending": "生产库维护窗口执行 runbook",
    }
    REPORT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
