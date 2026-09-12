#!/usr/bin/env python3
"""A-04：管理端 API 前缀冒烟 — 枚举 app.main 路由并校验关键前缀已挂载。"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

os.environ.setdefault(
    "JWT_SECRET_KEY",
    "ci-admin-smoke-only-" + ("x" * 32),
)

from app.main import app  # noqa: E402

# 15 个关键 API 前缀（超管 / SEO / 呼朋唤友，对应管理端冒烟范围）
KEY_PREFIXES = [
    "/api/v1/referral",
    "/api/v1/super-admin/dashboard",
    "/api/v1/super-admin/auth",
    "/api/v1/super-admin/users",
    "/api/v1/super-admin/menus",
    "/api/v1/super-admin/monitor",
    "/api/v1/seo/site-audit",
    "/api/v1/seo/content-optimizer",
    "/api/v1/seo/llms-txt",
    "/api/v1/seo/schema-markup",
    "/api/v1/seo/authors",
    "/api/v1/seo/compliance",
    "/api/v1/seo/keywords",
    "/api/v1/seo/dashboard",
    "/api/v1/seo-matrix/dashboard",
]

OUTPUT = ROOT / "docs" / "admin-smoke-result.txt"


def all_paths() -> list[str]:
    out: list[str] = []
    for r in app.routes:
        p = getattr(r, "path", "") or ""
        if p:
            out.append(p)
    return out


def prefix_mounted(prefix: str, paths: list[str]) -> bool:
    base = prefix.rstrip("/")
    return any(p == base or p.startswith(base + "/") for p in paths)


def main() -> int:
    paths = all_paths()
    lines: list[str] = [
        f"# Admin smoke route check — {datetime.now(timezone.utc).isoformat()}",
        f"total_routes={len(paths)}",
        "",
    ]
    missing: list[str] = []

    for prefix in KEY_PREFIXES:
        ok = prefix_mounted(prefix, paths)
        status = "PASS" if ok else "FAIL"
        lines.append(f"{status}\t{prefix}")
        if not ok:
            missing.append(prefix)

    lines.extend(
        [
            "",
            f"summary: {len(KEY_PREFIXES) - len(missing)}/{len(KEY_PREFIXES)} prefixes mounted",
        ]
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if missing:
        print(f"FAIL: {len(missing)} missing prefix(es); see {OUTPUT}")
        for m in missing:
            print(f"  - {m}")
        return 1

    print(f"OK: all {len(KEY_PREFIXES)} admin smoke prefixes mounted.")
    print(f"Report: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
