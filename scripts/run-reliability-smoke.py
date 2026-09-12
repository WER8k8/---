#!/usr/bin/env python3
"""可靠性冒烟：连续探测 health 端点（默认 60 次 × 5s ≈ 5 分钟）。"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8001"
INTERVAL_SEC = 5
ROUNDS = int(os.getenv("RELIABILITY_ROUNDS", "60"))
PATH = "/api/v1/system/health"


def ping() -> tuple[bool, float, int | None]:
    url = f"{BASE}{PATH}"
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=8) as resp:
            ms = (time.perf_counter() - t0) * 1000
            return resp.status < 500, ms, resp.status
    except urllib.error.HTTPError as e:
        ms = (time.perf_counter() - t0) * 1000
        return e.code < 500, ms, e.code
    except OSError:
        return False, (time.perf_counter() - t0) * 1000, None


def main() -> int:
    results = []
    ok_count = 0
    for i in range(ROUNDS):
        ok, ms, code = ping()
        if ok:
            ok_count += 1
        results.append({"round": i + 1, "ok": ok, "ms": round(ms, 1), "status": code})
        if i + 1 < ROUNDS:
            time.sleep(INTERVAL_SEC)

    report = {
        "base": BASE,
        "path": PATH,
        "rounds": ROUNDS,
        "interval_sec": INTERVAL_SEC,
        "success_rate": round(ok_count / ROUNDS * 100, 2),
        "passed": ok_count == ROUNDS,
        "samples": results[:5] + (["..."] if ROUNDS > 10 else []) + results[-3:],
    }
    out = Path(__file__).resolve().parent.parent / "docs" / "申报材料" / "reliability-smoke-latest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "success_rate": report["success_rate"], "out": str(out)}, ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
