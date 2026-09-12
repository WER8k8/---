#!/usr/bin/env python3
"""验证 SAU Sidecar 健康与 check 接口。"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

BASE = (os.environ.get("SAU_SIDECAR_URL") or "http://127.0.0.1:9910").rstrip("/")


def _get(path: str) -> dict:
    req = urllib.request.Request(f"{BASE}{path}")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def main() -> int:
    try:
        health = _get("/api/youding/health")
    except urllib.error.URLError as exc:
        print(f"FAIL: sidecar unreachable at {BASE}: {exc}")
        return 1
    if not health.get("ok"):
        print("FAIL: health not ok", health)
        return 1
    if health.get("mode") in ("mock", "reference", "stub"):
        print("FAIL: mock sidecar", health)
        return 1
    print("OK: SAU sidecar health", json.dumps(health, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
