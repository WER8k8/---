#!/usr/bin/env python3
"""飞轮 D2–D6 + UBrain 对话实机 smoke（需 :8001 已启动且 AI Key 可用）。"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8001"
USER = "admin"
PASS = "admin123"


def chk(name: str, ok: bool, detail: str = "") -> dict:
    return {"name": name, "ok": ok, "detail": detail}


def main() -> int:
    results: list[dict] = []
    with httpx.Client(base_url=BASE, timeout=90.0) as client:
        try:
            r = client.post(
                "/api/v1/auth/login",
                json={"username_or_email": USER, "password": PASS},
            )
            body = r.json()
            token = (body.get("data") or body).get("access_token") or (body.get("data") or body).get("token")
            ok = r.status_code == 200 and bool(token)
            results.append(chk("login", ok, f"status={r.status_code}"))
            if not ok:
                return _finish(results, 1)
        except Exception as exc:
            results.append(chk("login", False, str(exc)))
            return _finish(results, 1)

        h = {"Authorization": f"Bearer {token}"}

        endpoints = [
            ("d2_status", "GET", "/api/v1/ubrain/commercial-os/status", None),
            (
                "d3_research_brief",
                "POST",
                "/api/v1/ubrain/commercial-os/research-brief",
                {"message": "保温板出口越南可行性", "category": "insulation_board"},
            ),
            ("d4_pipelines", "GET", "/api/v1/ubrain/commercial-os/pipelines", None),
            ("d5_integrations", "GET", "/api/v1/ubrain/commercial-os/integrations", None),
            (
                "d6_feedback_sync",
                "POST",
                "/api/v1/ubrain/commercial-os/feedback/sync?period_days=7",
                None,
            ),
        ]
        for name, method, path, payload in endpoints:
            try:
                if method == "GET":
                    r = client.get(path, headers=h)
                else:
                    r = client.post(path, headers=h, json=payload or {})
                body = r.json()
                ok = r.status_code == 200 and body.get("code", 0) == 0
                results.append(chk(name, ok, f"status={r.status_code}"))
            except Exception as exc:
                results.append(chk(name, False, str(exc)))

        try:
            r = client.post(
                "/api/v1/ubrain/chat",
                headers=h,
                json={"message": "你好，请用一句话介绍优丁建材 AI SaaS 能做什么"},
            )
            body = r.json()
            data = body.get("data") or {}
            reply = str(data.get("reply") or data.get("message") or data.get("content") or "")
            ok = r.status_code == 200 and body.get("code", 0) == 0 and len(reply) > 4
            mock_hint = "mock" in reply.lower() and len(reply) < 30
            if mock_hint:
                ok = False
            results.append(
                chk(
                    "ubrain_chat_live",
                    ok,
                    f"status={r.status_code} intent={data.get('intent')} len={len(reply)}",
                )
            )
        except Exception as exc:
            results.append(chk("ubrain_chat_live", False, str(exc)))

    fails = sum(1 for x in results if not x["ok"])
    return _finish(results, fails)


def _finish(results: list[dict], fails: int) -> int:
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base": BASE,
        "passed": fails == 0,
        "fail_count": fails,
        "results": results,
    }
    out = ROOT / "docs" / "ubrain-flywheel-live-smoke-latest.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\nWrote {out}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
