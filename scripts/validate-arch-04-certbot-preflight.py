#!/usr/bin/env python3
"""ARCH-04 · Certbot/ACME 生产前置校验（无需真实域名）."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/arch-04-certbot-preflight-latest.json"

ENV_TEMPLATE = ROOT / "deploy/production/env.template"
COMPOSE_PROD = ROOT / "docker-compose.prod.yml"
SSL_README = ROOT / "docker/nginx/ssl/README.md"


def main() -> int:
    env = ENV_TEMPLATE.read_text(encoding="utf-8") if ENV_TEMPLATE.is_file() else ""
    compose = COMPOSE_PROD.read_text(encoding="utf-8") if COMPOSE_PROD.is_file() else ""

    checks = {
        "env_certbot_email": "CERTBOT_EMAIL" in env,
        "env_certbot_webroot": "CERTBOT_WEBROOT" in env,
        "env_ssl_provider": "SSL_PROVIDER" in env,
        "compose_prod_exists": COMPOSE_PROD.is_file(),
        "compose_mentions_certbot_or_ssl": any(x in compose.lower() for x in ("certbot", "ssl", "443")),
        "ssl_readme": SSL_README.is_file(),
        "staging_fullchain": (ROOT / "docker/nginx/ssl/fullchain.pem").is_file(),
        "staging_privkey": (ROOT / "docker/nginx/ssl/privkey.pem").is_file(),
        "owner_blocker_doc": (ROOT / "docs/compliance/owner-blocker-checklist-mod-08.md").is_file(),
    }
    ok = all(checks.values())
    report = {
        "ok": ok,
        "task": "ARCH-04-certbot-preflight",
        "checks": checks,
        "human_pending": "Owner 提供 HTTPS 演示域 + DNS + 实跑 certbot",
        "rehearsal_script": "scripts/pilot-acme-ssl-issue.ps1",
    }
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
