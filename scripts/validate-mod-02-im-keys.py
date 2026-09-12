#!/usr/bin/env python3
"""MOD-02 · 询盘 IM 生产密钥占位与 webhook 路由校验."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/mod-02-im-keys-validation-latest.json"
ENV_TEMPLATE = ROOT / "deploy/production/env.template"
OPENAPI = ROOT / "backend/openapi.json"

ENV_KEYS = (
    "INQUIRY_WEBHOOK_SECRET",
    "WECOM_CORP_ID",
    "WECOM_AGENT_SECRET",
    "DOUYIN_APP_ID",
    "DOUYIN_APP_SECRET",
)

CODE_PATHS = (
    ROOT / "backend/app/api/v1/routes/inquiry_channels.py",
    ROOT / "backend/app/services/im_channel_webhook_service.py",
    ROOT / "docs/compliance/MOD-02-im-prod-handoff-checklist.md",
)


def main() -> int:
    env_text = ENV_TEMPLATE.read_text(encoding="utf-8") if ENV_TEMPLATE.is_file() else ""
    env_ok = {k: k in env_text for k in ENV_KEYS}

    openapi = OPENAPI.read_text(encoding="utf-8") if OPENAPI.is_file() else ""
    routes_ok = {
        "wecom_webhook": "/inquiries/channels/wecom" in openapi,
        "douyin_webhook": "/inquiries/channels/douyin" in openapi,
    }
    files_ok = {str(p.relative_to(ROOT)): p.is_file() for p in CODE_PATHS}

    py = ROOT / "backend/.venv/Scripts/python.exe"
    if not py.exists():
        py = Path(sys.executable)
    test = subprocess.run(
        [str(py), "-m", "pytest", "backend/tests/unit/test_inquiry_channel_webhooks.py", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    webhook_tests_ok = test.returncode == 0

    ok = all(env_ok.values()) and all(routes_ok.values()) and all(files_ok.values()) and webhook_tests_ok
    report = {
        "ok": ok,
        "task": "MOD-02",
        "env_template_keys": env_ok,
        "openapi_routes": routes_ok,
        "files": files_ok,
        "webhook_tests_ok": webhook_tests_ok,
        "human_pending": "生产密钥回填 + 企微/抖音实机联调",
        "pytest_tail": (test.stdout + test.stderr)[-400:],
    }
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
