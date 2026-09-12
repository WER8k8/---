#!/usr/bin/env python3
"""Domain email extractor Sidecar 接线验证。"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

_dev_env = BACKEND / "config" / "dev" / ".env"
if _dev_env.is_file():
    for line in _dev_env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        if key.strip() and key.strip() not in os.environ:
            os.environ[key.strip()] = val.strip().strip('"').strip("'")

os.environ.setdefault("SECRET_KEY", "verify-email-ext-" + ("x" * 24))
os.environ.setdefault("JWT_SECRET_KEY", os.environ["SECRET_KEY"])
os.environ.setdefault("ENVIRONMENT", "development")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true", help="Extract emails for example.com")
    args = parser.parse_args()
    errors: list[str] = []

    from app.services.ubrain.domain_email_extractor_sidecar import (
        domain_email_extractor_sidecar_status,
        fetch_emails_for_domain,
    )

    st = domain_email_extractor_sidecar_status()
    print("status:", json.dumps(st, ensure_ascii=False, indent=2))
    if st.get("configured") and st.get("healthy") is not True:
        errors.append(f"unhealthy: {st.get('detail')}")

    if args.smoke and st.get("configured"):
        out = fetch_emails_for_domain("example.com", tenant_id="verify")
        if out and out.get("emails"):
            print(f"smoke: ok count={out['count']} probe={out.get('probe_mode')}")
            print("  -", out["emails"][0].get("email"), out["emails"][0].get("source_url"))
        else:
            errors.append("smoke returned no emails with source_url")

    if errors:
        print("FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print("OK domain-email-extractor sidecar")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
