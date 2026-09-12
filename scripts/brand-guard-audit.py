#!/usr/bin/env python3
"""COMP-02 品牌禁词抽检 CLI（租户可见文案）。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.hermes.brand_audit_service import audit_brand_leaks  # noqa: E402


def main() -> int:
    report = audit_brand_leaks(repo_root=ROOT)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report.get("ok"):
        print(f"\nOK — scanned {report.get('files_scanned', 0)} files, no leaks.")
        return 0
    print(
        f"\nFAIL — {report.get('violations_count', 0)} violation(s) "
        f"in {report.get('files_scanned', 0)} files."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
