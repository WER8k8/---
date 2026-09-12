#!/usr/bin/env python3
"""IMAP inquiry Sidecar wiring verification."""

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

os.environ.setdefault("SECRET_KEY", "verify-imap-" + ("x" * 24))
os.environ.setdefault("JWT_SECRET_KEY", os.environ["SECRET_KEY"])
os.environ.setdefault("ENVIRONMENT", "development")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    errors: list[str] = []

    from app.services.ubrain.imap_inquiry_sidecar import (
        imap_inquiry_sidecar_status,
        poll_imap_inbox,
    )

    st = imap_inquiry_sidecar_status()
    print("status:", json.dumps(st, ensure_ascii=False, indent=2))
    if st.get("smtp_disabled") is not True:
        errors.append("smtp_disabled must be true")
    if st.get("configured") and st.get("healthy") is not True:
        errors.append(f"unhealthy: {st.get('detail')}")

    if args.smoke and st.get("configured"):
        out = poll_imap_inbox(tenant_id="verify", max_messages=3)
        if out and out.get("messages"):
            first = out["messages"][0]
            if not first.get("message_id") or not first.get("body") or not first.get("from_email"):
                errors.append("smoke message missing id/body/email")
            else:
                print(f"smoke: ok count={out['count']} probe={out.get('probe_mode')}")
        else:
            errors.append("smoke returned no valid messages")

    if errors:
        print("FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print("OK imap-inquiry sidecar")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
