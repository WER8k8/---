#!/usr/bin/env python3
"""P1-05 · 租户站友链策略链路校验（API + Nuxt 渲染）。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/tenant-site-policy-p1-05-latest.json"

REQUIRED = [
    ("backend/app/services/tenant_settings_service.py", "hide_hub_backlink"),
    ("backend/app/api/v1/routes/mobile_public.py", "site-policy"),
    ("frontend/composables/useTenantSitePolicy.ts", "hide_hub_backlink"),
    ("frontend/components/common/Footer.vue", "hideHubBacklink"),
    ("frontend/layouts/default.vue", "loadTenantPolicy"),
]


def main() -> int:
    missing = []
    for rel, needle in REQUIRED:
        path = ROOT / rel
        if not path.is_file():
            missing.append(f"missing:{rel}")
            continue
        if needle not in path.read_text(encoding="utf-8", errors="replace"):
            missing.append(f"snippet:{rel}:{needle}")

    ok = not missing
    report = {
        "ok": ok,
        "task": "P1-05",
        "checks": len(REQUIRED) - len(missing),
        "required": len(REQUIRED),
        "missing": missing,
        "default_hide": True,
        "api": "/api/v1/mobile/site-policy",
    }
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
