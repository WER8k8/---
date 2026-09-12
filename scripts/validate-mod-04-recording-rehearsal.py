#!/usr/bin/env python3
"""MOD-04 · 七步录屏本地彩排：SPA 路由 HTTP 200（无需 HTTPS 域）."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/mod-04-recording-rehearsal-latest.json"

ROUTES = (
    "/login",
    "/client/dashboard",
    "/client/queues/inquiries",
    "/client/plan-gate",
    "/admin/tenants",
    "/agent/performance",
)


def probe(base: str, path: str) -> tuple[bool, int | None, str | None]:
    url = base.rstrip("/") + path
    try:
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "MOD-04-rehearsal/1.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            return resp.status == 200, resp.status, None
    except urllib.error.HTTPError as exc:
        return False, exc.code, str(exc.reason)
    except OSError as exc:
        return False, None, str(exc)


def main() -> int:
    base = os.environ.get("MOD04_BASE_URL", "http://127.0.0.1:4173").strip()
    hits: dict[str, dict] = {}
    for route in ROUTES:
        ok, status, err = probe(base, route)
        hits[route] = {"ok": ok, "status": status, "error": err}

    routes_ok = all(v["ok"] for v in hits.values())
    out = {
        "ok": routes_ok,
        "task": "MOD-04-rehearsal",
        "base_url": base,
        "routes": hits,
        "https_step_pending": "Step 7 需 Owner HTTPS 域 + curl -I",
        "human_pending": "HTTPS 域就绪后按清单录屏归档 mod-04-recordings/",
    }
    REPORT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if routes_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
