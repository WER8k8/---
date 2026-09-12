#!/usr/bin/env python3
"""CustomsDataSpider Sidecar wiring verification."""

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

os.environ.setdefault("SECRET_KEY", "verify-customs-spider-" + ("x" * 16))
os.environ.setdefault("JWT_SECRET_KEY", os.environ["SECRET_KEY"])
os.environ.setdefault("ENVIRONMENT", "development")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true", help="Fetch stub buyer research")
    args = parser.parse_args()
    errors: list[str] = []

    from app.services.foreign_trade.customs_data_spider_sidecar import (
        customs_data_spider_sidecar_status,
        fetch_customs_buyer_research,
    )

    st = customs_data_spider_sidecar_status()
    print("status:", json.dumps(st, ensure_ascii=False, indent=2))
    if st.get("configured") and st.get("healthy") is not True:
        errors.append(f"unhealthy: {st.get('detail')}")

    if args.smoke and st.get("configured"):
        out = fetch_customs_buyer_research(
            product="rock wool insulation",
            hs_code="680610",
            country_code="DE",
            tenant_id="verify",
            max_results=5,
        )
        if out and out.get("buyers"):
            first = out["buyers"][0]
            if not first.get("evidence_url"):
                errors.append("smoke buyer missing evidence_url")
            if out.get("included") is True:
                errors.append("stub must not set included=true")
            else:
                print(
                    f"smoke: ok count={out['buyer_count']} probe={out.get('probe_mode')} "
                    f"evidence={first.get('evidence_url')[:60]}"
                )
        else:
            errors.append("smoke returned no buyers with evidence_url")

    if errors:
        print("FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print("OK customs-data-spider sidecar")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
