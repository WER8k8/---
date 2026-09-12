#!/usr/bin/env python3
"""site_content 多语种 i18n + AI 翻译验收。"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/site-content-i18n-validation-latest.json"

PYTEST_TARGETS = [
    "backend/tests/unit/test_site_content_i18n_service.py",
    "backend/tests/unit/test_site_content_i18n_ai_service.py",
    "backend/tests/unit/test_site_content_locale_service.py",
    "backend/tests/unit/test_public_visitor_context_api.py",
]


def main() -> int:
    py = ROOT / "backend/.venv/Scripts/python.exe"
    if not py.exists():
        py = Path(sys.executable)

    tests = subprocess.run(
        [str(py), "-m", "pytest", *PYTEST_TARGETS, "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    ok = tests.returncode == 0
    report = {
        "ok": ok,
        "task": "site-content-i18n-ai",
        "pytest_ok": ok,
        "targets": PYTEST_TARGETS,
        "pytest_tail": (tests.stdout + tests.stderr)[-1200:],
        "export_langs": ["zh", "ar", "es", "pt", "ru", "th", "vi", "id", "ms", "ja", "ko"],
        "backfill_script": "scripts/backfill-site-content-i18n.py",
        "backfill_ai_flag": "--ai",
        "hermes_task_type": "hermes_site_i18n",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
