#!/usr/bin/env python3
"""AiToEarn 视频真发链路验收 — 不配 Key 会明确失败，配好则列出已绑账号。"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

# 优先 dev 配置
_dev_env = BACKEND / "config" / "dev" / ".env"
if _dev_env.is_file() and not os.getenv("AITOEARN_API_KEY"):
    for line in _dev_env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        if k.strip() in ("AITOEARN_API_KEY", "AITOEARN_API_BASE") and not os.getenv(k.strip()):
            os.environ[k.strip()] = v.strip().strip('"').strip("'")


def main() -> int:
    from app.services.aitoearn_publish_adapter import preflight_aitoearn_sync

    print("=== AiToEarn 视频发布预检 ===")
    data = preflight_aitoearn_sync()
    print(json.dumps(data, ensure_ascii=False, indent=2))
    if not data.get("ready"):
        print("\n[FAIL] 未就绪 — 按 setup 步骤配置后再试")
        return 1
    print(f"\n[OK] 就绪：{data.get('account_count')} 个账号可真发")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
