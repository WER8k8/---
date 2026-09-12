#!/usr/bin/env python3
"""COMM-PM-03 / COMM-PD-02 · Stub 矩阵与 stubVisibility.ts 同步校验."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / ".project/stub-matrix-T-PM-02-v1.json"
STUB_TS = ROOT / "frontend/admin/src/constants/stubVisibility.ts"
REPORT = ROOT / "docs/stub-matrix-sync-latest.json"


def _extract_string_array(ts: str, name: str) -> list[str]:
    m = re.search(rf"export const {name}\s*=\s*\[([\s\S]*?)\]\s*(?:as const)?", ts)
    if not m:
        return []
    return re.findall(r"['\"]([^'\"]+)['\"]", m.group(1))


def _extract_client_paths(ts: str) -> list[str]:
    m = re.search(
        r"export const CLIENT_STUB_RULES[^=]*=\s*\[([\s\S]*?)\]\s*(?:\n|$)",
        ts,
    )
    if not m:
        return []
    return re.findall(r"path:\s*['\"](/client/[^'\"]+)['\"]", m.group(1))


def main() -> int:
    if not MATRIX.is_file() or not STUB_TS.is_file():
        print(json.dumps({"ok": False, "error": "missing matrix or stubVisibility.ts"}, ensure_ascii=False))
        return 1

    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    ts = STUB_TS.read_text(encoding="utf-8")
    ts_platform = _extract_string_array(ts, "PLATFORM_LAB_PREFIXES")
    ts_killed = _extract_string_array(ts, "PLATFORM_KILLED_PREFIXES")
    ts_client_paths = _extract_client_paths(ts)

    matrix_platform = [r["path"] for r in matrix.get("platform_lab_prefixes", [])]
    matrix_killed = [r["path"] for r in matrix.get("platform_killed_prefixes", [])]
    matrix_client = [r["path"] for r in matrix.get("client_stub_rules", [])]

    missing_in_matrix = [p for p in ts_platform if p not in matrix_platform]
    extra_in_matrix = [p for p in matrix_platform if p not in ts_platform]
    killed_missing = [p for p in ts_killed if p not in matrix_killed]
    killed_extra = [p for p in matrix_killed if p not in ts_killed]
    client_missing = [p for p in ts_client_paths if p not in matrix_client]
    client_extra = [p for p in matrix_client if p not in ts_client_paths]

    overlap = [p for p in ts_platform if p in ts_killed]

    ok = not (
        missing_in_matrix
        or extra_in_matrix
        or killed_missing
        or killed_extra
        or client_missing
        or client_extra
        or overlap
    )
    report = {
        "ok": ok,
        "task": "T-PM-02",
        "platform_count_ts": len(ts_platform),
        "platform_count_matrix": len(matrix_platform),
        "killed_count_ts": len(ts_killed),
        "killed_count_matrix": len(matrix_killed),
        "client_count_ts": len(ts_client_paths),
        "client_count_matrix": len(matrix_client),
        "missing_in_matrix": missing_in_matrix,
        "extra_in_matrix": extra_in_matrix,
        "killed_missing_in_matrix": killed_missing,
        "killed_extra_in_matrix": killed_extra,
        "client_missing_in_matrix": client_missing,
        "client_extra_in_matrix": client_extra,
        "lab_kill_overlap": overlap,
        "matrix_path": str(MATRIX.relative_to(ROOT)),
    }
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
