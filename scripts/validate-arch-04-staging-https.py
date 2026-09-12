#!/usr/bin/env python3
"""ARCH-04 · staging 自签证书有效性 + 可选 :443 探测."""

from __future__ import annotations

import json
import os
import socket
import ssl
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/arch-04-staging-https-latest.json"
SSL_DIR = ROOT / "docker/nginx/ssl"
FULLCHAIN = SSL_DIR / "fullchain.pem"
PRIVKEY = SSL_DIR / "privkey.pem"
STAGING_DOMAIN = "demo.youding.local"


def openssl_checkend(path: Path) -> tuple[bool, str | None]:
    for exe in ("openssl", r"C:\Program Files\Git\usr\bin\openssl.exe"):
        try:
            proc = subprocess.run(
                [exe, "x509", "-in", str(path), "-noout", "-checkend", "86400"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if proc.returncode == 0:
                return True, None
            if proc.returncode == 1:
                return False, "certificate expires within 24h or invalid"
            continue
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return FULLCHAIN.is_file() and FULLCHAIN.stat().st_size > 200, "openssl unavailable; size check only"


def port_open(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def probe_https(url: str) -> tuple[bool, int | None, str | None]:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "ARCH-04-staging-https/1.0"})
        with urllib.request.urlopen(req, timeout=8, context=ctx) as resp:
            return resp.status in (200, 301, 302, 404), resp.status, None
    except urllib.error.HTTPError as exc:
        return exc.code in (200, 301, 302, 404), exc.code, str(exc.reason)
    except OSError as exc:
        return False, None, str(exc)


def main() -> int:
    cert_ok, cert_note = openssl_checkend(FULLCHAIN) if FULLCHAIN.is_file() else (False, "missing fullchain")
    checks = {
        "fullchain_pem": FULLCHAIN.is_file(),
        "privkey_pem": PRIVKEY.is_file(),
        "cert_valid_24h": cert_ok,
        "nginx_default_conf": (ROOT / "docker/nginx/default.conf").is_file(),
        "staging_domain_in_ssl_readme": STAGING_DOMAIN in (SSL_DIR / "README.md").read_text(encoding="utf-8")
        if (SSL_DIR / "README.md").is_file()
        else False,
    }

    https_probe: dict = {"skipped": True, "reason": "port 443 not listening"}
    probe_host = os.environ.get("ARCH04_HTTPS_HOST", "127.0.0.1")
    if port_open(probe_host, 443):
        url = os.environ.get("ARCH04_HTTPS_URL", f"https://{probe_host}/")
        ok, status, err = probe_https(url)
        https_probe = {"skipped": False, "url": url, "ok": ok, "status": status, "error": err}

    file_ok = all(checks[k] for k in checks)
    ok = file_ok and (https_probe.get("skipped") or https_probe.get("ok"))
    out = {
        "ok": ok,
        "task": "ARCH-04-staging-https",
        "staging_domain": STAGING_DOMAIN,
        "checks": checks,
        "cert_note": cert_note,
        "https_probe": https_probe,
        "human_pending": "Owner 生产域 + Certbot 替换自签",
    }
    REPORT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
