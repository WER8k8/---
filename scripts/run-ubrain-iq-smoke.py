#!/usr/bin/env python3
"""UBrain 实机智商 smoke — 多意图探测是否 Mock/模板。"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8001"
USER, PASS = "admin", "admin123"

CASES = [
    {
        "id": "reasoning",
        "message": "一个租户本月询盘 12 条、成交 2 单，请用一句话给出最该优先做的动作，不要泛泛而谈。",
        "expect": ["询盘", "成交", "优先"],
        "reject": ["我是AI助手", "很高兴为您服务", "mock"],
    },
    {
        "id": "trade_intel",
        "message": "保温板出口越南可行性怎么样？",
        "expect": ["越南", "VN"],
        "reject": ["mock", "示例回复"],
    },
    {
        "id": "tool_routing",
        "message": "帮我查一下轻集料混凝土 HS 编码",
        "expect": ["6810", "HS", "编码"],
        "reject": [],
    },
    {
        "id": "anti_template",
        "message": "请只回复数字 42，不要任何其它字。",
        "expect": ["42"],
        "reject": ["我是", "助手"],
    },
]


def score_reply(case: dict, data: dict) -> dict:
    reply = str(
        data.get("reply")
        or data.get("message")
        or data.get("content")
        or data.get("answer")
        or ""
    )
    tool = data.get("tool") or data.get("tool_name")
    intent = data.get("intent")
    tr = data.get("tool_result") or {}
    if isinstance(tr, dict):
        reply = reply or json.dumps(tr, ensure_ascii=False)[:500]

    low = reply.lower()
    hits = [w for w in case["expect"] if w.lower() in low or w in reply]
    bad = [w for w in case["reject"] if w.lower() in low]
    mock_flag = bool(data.get("mock")) or "mockllm" in low or reply.startswith("【模拟")

    ok = len(hits) >= 1 and not bad and not mock_flag and len(reply.strip()) >= 3
    if case["id"] == "anti_template":
        ok = "42" in reply.strip()[:10] and not mock_flag

    return {
        "id": case["id"],
        "ok": ok,
        "intent": intent,
        "tool": tool,
        "reply_preview": reply[:280].replace("\n", " "),
        "expect_hits": hits,
        "reject_hits": bad,
        "mock_suspect": mock_flag,
        "needs_confirmation": data.get("needs_confirmation"),
    }


def main() -> int:
    results = []
    with httpx.Client(base_url=BASE, timeout=120.0) as client:
        r = client.post(
            "/api/v1/auth/login",
            json={"username_or_email": USER, "password": PASS},
        )
        token = (r.json().get("data") or r.json()).get("access_token")
        if not token:
            print("login failed", r.status_code, r.text[:200])
            return 1
        h = {"Authorization": f"Bearer {token}"}

        for case in CASES:
            try:
                resp = client.post(
                    "/api/v1/ubrain/chat",
                    headers=h,
                    json={"message": case["message"]},
                )
                body = resp.json()
                data = body.get("data") or {}
                row = score_reply(case, data)
                row["http"] = resp.status_code
                row["code"] = body.get("code")
            except Exception as exc:
                row = {"id": case["id"], "ok": False, "error": str(exc)}
            results.append(row)
            print(json.dumps(row, ensure_ascii=False))

    passed = sum(1 for x in results if x.get("ok"))
    verdict = "真能用" if passed >= 3 else ("半吊子" if passed >= 2 else "偏智障/模板")
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "passed": passed,
        "total": len(results),
        "verdict": verdict,
        "results": results,
    }
    out = ROOT / "docs" / "ubrain-iq-smoke-latest.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n=== {passed}/{len(results)} PASS · 结论: {verdict} ===")
    print(f"Report: {out}")
    return 0 if passed >= 3 else 1


if __name__ == "__main__":
    raise SystemExit(main())
