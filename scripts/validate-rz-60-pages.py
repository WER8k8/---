#!/usr/bin/env python3
"""COMP-02 · 60 页导出校验 + BE-06 readability 前置"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "docs" / "compliance" / "rz-60-pages"
META = PAGES / "meta.json"
FORBIDDEN = ["admin-vben", "_ref/", "node_modules", "v2ray", "vue-vben-admin"]


def main() -> int:
    fails = 0
    files = sorted(PAGES.glob("page-*.txt"))
    if len(files) != 60:
        print(f"[FAIL] expected 60 pages, got {len(files)}")
        fails += 1
    else:
        print(f"[PASS] page count = 60")

    empty = [f.name for f in files if f.stat().st_size < 50]
    if empty:
        print(f"[FAIL] empty/small pages: {empty[:5]}")
        fails += 1
    else:
        print("[PASS] no empty pages")

    hit_forbidden: list[str] = []
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        for bad in FORBIDDEN:
            if bad in text:
                hit_forbidden.append(f"{f.name}:{bad}")
    if hit_forbidden:
        print(f"[FAIL] forbidden refs: {hit_forbidden[:5]}")
        fails += 1
    else:
        print("[PASS] no forbidden strings in 60 pages")

    meta = {}
    if META.exists():
        meta = json.loads(META.read_text(encoding="utf-8"))
    report = {
        "page_count": len(files),
        "forbidden_hits": hit_forbidden,
        "meta": meta,
        "readability_signoff_pending": True,
    }
    out = ROOT / "docs" / "compliance" / "comp-02-rz-validation.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out}")

    if fails:
        print(f"COMP-02 validation: {fails} FAILED")
        return 1
    print("COMP-02 validation: PASS (awaiting human signoff)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
