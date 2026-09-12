#!/usr/bin/env python3
"""RZ-02 / FE-12 / BE-06 · 软著 60 页文件清单导出"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BACKEND_DIRS = [
    ROOT / "backend/app/api/v1/admin_bff",
    ROOT / "backend/app/core",
    ROOT / "backend/app/services",
]

FRONTEND_DIRS = [
    ROOT / "frontend/admin/src/constants",
    ROOT / "frontend/admin/src/components/youding",
    ROOT / "frontend/admin/src/views/client",
    ROOT / "frontend/admin/src/views/agent",
    ROOT / "frontend/admin/src/api/admin-bff.ts",
]

EXCLUDE_PARTS = {"node_modules", "_ref", "admin-vben", ".git", "__pycache__"}


def collect_files(paths: list[Path]) -> list[str]:
    out: list[str] = []
    for p in paths:
        if p.is_file():
            out.append(str(p.relative_to(ROOT)).replace("\\", "/"))
            continue
        if not p.is_dir():
            continue
        for f in sorted(p.rglob("*")):
            if not f.is_file():
                continue
            parts = set(f.parts)
            if parts & EXCLUDE_PARTS:
                continue
            if f.suffix.lower() in {".py", ".ts", ".vue", ".scss"}:
                out.append(str(f.relative_to(ROOT)).replace("\\", "/"))
    return out


def main() -> None:
    backend = collect_files(BACKEND_DIRS)
    frontend = collect_files(FRONTEND_DIRS)
    payload = {
        "backend_count": len(backend),
        "frontend_count": len(frontend),
        "backend_files": backend,
        "frontend_files": frontend,
        "note": "Export for RZ-02; exclude Vben/_ref/Stub lab",
    }
    out = ROOT / "docs/compliance/soft-copyright-file-export.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out} ({len(backend)} BE + {len(frontend)} FE files)")


if __name__ == "__main__":
    main()
