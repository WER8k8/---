#!/usr/bin/env python3
"""Hermes 视频发布 Worker 预检验收。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.publish_workers.tier_router import preflight_workers, platform_tier_chain


def main() -> int:
    pf = preflight_workers()
    print("=== Hermes 视频发布 Worker 预检 ===")
    print(json.dumps(pf, ensure_ascii=False, indent=2))
    print("\n平台 Worker 链（当前环境）：")
    for name in ("抖音", "快手", "哔哩哔哩", "小红书", "微信视频号", "YouTube"):
        chain = platform_tier_chain(name)
        print(f"  {name}: {' → '.join(chain) if chain else '(无)'}")
    return 0 if pf.get("ready") else 1


if __name__ == "__main__":
    raise SystemExit(main())
