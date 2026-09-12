#!/usr/bin/env python3
"""IP-04 · 每周 COMP-K3 失信风险扫描（禁止清单路径）"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / "docs" / "compliance" / "soft-copyright-file-export.json"
FORBIDDEN_GLOBS = [
    "frontend/admin-vben",
    "_ref",
    "node_modules",
    "dist",
]

SCAN_DIRS = [
    ROOT / "docs" / "compliance" / "rz-60-pages",
    ROOT / "frontend" / "admin" / "src",
    ROOT / "backend" / "app",
]


def scan_file_list(paths: list[str]) -> list[str]:
    hits = []
    for p in paths:
        norm = p.replace("\\", "/")
        for bad in FORBIDDEN_GLOBS:
            if bad in norm:
                hits.append(p)
                break
    return hits


def main() -> int:
    hits: list[str] = []
    if EXPORT.exists():
        data = json.loads(EXPORT.read_text(encoding="utf-8"))
        for key in ("backend", "frontend"):
            hits.extend(scan_file_list(data.get(key, [])))

    text_hits: list[str] = []
    for d in SCAN_DIRS:
        if not d.is_dir():
            continue
        for f in d.rglob("*"):
            if not f.is_file():
                continue
            rel = str(f.relative_to(ROOT)).replace("\\", "/")
            for bad in FORBIDDEN_GLOBS:
                if bad in rel:
                    text_hits.append(rel)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "export_json_hits": hits,
        "filesystem_hits_sample": text_hits[:20],
        "risk_level": "high" if hits else "low",
    }
    out = ROOT / "docs" / "compliance" / "ip-04-weekly-scan-latest.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    if hits:
        print(f"[WARN] {len(hits)} forbidden paths in export JSON")
        return 1
    print("[PASS] IP-04 weekly scan: export JSON clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
