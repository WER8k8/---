#!/usr/bin/env python3
"""大陆 IP 访客上下文合规验收 · CN 仅微信/QQ/电话。"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/cn-visitor-context-validation-latest.json"


def main() -> int:
    py = ROOT / "backend/.venv/Scripts/python.exe"
    if not py.exists():
        py = Path(sys.executable)

    tests = subprocess.run(
        [
            str(py),
            "-m",
            "pytest",
            "backend/tests/unit/test_visitor_locale.py",
            "backend/tests/unit/test_public_visitor_context_api.py",
            "backend/tests/unit/test_public_wangcai_cn.py",
            "backend/tests/unit/test_site_content_locale_service.py",
            "backend/tests/unit/test_wangcai_reply_locale.py",
            "-q",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    ok = tests.returncode == 0
    report = {
        "ok": ok,
        "task": "CN-visitor-context",
        "pytest_ok": ok,
        "pytest_tail": (tests.stdout + tests.stderr)[-800:],
        "api_path": "/api/v1/public/tenants/{domain}/visitor-context",
        "cn_rule": "contact_channels only wechat/qq/phone; contacts omit whatsapp/email",
        "debug_headers": ["X-Visitor-Country: CN", "Accept-Language: zh-CN"],
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
