#!/usr/bin/env python3
"""MOD-04 · 七步录屏清单对应路由在 router 中可解析."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "frontend/admin/src/router/index.ts"
REPORT = ROOT / "docs/mod-04-recording-routes-latest.json"

ROUTES = (
    "/login",
    "/client/dashboard",
    "/client/queues/inquiries",
    "/client/plan-gate",
    "/admin/tenants",
    "/agent/performance",
)


def main() -> int:
    text = ROUTER.read_text(encoding="utf-8") if ROUTER.is_file() else ""
    found = {}
    for route in ROUTES:
        if route == "/login":
            found[route] = "path: '/login'" in text or 'path: "/login"' in text
            continue
        if route == "/admin/tenants":
            found[route] = "admin/tenants" in text
            continue
        tail = route.split("/")[-1]
        found[route] = bool(re.search(rf"path:\s*['\"]{re.escape(tail)}['\"]", text))

    ok = all(found.values())
    out = {"ok": ok, "task": "MOD-04-routes", "routes": found, "router": str(ROUTER.relative_to(ROOT))}
    REPORT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
