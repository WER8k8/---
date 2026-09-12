#!/usr/bin/env python3
"""SITE-DESIGN-01g · W3 多语言 Tier1+2 UI + 建站发布就绪条验收。"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / ".project" / "site-design-target.json"
REPORT = ROOT / "docs" / "site-design-w3-validation-latest.json"

W3_FILES = [
    "frontend/components/tenant/premium/LProLanguagePicker.vue",
    "frontend/components/tenant/premium/PremiumB2bShell.vue",
    "frontend/composables/useTenantLanguagePicker.ts",
    "frontend/utils/l-pro-publish-gate.ts",
    "frontend/admin/src/components/site-builder/SiteEditorLProPublishBanner.vue",
    "frontend/admin/src/views/tenants/site-editor.vue",
    "backend/app/api/v1/routes/public_visitor_context.py",
]


def _contract_issues() -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not CONTRACT.is_file():
        issues.append({"severity": "P0", "check": "contract", "detail": "missing site-design-target.json"})
        return issues
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    tier1 = data.get("multilingual", {}).get("tier1_core", {})
    if tier1.get("count") != 12:
        issues.append(
            {
                "severity": "P0",
                "check": "tier1_count",
                "detail": "multilingual.tier1_core.count must be 12",
            }
        )
    waves = data.get("implementation_waves", [])
    w3 = next((w for w in waves if w.get("wave") == "W3"), None)
    if not w3 or "SITE-DESIGN-01g" not in (w3.get("tasks") or []):
        issues.append(
            {
                "severity": "P1",
                "check": "w3_wave",
                "detail": "implementation_waves missing W3 / SITE-DESIGN-01g",
            }
        )
    return issues


def _file_issues() -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for rel in W3_FILES:
        path = ROOT / rel
        if not path.is_file():
            issues.append({"severity": "P0", "check": "w3_file", "detail": f"missing {rel}"})
    shell = (ROOT / "frontend/components/tenant/premium/PremiumB2bShell.vue").read_text(encoding="utf-8")
    if "LProLanguagePicker" not in shell:
        issues.append(
            {
                "severity": "P0",
                "check": "shell_lang_picker",
                "detail": "PremiumB2bShell must mount LProLanguagePicker",
            }
        )
    if "SiteEditorLProPublishBanner" not in (
        ROOT / "frontend/admin/src/views/tenants/site-editor.vue"
    ).read_text(encoding="utf-8"):
        issues.append(
            {
                "severity": "P0",
                "check": "editor_publish_banner",
                "detail": "site-editor.vue must mount SiteEditorLProPublishBanner",
            }
        )
    ctx = (ROOT / "backend/app/api/v1/routes/public_visitor_context.py").read_text(encoding="utf-8")
    if "supported_languages" not in ctx:
        issues.append(
            {
                "severity": "P0",
                "check": "supported_languages_api",
                "detail": "visitor-context must return supported_languages",
            }
        )
    return issues


def _tenant_page_issues() -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    script = ROOT / "scripts" / "validate-tenant-pages-git.py"
    if not script.is_file():
        issues.append(
            {"severity": "P1", "check": "tenant_pages_gate", "detail": "missing validate-tenant-pages-git.py"}
        )
        return issues
    proc = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        issues.append(
            {
                "severity": "P0",
                "check": "tenant_pages_git",
                "detail": (proc.stdout or proc.stderr or "tenant pages git gate failed").strip()[:500],
            }
        )
    return issues


def _run_pytest() -> tuple[bool, str]:
    py = ROOT / "backend/.venv/Scripts/python.exe"
    if not py.exists():
        py = Path(sys.executable)
    env = dict(__import__("os").environ)
    env["DATABASE_URL"] = "sqlite:///:memory:"
    env["ENVIRONMENT"] = "testing"
    env["DB_TYPE"] = "sqlite"
    tests = subprocess.run(
        [
            str(py),
            "-m",
            "pytest",
            "tests/unit/test_public_visitor_context_api.py",
            "-q",
        ],
        cwd=ROOT / "backend",
        env=env,
        capture_output=True,
        text=True,
    )
    tail = (tests.stdout + tests.stderr)[-1200:]
    return tests.returncode == 0, tail


def main() -> int:
    issues = _contract_issues() + _file_issues() + _tenant_page_issues()
    pytest_ok, pytest_tail = _run_pytest()
    if not pytest_ok:
        issues.append(
            {
                "severity": "P0",
                "check": "pytest_visitor_context",
                "detail": "visitor-context language E2E tests failed",
            }
        )

    p0 = sum(1 for i in issues if i["severity"] == "P0")
    p1 = sum(1 for i in issues if i["severity"] == "P1")
    ok = p0 == 0 and pytest_ok

    report = {
        "ok": ok,
        "task": "SITE-DESIGN-01g",
        "contract_id": "SITE-DESIGN-01",
        "wave": "W3",
        "p0": p0,
        "p1": p1,
        "pytest_ok": pytest_ok,
        "pytest_tail": pytest_tail,
        "issues": issues,
        "w3_files_checked": W3_FILES,
        "acceptance": [
            "Tier1 12 语下拉 + Tier2 Google 翻译外链",
            "visitor-context supported_languages + language 参数切换",
            "建站页发布就绪 / 还差 N 项提示条",
        ],
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
