#!/usr/bin/env python3
"""O-4 真实 B2B 上游接线验收 — 禁止 stub 冒充实盘。"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
REPORT = ROOT / "docs" / "o4-b2b-upstream-wire-latest.json"

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

os.environ.setdefault("SECRET_KEY", "validate-o4-" + ("x" * 24))
os.environ.setdefault("JWT_SECRET_KEY", os.environ["SECRET_KEY"])
os.environ.setdefault("ENVIRONMENT", "development")


def main() -> int:
    errors: list[str] = []
    checks: dict[str, object] = {}

    stub_flag = (os.getenv("AI_FIND_CUSTOMER_ALLOW_DEV_STUB") or "").strip()
    checks["allow_dev_stub"] = stub_flag
    if stub_flag not in ("0", "false", "no", "off"):
        errors.append(f"AI_FIND_CUSTOMER_ALLOW_DEV_STUB must be 0 for O-4 (got {stub_flag!r})")

    upstream = (os.getenv("AI_HUNTER_UPSTREAM_URL") or "").strip().rstrip("/")
    sidecar = (os.getenv("AI_FIND_CUSTOMER_URL") or "").strip().rstrip("/")
    checks["upstream_url"] = upstream or None
    checks["sidecar_url"] = sidecar or None

    if upstream:
        try:
            with httpx.Client(timeout=8.0) as client:
                r = client.get(f"{upstream}/api/v1/health")
            body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            checks["upstream_health"] = {"status": r.status_code, "body": body}
            if r.status_code >= 300:
                errors.append(f"upstream health HTTP {r.status_code}")
            elif str(body.get("mode") or "").lower() == "mock":
                errors.append("upstream is ai-hunter-upstream-mock — clone real AI_Find_Customer")
            elif body.get("service") == "ai-hunter-upstream-mock":
                errors.append("upstream service=ai-hunter-upstream-mock")
        except Exception as exc:
            errors.append(f"upstream health: {exc}")

    if sidecar:
        try:
            with httpx.Client(timeout=8.0) as client:
                r = client.get(f"{sidecar}/health")
            body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            checks["sidecar_health"] = body
            if body.get("upstream_healthy") is not True:
                errors.append(f"sidecar upstream_healthy != true ({body.get('upstream_detail')})")
        except Exception as exc:
            errors.append(f"sidecar health: {exc}")

    try:
        sys.path.insert(0, str(BACKEND))
        from app.services.ubrain.ai_find_customer_sidecar import (
            allow_dev_stub,
            fetch_sidecar_prospects,
        )

        checks["backend_allow_dev_stub"] = allow_dev_stub()
        if allow_dev_stub():
            errors.append("backend allow_dev_stub() still True")

        out = fetch_sidecar_prospects(
            tenant_id="o4-verify",
            query="中东 保温建材 分销商",
            region="中东",
            category="保温建材",
            count=3,
        )
        checks["smoke_find"] = bool(out and out.get("prospects"))
        if out and (out.get("probe_mode") == "stub" or str(out.get("mode") or "").lower() == "mock"):
            errors.append("smoke_find returned stub/mock with ALLOW_DEV_STUB=0")
        elif not out:
            errors.append(
                "smoke_find returned None — upstream may lack API keys or hunt failed (honest)"
            )
        else:
            checks["smoke_mode"] = out.get("mode")
            checks["smoke_count"] = len(out.get("prospects") or [])
    except Exception as exc:
        errors.append(f"backend smoke: {exc}")

    ok = len(errors) == 0
    payload = {"ok": ok, "task": "O-4", "checks": checks, "errors": errors}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
