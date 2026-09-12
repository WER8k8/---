#!/usr/bin/env python3
"""COMP-06 · 律师签字记录校验（S2；未签时不阻断 gate）."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/comp-06-lawyer-signoff-validation-latest.json"
RECORD = ROOT / "docs/compliance/comp-06-lawyer-signoff-record.json"
DRAFT = ROOT / "docs/compliance/comp-06-lawyer-review-draft-20260602.md"
BUNDLE_VAL = ROOT / "docs/compliance/comp-06-validation-latest.json"


def main() -> int:
    record = json.loads(RECORD.read_text(encoding="utf-8-sig")) if RECORD.is_file() else {}
    bundle_ok = False
    if BUNDLE_VAL.is_file():
        bundle_ok = json.loads(BUNDLE_VAL.read_text(encoding="utf-8-sig")).get("ok") is True

    signed = bool(record.get("signed_by"))
    checks = {
        "signoff_record": RECORD.is_file(),
        "lawyer_draft": DRAFT.is_file(),
        "bundle_validation_green": bundle_ok,
    }
    ok = all(checks.values())
    out = {
        "ok": ok,
        "task": "COMP-06-lawyer-signoff",
        "checks": checks,
        "signed": signed,
        "human_pending": not signed,
        "apply_command": "python scripts/apply-comp-06-lawyer-signoff.py --name 律师姓名 --firm 律所名",
    }
    REPORT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
