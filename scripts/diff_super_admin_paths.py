#!/usr/bin/env python3
"""对比前端 super-admin 引用与 FastAPI 挂载路径（P0-08）。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend" / "admin"
PATTERN = re.compile(
    r"""['"](/api/v1/super-admin[^'"]+)['"]|"""
    r"""['"](/super-admin[^'"]+)['"]|"""
    r"""apiGet\(\s*['"](/super-admin[^'"]+)['"]"""
)


def collect_frontend() -> set[str]:
    found: set[str] = set()
    for ext in ("*.vue", "*.ts", "*.js"):
        for path in FRONTEND.rglob(ext):
            if "node_modules" in path.parts or "dist" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for m in PATTERN.finditer(text):
                p = m.group(1) or m.group(2) or m.group(3)
                if p.startswith("/api/v1"):
                    p = p[len("/api/v1") :]
                if not p.startswith("/super-admin"):
                    continue
                found.add(p.split("?")[0].rstrip("/"))
    return found


def collect_mounted() -> set[str]:
    sys.path.insert(0, str(ROOT / "backend"))
    from app.main import app

    out: set[str] = set()
    for r in app.routes:
        p = (getattr(r, "path", "") or "").rstrip("/")
        if "/super-admin" in p:
            out.add(p[len("/api/v1") :] if p.startswith("/api/v1") else p)
    return out


def path_matches(call: str, mounted: set[str]) -> bool:
    if call in mounted:
        return True
    for m in mounted:
        if m.startswith(call + "/") or call.startswith(m + "/"):
            return True
        # param routes: /super-admin/foo/{id} vs /super-admin/foo/abc
        if "{" in m:
            prefix = m.split("{")[0].rstrip("/")
            if call.startswith(prefix):
                return True
    return False


def main() -> int:
    fe = collect_frontend()
    mounted = collect_mounted()
    missing = sorted(p for p in fe if not path_matches(p, mounted))
    print(f"frontend refs: {len(fe)}, mounted: {len(mounted)}, missing: {len(missing)}")
    for p in missing[:40]:
        print(f"  MISSING {p}")
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
