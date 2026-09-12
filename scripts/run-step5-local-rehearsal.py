#!/usr/bin/env python3
"""本地七步⑤ 5a/5b/5c API 彩排（须 backend :8001 已启动 + 租户 token）。"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
API = os.getenv("REHEARSAL_API_BASE", "http://127.0.0.1:8001/api/v1").rstrip("/")
USER = os.getenv("REHEARSAL_USER", "admin")
PASS = os.getenv("REHEARSAL_PASS", "admin123")


def _login(client: httpx.Client) -> str:
    r = client.post(f"{API}/auth/login", json={"username_or_email": USER, "password": PASS})
    r.raise_for_status()
    body = r.json()
    data = body.get("data") or body
    token = data.get("access_token") or data.get("token")
    if not token:
        raise RuntimeError(f"login_failed:{body}")
    return token


def _post(client: httpx.Client, path: str, token: str) -> dict:
    r = client.post(f"{API}{path}", headers={"Authorization": f"Bearer {token}"})
    try:
        return r.json()
    except Exception:
        return {"http_status": r.status_code, "text": r.text[:500]}


def main() -> int:
    out: dict = {"api": API, "steps": {}}
    try:
        with httpx.Client(timeout=30.0) as client:
            token = os.getenv("SMOKE_TOKEN", "").strip() or _login(client)
            for step, path in (
                ("5a_inbound", "/client/sales-channel-rehearsal/inbound"),
                ("5b_wecom", "/client/sales-channel-rehearsal/wecom-push"),
                ("5c_comment", "/client/douyin-comments/rehearsal-ingest"),
            ):
                body = _post(client, path, token)
                out["steps"][step] = body
    except Exception as exc:
        out["error"] = str(exc)
        latest = ROOT / "docs" / "step5-local-rehearsal-latest.json"
        latest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"FAIL: {exc}")
        return 1

    latest = ROOT / "docs" / "step5-local-rehearsal-latest.json"
    latest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    ok5a = (out["steps"].get("5a_inbound") or {}).get("code") == 0
    ok5c = ((out["steps"].get("5c_comment") or {}).get("data") or {}).get("ingested", 0) >= 1
    ok5b = ((out["steps"].get("5b_wecom") or {}).get("data") or {}).get("ok") is True
    print(f"5a={'PASS' if ok5a else 'WARN'} 5b={'PASS' if ok5b else 'SKIP/WARN'} 5c={'PASS' if ok5c else 'FAIL'}")
    print(f"Wrote {latest}")
    return 0 if ok5a and ok5c else 1


if __name__ == "__main__":
    sys.exit(main())
