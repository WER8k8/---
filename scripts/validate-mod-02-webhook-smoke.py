#!/usr/bin/env python3
"""MOD-02 · 读取 webhook 冒烟报告."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/mod-02-webhook-smoke-validation-latest.json"
SMOKE = ROOT / "docs/mod-02-webhook-smoke-latest.json"


def main() -> int:
    if not SMOKE.is_file():
        out = {"ok": False, "task": "MOD-02-smoke", "error": "run smoke-mod-02-inquiry-webhooks.ps1 first"}
        REPORT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 1
    data = json.loads(SMOKE.read_text(encoding="utf-8-sig"))
    ok = bool(data.get("pass"))
    out = {"ok": ok, "task": "MOD-02-smoke", "channels": data.get("channels"), "source": str(SMOKE.relative_to(ROOT))}
    REPORT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
