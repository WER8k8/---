#!/usr/bin/env python3
"""MOD-06 · 出海计 App Capacitor 构建链校验."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADMIN = ROOT / "frontend/admin"
REPORT = ROOT / "docs/mod-06-chuhaiji-validation-latest.json"

REQUIRED = {
    "capacitor.config.ts": ADMIN / "capacitor.config.ts",
    "chuhaiji-app.vue": ADMIN / "src/views/client/chuhaiji-app.vue",
    "app-store-checklist": ROOT / "docs/compliance/MOD-06-app-store-submission-checklist.md",
}


def main() -> int:
    pkg = json.loads((ADMIN / "package.json").read_text(encoding="utf-8"))
    scripts = pkg.get("scripts", {})
    cap_config = (ADMIN / "capacitor.config.ts").read_text(encoding="utf-8") if (ADMIN / "capacitor.config.ts").is_file() else ""

    checks = {name: path.is_file() for name, path in REQUIRED.items()}
    checks["cap_sync_script"] = "cap:sync" in scripts
    checks["app_id_com_youding"] = "com.youding.chuhaiji" in cap_config
    checks["app_name_chuhaiji"] = "出海计" in cap_config

    ok = all(checks.values())
    report = {
        "ok": ok,
        "task": "MOD-06",
        "checks": checks,
        "human_pending": "npm i @capacitor/* + 商店提审实机包",
        "build_command": "cd frontend/admin && npm run cap:sync",
    }
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
