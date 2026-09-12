#!/usr/bin/env python3
"""E2E：全媒体工作室 — capabilities → 项目持久化 → 精品轨门禁。"""
from __future__ import annotations

import sys
import uuid

import requests

API = "http://127.0.0.1:8001"
USERNAME = "tenant"
PASSWORD = "tenant123"
HEADERS = {
    "User-Agent": "Mozilla/5.0 YouDingMediaStudioE2E/1.0",
    "Accept": "application/json",
}


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


def _ok(resp: requests.Response, step: str) -> dict:
    try:
        body = resp.json()
    except Exception:
        body = {"raw": resp.text[:500]}
    if not resp.ok:
        raise RuntimeError(f"{step} HTTP {resp.status_code}: {body}")
    if isinstance(body, dict) and body.get("code") not in (None, 0):
        raise RuntimeError(f"{step} code={body.get('code')}: {body.get('message')}")
    return body.get("data", body) if isinstance(body, dict) else body


def login() -> tuple[requests.Session, str]:
    s = _session()
    r = s.post(
        f"{API}/api/v1/auth/login",
        json={"username_or_email": USERNAME, "password": PASSWORD},
        timeout=60,
    )
    data = _ok(r, "login")
    token = data.get("access_token")
    if not token:
        raise RuntimeError("login: no access_token")
    s.headers["Authorization"] = f"Bearer {token}"
    return s, token


def main() -> int:
    s, _ = login()

    cap = _ok(s.get(f"{API}/api/v1/cross-border/media-studio/capabilities", timeout=30), "capabilities")
    assert cap.get("product_id") == "CROSS-BORDER-MEDIA-STUDIO-01"
    editors = {e["id"]: e for e in cap.get("editors") or []}
    assert "fly_cut" in editors
    assert editors["fly_cut"].get("route") == "/client/video-editor/fly-cut"
    print("OK capabilities", "fly_cut.configured=", editors["fly_cut"].get("configured"))

    fake_id = str(uuid.uuid4())
    r404 = s.get(f"{API}/api/v1/cross-border/media-studio/projects/{fake_id}", timeout=30)
    if r404.status_code != 404:
        raise RuntimeError(f"expected 404 for missing project, got {r404.status_code}")

    # 精品轨未配 sidecar 时应 503（诚实门禁）
    r503 = s.post(
        f"{API}/api/v1/cross-border/video-dub/premium-jobs",
        json={
            "media_task_id": fake_id,
            "track": "opensource_premium",
            "voice_consent": True,
            "output_mode": "subtitle_burn",
        },
        timeout=30,
    )
    if r503.status_code == 404:
        print("SKIP premium 503: media_task missing (expected if no upload)")
    elif r503.status_code == 503:
        body = r503.json()
        msg = str(body.get("message") or "")
        assert "OPENSOURCE_NOT_CONFIGURED" in msg or "VOZO_NOT_CONFIGURED" in msg
        print("OK premium gate 503:", msg[:80])
    else:
        raise RuntimeError(f"premium-jobs expected 503 or 404, got {r503.status_code}: {r503.text[:200]}")

    print("OK media-studio e2e smoke")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
