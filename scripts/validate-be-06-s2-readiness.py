#!/usr/bin/env python3
"""BE-06 · S2 readability 签字前置（60 页 + 模板就绪）."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/be-06-s2-readiness-latest.json"
TEMPLATE = ROOT / "docs/compliance/comp-02-readability-signoff.template.json"
META = ROOT / "docs/compliance/rz-60-pages/meta.json"


def main() -> int:
    py = ROOT / "backend/.venv/Scripts/python.exe"
    if not py.exists():
        py = Path(sys.executable)
    rz = subprocess.run([str(py), str(ROOT / "scripts/validate-rz-60-pages.py")], cwd=ROOT, capture_output=True, text=True)
    rz_ok = rz.returncode == 0

    meta_ok = False
    exported = 0
    if META.is_file():
        meta = json.loads(META.read_text(encoding="utf-8-sig"))
        exported = int(meta.get("exported") or 0)
        meta_ok = exported >= 60

    checks = {
        "rz_validate": rz_ok,
        "meta_exported_60": meta_ok,
        "signoff_template": TEMPLATE.is_file(),
        "validate_be06_export_script": (ROOT / "scripts/validate-be-06-export.py").is_file(),
    }
    ok = all(checks.values())
    out = {
        "ok": ok,
        "task": "BE-06-s2-readiness",
        "checks": checks,
        "exported": exported,
        "human_pending": "S2：BE lead 填写 comp-02-readability-signoff",
    }
    REPORT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
