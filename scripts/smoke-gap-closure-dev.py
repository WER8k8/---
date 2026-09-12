#!/usr/bin/env python3
"""Gap closure dev smoke — API 探针 + 旁路 + 发布门禁（无需浏览器）。"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
VENV_PY = BACKEND / ".venv" / "Scripts" / "python.exe"
REPORT = ROOT / "docs" / "gap-closure-smoke-latest.json"


def _login(base: str) -> str | None:
    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.post(
                f"{base}/api/v1/auth/login",
                json={"username_or_email": "tenant", "password": "tenant123"},
                headers={"User-Agent": "YouDingSaaS-Internal/1.0"},
            )
            if r.status_code >= 300:
                return None
            body = r.json()
            data = body.get("data") if isinstance(body.get("data"), dict) else body
            return (data or {}).get("access_token") or body.get("access_token")
    except Exception:
        return None


def _probe(name: str, url: str, *, token: str | None = None, timeout: float = 45.0) -> dict:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.get(url, headers=headers)
            ok = r.status_code < 300
            return {"name": name, "ok": ok, "status": r.status_code, "url": url}
    except Exception as exc:
        return {"name": name, "ok": False, "error": str(exc)[:200], "url": url}


def _run_script(rel: str, extra_args: list[str] | None = None) -> dict:
    py = VENV_PY if VENV_PY.is_file() else Path(sys.executable)
    cmd = [str(py), str(ROOT / "scripts" / rel)]
    if extra_args:
        cmd.extend(extra_args)
    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return {"script": rel, "ok": proc.returncode == 0, "exit": proc.returncode}


def main() -> int:
    parser = argparse.ArgumentParser(description="Gap closure dev smoke")
    parser.add_argument("--api-base", default=os.getenv("YOUDING_API_BASE", "http://127.0.0.1:8001"))
    args = parser.parse_args()
    base = args.api_base.rstrip("/")

    checks: list[dict] = []
    checks.append(_probe("health", f"{base}/api/v1/health"))
    token = _login(base)
    checks.append({"name": "tenant_login", "ok": bool(token)})

    if token:
        authed = [
            ("pipeline_summary", f"{base}/api/v1/cross-border/inquiries/pipeline/summary"),
            ("geo_visibility", f"{base}/api/v1/cross-border/geo-visibility"),
            ("unified_geo_score", f"{base}/api/v1/cross-border/unified-geo-score?include_probes=false"),
            ("public_geo_score", f"{base}/api/v1/public/tenants/dev.local/geo-score?include_probes=false"),
            ("gsc_ads_status", f"{base}/api/v1/foreign-trade/attribution/gsc-ads-status"),
            ("sidecars_status", f"{base}/api/v1/foreign-trade/integrations/sidecars/status"),
            ("matrix_oauth_gate", f"{base}/api/v1/foreign-trade/integrations/matrix-oauth-gate"),
        ]
        for name, url in authed:
            checks.append(_probe(name, url, token=token))

    scripts = [
        "verify-b2b-sidecars-all.py",
        "validate-site-l-pro-publish-e2e.py",
        "validate-gsc-ads-webhook.py",
        "validate-tenant-seo-audit.py",
        "validate-tenant-geo-audit.py",
        "run-seo-keyword-discover.py",
    ]
    script_results = [
        _run_script(s, ["--skip-probes"] if s == "validate-tenant-geo-audit.py" else [])
        for s in scripts
    ]

    failed = [c for c in checks if not c.get("ok")] + [s for s in script_results if not s.get("ok")]
    payload = {
        "ok": len(failed) == 0,
        "checks": checks,
        "scripts": script_results,
        "failed_count": len(failed),
    }
    REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
