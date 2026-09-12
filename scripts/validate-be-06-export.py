#!/usr/bin/env python3
"""BE-06 · 60 页导出终验：meta + 页数 + 非空."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/compliance/rz-60-pages"
META = OUT / "meta.json"
EXPECTED = 60


def main() -> int:
    if not META.exists():
        print(json.dumps({"ok": False, "error": "run export-rz-60-pages.py first"}, indent=2))
        return 1

    meta = json.loads(META.read_text(encoding="utf-8"))
    pages = sorted(OUT.glob("page-*.txt"))
    empty = [p.name for p in pages if not p.read_text(encoding="utf-8").strip()]

    report = {
        "ok": len(pages) == EXPECTED and not empty and meta.get("exported") == EXPECTED,
        "exported": meta.get("exported"),
        "page_files": len(pages),
        "expected": EXPECTED,
        "empty_pages": empty,
        "total_source_pages": meta.get("total_source_pages"),
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
