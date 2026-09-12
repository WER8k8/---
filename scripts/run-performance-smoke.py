#!/usr/bin/env python3
"""送检前性能冒烟：登录 + 核心 API 延迟采样（无需 Locust）。"""
from __future__ import annotations

import json
import statistics
import sys
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8001"
SAMPLES = 20
P99_MAX_MS = 2000
P50_MAX_MS = 500


def req(method: str, path: str, body: dict | None = None, token: str | None = None) -> tuple[int, float]:
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            resp.read()
            return resp.status, (time.perf_counter() - t0) * 1000
    except urllib.error.HTTPError as e:
        e.read()
        return e.code, (time.perf_counter() - t0) * 1000


def sample(name: str, method: str, path: str, token: str | None = None) -> dict:
    times: list[float] = []
    status = 0
    for _ in range(SAMPLES):
        status, ms = req(method, path, token=token)
        times.append(ms)
    times.sort()
    p50 = times[len(times) // 2]
    p99 = times[int(len(times) * 0.99) or -1]
    return {
        "name": name,
        "path": path,
        "status_last": status,
        "p50_ms": round(p50, 1),
        "p99_ms": round(p99, 1),
        "ok": p99 <= P99_MAX_MS,
    }


def main() -> int:
    report: dict = {"base": BASE, "samples": SAMPLES, "endpoints": [], "passed": True}
    try:
        code, _ = req("GET", "/api/v1/system/health")
        if code >= 500:
            report["error"] = f"health HTTP {code}"
            report["passed"] = False
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 1
    except OSError as e:
        report["error"] = f"backend unreachable: {e}"
        report["passed"] = False
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1

    login_code, _ = req(
        "POST",
        "/api/v1/auth/login",
        {"username_or_email": "admin", "password": "admin123"},
    )
    token = None
    if login_code == 200:
        _, _ = req("POST", "/api/v1/auth/login", {"username_or_email": "admin", "password": "admin123"})
        # re-fetch for token body
        url = f"{BASE}/api/v1/auth/login"
        body = json.dumps({"username_or_email": "admin", "password": "admin123"}).encode()
        req_obj = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req_obj, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            token = data.get("access_token") or data.get("data", {}).get("access_token")

    for name, method, path in [
        ("health", "GET", "/api/v1/system/health"),
        ("products", "GET", "/api/v1/products?page=1&page_size=20"),
        ("dashboard", "GET", "/api/v1/dashboard"),
    ]:
        row = sample(name, method, path, token=token)
        report["endpoints"].append(row)
        if not row["ok"]:
            report["passed"] = False

    out = __file__.replace("run-performance-smoke.py", "../docs/申报材料/performance-smoke-latest.json")
    import pathlib
    p = pathlib.Path(__file__).resolve().parent.parent / "docs" / "申报材料" / "performance-smoke-latest.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "out": str(p), "endpoints": report["endpoints"]}, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
