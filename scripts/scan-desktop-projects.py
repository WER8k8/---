#!/usr/bin/env python3
"""Scan Desktop project folders — exclude heavy dirs, emit JSON report."""
from __future__ import annotations

import json
import os
from pathlib import Path

DESKTOP = Path(r"C:\Users\97907\Desktop")
OUT = DESKTOP / "上线网站" / "results" / "desktop-project-scan.json"

SKIP_DIRS = {
    "node_modules", ".venv", "venv", "__pycache__", ".git", ".output",
    "dist", "build", ".nuxt", ".pytest_cache", "backup_auto", ".next",
    "coverage", ".turbo", ".pnpm-store", ".obsidian",
}

MARKERS = {
    "backend": "backend",
    "frontend": "frontend",
    "frontend_admin": "frontend/admin",
    "docs": "docs",
    "pm_doc": "docs/产品经理-开发文档.md",
    "source_repo": "docs/SOURCE-REPO.md",
    "readme": "README.md",
    "package_json": "frontend/package.json",
    "requirements": "backend/requirements.txt",
}


def count_files(root: Path) -> int:
    n = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        n += len(filenames)
    return n


def scan_root(root: Path) -> dict:
    if not root.is_dir():
        return {"path": str(root), "exists": False}
    row = {
        "path": str(root),
        "name": root.name,
        "exists": True,
        "files_excl_heavy": count_files(root),
        "git": (root / ".git").is_dir(),
    }
    for key, rel in MARKERS.items():
        row[key] = (root / rel).exists()
    # top-level sample
    try:
        row["top_level"] = sorted(
            [p.name + ("/" if p.is_dir() else "") for p in root.iterdir()][:40]
        )
    except OSError:
        row["top_level"] = []
    return row


def main() -> None:
    roots: list[Path] = []
    if DESKTOP.is_dir():
        for p in sorted(DESKTOP.iterdir()):
            if p.is_dir() and p.name not in {"__pycache__"}:
                roots.append(p)
    # UJ children explicitly
    uj = DESKTOP / "UJ"
    if uj.is_dir():
        for p in uj.iterdir():
            if p.is_dir() and p not in roots:
                roots.append(p)
    # 汇总 children if any
    hz = DESKTOP / "汇总"
    if hz.is_dir():
        for p in hz.iterdir():
            if p.is_dir():
                roots.append(p)

    seen = set()
    unique: list[Path] = []
    for p in roots:
        key = str(p.resolve()).lower()
        if key not in seen:
            seen.add(key)
            unique.append(p)

    report = {
        "desktop_dir_count": len(list(DESKTOP.iterdir())) if DESKTOP.is_dir() else 0,
        "scanned": [scan_root(p) for p in unique],
    }
    report["scanned"].sort(key=lambda x: x.get("files_excl_heavy", 0), reverse=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT} ({len(report['scanned'])} roots)")


if __name__ == "__main__":
    main()
