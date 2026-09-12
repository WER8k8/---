#!/usr/bin/env python3
"""ARCH-04 · 校验 nginx HTTPS 配置与 staging SSL 文件."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NGINX = ROOT / "docker/nginx/default.conf"
SSL_DIR = ROOT / "docker/nginx/ssl"
REPORT = ROOT / "docs/arch-04-nginx-ssl-check-latest.json"


def main() -> int:
    text = NGINX.read_text(encoding="utf-8") if NGINX.exists() else ""
    checks = {
        "nginx_conf_exists": NGINX.exists(),
        "listen_443": "listen 443 ssl" in text,
        "http_to_https_redirect": "return 301 https://" in text,
        "ssl_cert_path": "/etc/nginx/ssl/fullchain.pem" in text,
        "ssl_key_path": "/etc/nginx/ssl/privkey.pem" in text,
        "hsts_header": "Strict-Transport-Security" in text,
        "fullchain_pem": (SSL_DIR / "fullchain.pem").exists(),
        "privkey_pem": (SSL_DIR / "privkey.pem").exists(),
    }
    ok = all(checks.values())
    report = {
        "ok": ok,
        "task": "ARCH-04",
        "nginx_conf": str(NGINX.relative_to(ROOT)),
        "checks": checks,
        "staging_domain": "demo.youding.local",
        "production_note": "Replace self-signed with Certbot when Owner provides domain",
    }
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
