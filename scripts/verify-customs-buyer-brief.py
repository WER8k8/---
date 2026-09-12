#!/usr/bin/env python3
"""Customs buyer brief API honesty verification (no fake buyer lists)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

os.environ.setdefault("SECRET_KEY", "verify-customs-" + ("x" * 24))
os.environ.setdefault("JWT_SECRET_KEY", os.environ["SECRET_KEY"])
os.environ.setdefault("ENVIRONMENT", "development")


def main() -> int:
    errors: list[str] = []

    from app.services.foreign_trade.customs_buyer_brief_service import build_customs_buyer_brief

    brief = build_customs_buyer_brief(
        product="rock wool insulation",
        hs_code="680610",
        country_code="DE",
    )
    print("brief:", json.dumps(brief, ensure_ascii=False, indent=2)[:1200], "...")

    if brief.get("buyer_history") is not None:
        errors.append("buyer_history must be null (no unverified buyers)")
    if brief.get("included") is not None:
        errors.append("included must be null without sidecar source")
    if not brief.get("disclaimer"):
        errors.append("missing disclaimer")
    if not brief.get("honesty"):
        errors.append("missing honesty field")
    if brief.get("stats_count", 0) < 0:
        errors.append("invalid stats_count")

    if errors:
        print("FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print("OK customs-buyer-brief (honest stats only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
