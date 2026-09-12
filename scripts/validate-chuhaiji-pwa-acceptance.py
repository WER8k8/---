#!/usr/bin/env python3
"""COMM-APP-01 · 出海计 PWA 四 Tab 静态验收（路由 + 资源 + BFF 契约）."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADMIN = ROOT / "frontend/admin"
REPORT = ROOT / "docs/chuhaiji-pwa-acceptance-latest.json"

REQUIRED_TABS = ("assistant", "today", "publish", "profile")
REQUIRED_API_SNIPPETS = (
    "/api/v1/app/v1/home",
    "/api/v1/app/v1/today",
    "/api/v1/app/v1/config",
    "/api/v1/app/v1/inquiries/offline",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def main() -> int:
    vue = _read(ADMIN / "src/views/client/chuhaiji-app.vue")
    router = _read(ADMIN / "src/router/index.ts")
    manifest = _read(ADMIN / "public/manifest.webmanifest")
    sw = _read(ADMIN / "public/sw.js")

    tab_hits = {t: t in vue for t in REQUIRED_TABS}
    checks = {
        "chuhaiji_vue": (ADMIN / "src/views/client/chuhaiji-app.vue").is_file(),
        "four_tabs": all(tab_hits.values()),
        "route_client_app": (
            "ChuhaijiApp" in router
            and "chuhaiji-app.vue" in router
            and bool(re.search(r"path:\s*['\"]app['\"]", router))
        ),
        "manifest_start_url": '"/client/app"' in manifest or "'/client/app'" in manifest,
        "service_worker": (ADMIN / "public/sw.js").is_file(),
        "sw_cache_shell": "chuhaiji" in sw.lower(),
        "bff_home": "/api/v1/app/v1/home" in vue,
        "bff_today": "/api/v1/app/v1/today" in vue,
        "bff_config": "/api/v1/app/v1/config" in vue,
        "bff_offline_inquiries": "/api/v1/app/v1/inquiries/offline" in vue,
        "brand_chuhaiji": "出海计" in vue,
    }

    missing_apis = [s for s in REQUIRED_API_SNIPPETS if s not in vue]
    ok = all(checks.values())
    report = {
        "ok": ok,
        "task": "COMM-APP-01",
        "checks": checks,
        "tab_hits": tab_hits,
        "missing_api_refs": missing_apis,
        "manual_e2e": [
            "tenant/tenant123 登录 -> /client/app",
            "切换四 Tab：助手 / 今日 / 发布 / 我的",
            "助手发送一条消息，今日拉取待办，我的测试推送",
        ],
        "out_of_scope": "AAB 提审、FCM 生产密钥、商店五图",
    }
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
