# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""软著/送审干净源码包导出脚本（只读打包，不改代码）。

红线（AGENTS）：
    · 排除 _external / _archive / .env / 密钥 / node_modules / .git
    · 排除 external 大体积依赖
用法：
    python backend/scripts/export_clean_source_bundle.py --out docs/softcopy_youding_src.zip
"""
from __future__ import annotations

import argparse
import zipfile
from pathlib import Path
from typing import Any

# 需要打入包的相对根目录（相对 worktree backend 上级，即仓库根）
# 软著包：仅源码与关键文档（控制体积）
INCLUDE_DIRS = (
    "backend/app",
    "backend/tests",
    "backend/scripts",
    "backend/alembic_migrations",
    "frontend/admin/src",
    "frontend/admin/scripts",
    "docs/product",
    "docs/compose",
    "docs/能力台账",
    "scripts",
)
EXCLUDE_PARTS = (
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "_external",
    "external",
    "_archive",
    ".nuxt",
    "dist",
    ".output",
    "logs",
    "softcopy",
)
EXCLUDE_SUFFIX = (
    ".env",
    ".env.local",
    ".env.production",
    ".key",
    ".pem",
    ".p12",
    ".pyc",
    ".pyo",
    ".log",
)
EXCLUDE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "auto-secret-dev.txt",
    "youding_dev.db",
}


def _should_skip(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    parts = set(rel.parts)
    if parts & set(EXCLUDE_PARTS):
        return True
    if path.name in EXCLUDE_NAMES:
        return True
    if path.suffix.lower() in EXCLUDE_SUFFIX:
        return True
    if path.name.endswith((".env", ".pem", ".key")):
        return True
    return False


def export_bundle(repo_root: Path, out_path: Path) -> dict[str, Any]:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    total = 0
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for top in INCLUDE_DIRS:
            base = repo_root / top
            if not base.exists():
                continue
            for p in base.rglob("*"):
                if not p.is_file():
                    continue
                if _should_skip(p, repo_root):
                    continue
                arc = p.relative_to(repo_root).as_posix()
                low = arc.lower()
                if any(x in low for x in ("/_external/", "/_archive/", "/node_modules/", "/.venv/")):
                    continue
                if low.endswith(".env") or ("secret" in low and low.endswith(".txt")):
                    continue
                size = p.stat().st_size
                if size > 5 * 1024 * 1024:
                    continue
                zf.write(p, arcname=arc)
                count += 1
                total += size
    return {
        "out": str(out_path),
        "files": count,
        "bytes": total,
        "ok": count > 0,
        "hint": "送审前人工抽查：无 external/_archive/.env/密钥",
    }


if __name__ == "__main__":
    import json
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="docs/softcopy_youding_src.zip")
    parser.add_argument("--root", default="")
    args = parser.parse_args()
    script_path = Path(__file__).resolve()
    # backend/scripts/xxx.py -> parents[2] = repo root
    root = Path(args.root) if args.root else script_path.parents[2]
    out = Path(args.out)
    if not out.is_absolute():
        out = root / args.out
    result = export_bundle(root, out)
    print(json.dumps(result, ensure_ascii=False, indent=2))
