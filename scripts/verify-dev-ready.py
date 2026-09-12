#!/usr/bin/env python3
"""开发栈就绪检查 — 产品 AI 路由 + NVIDIA Key。"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8001"


def _get(path: str) -> dict:
    req = urllib.request.Request(f"{BASE}{path}")
    with urllib.request.urlopen(req, timeout=8) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    errors: list[str] = []
    try:
        spec = _get("/openapi.json")
        paths = set(spec.get("paths") or {})
        if "/api/v1/ai/product/generate" not in paths:
            errors.append("缺少 /api/v1/ai/product/generate — 请运行 scripts/restart-dev-admin.ps1")
    except urllib.error.URLError as exc:
        errors.append(f"backend :8001 未启动 ({exc})")
        print("FAIL")
        for e in errors:
            print(" -", e)
        return 1

    try:
        login_body = json.dumps(
            {"username_or_email": "admin", "password": "admin123"}
        ).encode("utf-8")
        req = urllib.request.Request(
            f"{BASE}/api/v1/auth/login",
            data=login_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            token = json.loads(resp.read().decode("utf-8")).get("data", {}).get("access_token")
        if not token:
            errors.append("登录失败")
        else:
            gen_body = json.dumps(
                {
                    "content_type": "seo_title",
                    "product_name": "轻集料混凝土",
                    "category_name": "轻集料混凝土",
                    "strength_grade": "LC5.0",
                    "fire_rating": "A级",
                }
            ).encode("utf-8")
            req2 = urllib.request.Request(
                f"{BASE}/api/v1/ai/product/generate",
                data=gen_body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req2, timeout=60) as resp2:
                data = json.loads(resp2.read().decode("utf-8"))
            content = (data.get("data") or {}).get("content") or ""
            if not content.strip():
                errors.append("AI 生成返回空 content")
            else:
                print("OK product AI:", content[:80])
    except urllib.error.HTTPError as exc:
        errors.append(f"AI 接口 HTTP {exc.code} — 检查 NVIDIA Key / 重启 backend")
    except Exception as exc:
        errors.append(str(exc))

    if errors:
        print("FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print("READY for local/LAN test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
