#!/usr/bin/env python3
"""Staging 支付自检 CLI — 与 POST /payment/ops/staging/self-check 同源逻辑。"""

from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


import argparse
import json
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("JWT_SECRET_KEY", "staging-check-" + "x" * 24)


def main() -> int:
    parser = argparse.ArgumentParser(description="Staging 支付自检")
    parser.add_argument(
        "--http",
        action="store_true",
        help="调用已运行后端的 HTTP API（需 super_admin token）",
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8001")
    parser.add_argument("--admin-user", default="admin")
    parser.add_argument("--admin-pass", default="admin123")
    args = parser.parse_args()

    if args.http:
        import httpx

        base = args.base_url.rstrip("/")
        with httpx.Client(timeout=60.0, follow_redirects=True) as client:
            login = client.post(
                f"{base}/api/v1/auth/login",
                json={"username_or_email": args.admin_user, "password": args.admin_pass},
            )
            body = login.json()
            if body.get("code") != 0:
                logger.info(json.dumps({"ok": False, "error": "login failed"}, ensure_ascii=False))
                return 1
            token = body["data"]["access_token"]
            r = client.post(
                f"{base}/api/v1/payment/ops/staging/self-check",
                headers={"Authorization": f"Bearer {token}"},
            )
            report = r.json().get("data") or r.json()
    else:
        from app.db.session import SessionLocal
        from app.services.payment_ops_service import run_staging_payment_self_check

        db = SessionLocal()
        try:
            report = run_staging_payment_self_check(db)
        finally:
            db.close()

    logger.info(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
