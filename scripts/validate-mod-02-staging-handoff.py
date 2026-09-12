#!/usr/bin/env python3
"""MOD-02 · staging 联调示例与 smoke 脚本就绪."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/mod-02-staging-handoff-latest.json"

FILES = (
    ROOT / "deploy/staging/mod02-webhook.env.example",
    ROOT / "scripts/smoke-mod-02-inquiry-webhooks.ps1",
    ROOT / "docs/compliance/MOD-02-im-prod-handoff-checklist.md",
)


def main() -> int:
    checks = {str(p.relative_to(ROOT)): p.is_file() for p in FILES}
    example = ROOT / "deploy/staging/mod02-webhook.env.example"
    has_secret_key = "INQUIRY_WEBHOOK_SECRET" in example.read_text(encoding="utf-8") if example.is_file() else False
    checks["example_has_webhook_secret"] = has_secret_key
    ok = all(checks.values())
    out = {
        "ok": ok,
        "task": "MOD-02-staging-handoff",
        "checks": checks,
        "human_pending": "生产 env.template 回填 + 企微/抖音平台联调",
    }
    REPORT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
