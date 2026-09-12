#!/usr/bin/env python3
"""ITER-01c · 开户链 smoke（注册→建站→IM→旺财→发布 相关单测）。"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/iter-01c-onboarding-chain-validation-latest.json"

PYTEST_TARGETS = [
    "backend/tests/unit/test_onboarding_chain.py",
    "backend/tests/unit/test_onboarding_im_contacts.py",
    "backend/tests/unit/test_onboarding_first_publish.py",
    "backend/tests/unit/test_onboarding_autopilot.py",
    "backend/tests/unit/test_wangcai_entry_parity.py",
    "backend/tests/unit/test_public_visitor_context_api.py",
    "backend/tests/unit/test_public_wangcai_cn.py",
    "backend/tests/unit/test_site_content_locale_service.py",
    "backend/tests/unit/test_wangcai_reply_locale.py",
]


def main() -> int:
    py = ROOT / "backend/.venv/Scripts/python.exe"
    if not py.exists():
        py = Path(sys.executable)

    test = subprocess.run(
        [str(py), "-m", "pytest", *PYTEST_TARGETS, "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    ok = test.returncode == 0
    report = {
        "ok": ok,
        "task": "ITER-01c",
        "pytest_ok": ok,
        "targets": PYTEST_TARGETS,
        "pytest_tail": (test.stdout + test.stderr)[-1200:],
        "manual_e2e": [
            "注册 → /client/onboarding?product=…",
            "Hermes 建站保存 → site_built",
            "IM 联系方式 → im_contacts_done",
            "旺财预览与公开 /public/tenants/{domain}/wangcai/ask 同源",
            "Nuxt /tenant?__tenant={domain} 大陆头无 WhatsApp",
        ],
        "human_recording_pending": True,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
