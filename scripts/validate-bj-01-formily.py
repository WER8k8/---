#!/usr/bin/env python3
"""BJ-01 · Formily site-editor 自动化验收（文件 + BFF 单测）."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADMIN = ROOT / "frontend/admin"
REPORT = ROOT / "docs/bj-01-formily-validation-latest.json"

REQUIRED = [
    ADMIN / "src/components/youding/YdFormilyForm.vue",
    ADMIN / "src/components/youding/formily/antdv-bridge.ts",
    ADMIN / "src/components/youding/formily/siteEditorSchema.ts",
    ADMIN / "src/constants/lProTier1Locales.ts",
    ADMIN / "src/views/client/site-editor-lab.vue",
    ROOT / "docs/bj-01-formily-saas-five-questions.md",
    ROOT / "docs/bj-01-saas-signoff-record.json",
]


def main() -> int:
    files_ok = {str(p.relative_to(ROOT)): p.exists() for p in REQUIRED}
    py = ROOT / "backend/.venv/Scripts/python.exe"
    if not py.exists():
        py = Path(sys.executable)

    test = subprocess.run(
        [
            str(py),
            "-m",
            "pytest",
            "backend/tests/unit/test_lab_site_editor_bff.py",
            "-q",
        ],
        cwd=ROOT,
        env={
            **dict(__import__("os").environ),
            "DATABASE_URL": "sqlite:///:memory:",
            "ENVIRONMENT": "testing",
            "DB_TYPE": "sqlite",
        },
        capture_output=True,
        text=True,
    )
    bff_test_ok = test.returncode == 0
    ok = all(files_ok.values()) and bff_test_ok

    report = {
        "ok": ok,
        "task": "BJ-01",
        "files": files_ok,
        "bff_test_ok": bff_test_ok,
        "pytest_tail": (test.stdout + test.stderr)[-500:],
        "saas_checklist": "docs/bj-01-formily-saas-five-questions.md",
        "signoff_record": "docs/bj-01-saas-signoff-record.json",
        "human_signoff_pending": True,
    }
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
