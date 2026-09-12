#!/usr/bin/env python3
"""MOD-07 · 贸易情报 20×50 矩阵 PM 签字占位校验."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/mod-07-trade-matrix-signoff-latest.json"
RECORD = ROOT / "docs/compliance/mod-07-trade-intel-matrix-signoff-record.json"
CHECKLIST = ROOT / "docs/compliance/MOD-07-trade-intel-matrix-checklist.md"
TRADE_INTEL_VUE = ROOT / "frontend/admin/src/views/admin/ai-engine/trade-intel.vue"
ROUTER = ROOT / "frontend/admin/src/router/index.ts"


def ensure_record() -> dict:
    if RECORD.is_file():
        return json.loads(RECORD.read_text(encoding="utf-8"))
    data = {
        "task": "MOD-07",
        "status": "pending_pm_signoff",
        "matrix_spec": "20 categories × 50 countries",
        "ui_route": "/admin/ai-engine/trade-intel",
        "checklist": str(CHECKLIST.relative_to(ROOT)).replace("\\", "/"),
        "signatory_role": "产品经理",
        "signed_by": None,
        "signed_at": None,
        "notes": "PM 确认品类×国家矩阵范围与免责声明后签字；M2 API Key 可选",
    }
    RECORD.parent.mkdir(parents=True, exist_ok=True)
    RECORD.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return data


def main() -> int:
    record = ensure_record()
    router_text = ROUTER.read_text(encoding="utf-8") if ROUTER.is_file() else ""
    checks = {
        "record_json": RECORD.is_file(),
        "checklist_md": CHECKLIST.is_file(),
        "trade_intel_vue": TRADE_INTEL_VUE.is_file(),
        "router_trade_intel": "trade-intel" in router_text,
        "matrix_spec_documented": "20" in record.get("matrix_spec", "") and "50" in record.get("matrix_spec", ""),
    }
    signed = bool(record.get("signed_by"))
    ok = all(checks.values())
    out = {
        "ok": ok,
        "task": "MOD-07",
        "checks": checks,
        "signed": signed,
        "human_pending": not signed,
        "record": str(RECORD.relative_to(ROOT)),
    }
    REPORT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
