#!/usr/bin/env python3
"""ARCH-03 · Hermes 写库边界静态审计 CLI。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.hermes.write_boundary_audit_service import audit_write_boundaries  # noqa: E402


def main() -> int:
    report = audit_write_boundaries()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report.get("ok"):
        print("\nOK — write boundary checks passed.")
        return 0
    print(f"\nFAIL — {report.get('violations_count', 0)} violation(s).")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
