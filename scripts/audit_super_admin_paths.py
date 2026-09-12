#!/usr/bin/env python3
"""扫描管理端 super-admin API 引用并与 FastAPI 挂载路径对照（P0-08）。"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
PATTERN = re.compile(
    r"""['"](/api/v1/super-admin[^'"]+)['"]|"""
    r"""['"`](/super-admin[^'"]+)['"`]"""
)


def collect() -> set[str]:
    found: set[str] = set()
    for base in (FRONTEND / "admin", FRONTEND / "pages"):
        if not base.is_dir():
            continue
        for ext in ("*.vue", "*.ts", "*.js"):
            for path in base.rglob(ext):
                if "node_modules" in path.parts or "dist" in path.parts:
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
                for m in PATTERN.finditer(text):
                    p = m.group(1) or m.group(2)
                    if p.startswith("/api/v1"):
                        p = p[len("/api/v1") :]
                    if p.startswith("/super-admin"):
                        found.add(p.split("?")[0].rstrip("/"))
    return found


def main() -> int:
    paths = sorted(collect())
    print(f"frontend super-admin references: {len(paths)}")
    for p in paths[:120]:
        print(f"  {p}")
    if len(paths) > 120:
        print(f"  ... +{len(paths) - 120} more")
    print("\nRun backend GET /api/v1/ops/super-admin-route-audit (auth) for live diff.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
