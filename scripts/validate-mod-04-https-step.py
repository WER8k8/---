#!/usr/bin/env python3
"""MOD-04 · 第 7 步 HTTPS 锁标探测（需 MOD04_HTTPS_DOMAIN 或跳过）."""

from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/mod-04-https-step-latest.json"
ARCHIVE = ROOT / "docs/compliance/mod-04-recordings/mod04-07-https.txt"


def probe(domain: str) -> tuple[bool, dict]:
    url = domain if domain.startswith("https://") else f"https://{domain}/"
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(
            urllib.request.Request(url, method="HEAD", headers={"User-Agent": "MOD-04-https-step/1.0"}),
            timeout=12,
            context=ctx,
        ) as resp:
            return True, {"url": url, "status": resp.status, "verified_ssl": True}
    except urllib.error.HTTPError as exc:
        return exc.code in (200, 301, 302), {
            "url": url,
            "status": exc.code,
            "verified_ssl": True,
            "note": str(exc.reason),
        }
    except ssl.SSLError as exc:
        return False, {"url": url, "verified_ssl": False, "error": str(exc)}
    except OSError as exc:
        return False, {"url": url, "error": str(exc)}


def main() -> int:
    domain = os.environ.get("MOD04_HTTPS_DOMAIN", "").strip()
    if not domain:
        out = {
            "ok": True,
            "task": "MOD-04-https-step",
            "skipped": True,
            "reason": "MOD04_HTTPS_DOMAIN unset; dev-ready",
            "human_pending": "Owner 提供 HTTPS 域后: $env:MOD04_HTTPS_DOMAIN='demo.example.com'; python scripts/validate-mod-04-https-step.py",
        }
        REPORT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0

    ok, detail = probe(domain)
    if ok and not ARCHIVE.is_file():
        ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
        ARCHIVE.write_text(
            f"# MOD-04 step 7 auto-check\n# domain={domain}\n{json.dumps(detail, ensure_ascii=False)}\n",
            encoding="utf-8",
        )
    out = {
        "ok": ok,
        "task": "MOD-04-https-step",
        "skipped": False,
        "domain": domain,
        "probe": detail,
        "archive_hint": str(ARCHIVE.relative_to(ROOT)),
    }
    REPORT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
