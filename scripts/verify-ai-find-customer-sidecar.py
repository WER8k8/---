#!/usr/bin/env python3
"""AI_Find_Customer Sidecar 接线验证 — 状态 + 可选找客 smoke。"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

_dev_env = BACKEND / "config" / "dev" / ".env"
if _dev_env.is_file():
    for line in _dev_env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val

os.environ.setdefault("SECRET_KEY", "verify-sidecar-" + ("x" * 24))
os.environ.setdefault("JWT_SECRET_KEY", os.environ["SECRET_KEY"])
os.environ.setdefault("ENVIRONMENT", "development")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify AI Find Customer sidecar wiring")
    parser.add_argument(
        "--api-base",
        default=os.getenv("YOUDING_API_BASE", "http://127.0.0.1:8001"),
        help="YouDing backend base URL",
    )
    parser.add_argument("--token", default=os.getenv("YOUDING_ADMIN_TOKEN", ""))
    parser.add_argument("--smoke-find", action="store_true", help="Call fetch_sidecar_prospects once")
    args = parser.parse_args()

    errors: list[str] = []

    try:
        from app.services.ubrain.ai_find_customer_sidecar import (
            ai_find_customer_sidecar_status,
            fetch_sidecar_prospects,
        )

        st = ai_find_customer_sidecar_status()
        print("sidecar_status:", json.dumps(st, ensure_ascii=False, indent=2))
        if not st.get("configured"):
            print("INFO: AI_FIND_CUSTOMER_URL not set — Accio 画像模板兜底（诚实）")
        elif st.get("healthy") is not True:
            errors.append(f"sidecar unhealthy: {st.get('detail')}")

        if args.smoke_find and st.get("configured"):
            out = fetch_sidecar_prospects(
                tenant_id="verify-tenant",
                query="中东 保温建材 分销商",
                region="中东",
                category="保温建材",
                count=3,
            )
            if out and out.get("prospects"):
                print(f"smoke_find: ok mode={out.get('mode')} count={len(out['prospects'])}")
                if out.get("probe_mode") == "stub":
                    print("  probe_mode=stub (dev mock upstream — honest)")
                for p in out["prospects"][:2]:
                    print("  -", p.get("title"), p.get("evidence_url"))
            elif out:
                errors.append("smoke_find returned pack without prospects")
            else:
                errors.append("smoke_find returned None (upstream down or no evidence leads)")
    except Exception as exc:
        errors.append(f"import/status: {exc}")

    if args.token:
        try:
            import httpx

            url = f"{args.api_base.rstrip('/')}/api/v1/foreign-trade/integrations/sidecars/status"
            resp = httpx.get(
                url,
                headers={"Authorization": f"Bearer {args.token}"},
                timeout=10.0,
            )
            if resp.status_code >= 300:
                errors.append(f"integrations status HTTP {resp.status_code}")
            else:
                body = resp.json()
                ai = (body.get("data") or {}).get("ai_find_customer") or {}
                print("integrations.ai_find_customer:", json.dumps(ai, ensure_ascii=False))
        except Exception as exc:
            errors.append(f"integrations status: {exc}")
    else:
        print("SKIP integrations API (set --token or YOUDING_ADMIN_TOKEN)")

    if errors:
        print("FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print("OK ai-find-customer sidecar")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
