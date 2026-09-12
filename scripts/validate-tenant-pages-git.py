#!/usr/bin/env python3
"""Tenant Nuxt pages — disk vs git tracking gate (换机/送检不得丢页)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TENANT_PAGES = ROOT / "frontend" / "pages" / "tenant"

REQUIRED = [
    "frontend/pages/tenant/index.vue",
    "frontend/pages/tenant/about.vue",
    "frontend/pages/tenant/contact.vue",
    "frontend/pages/tenant/solutions.vue",
    "frontend/pages/tenant/downloads.vue",
    "frontend/pages/tenant/products/index.vue",
    "frontend/pages/tenant/products/[slug].vue",
]

OBSOLETE = [
    "frontend/pages/tenant/products.vue",
]


def main() -> int:
    errors: list[str] = []

    for rel in REQUIRED:
        path = ROOT / rel.replace("/", "\\") if "\\" in str(ROOT) else ROOT / rel
        if not path.is_file():
            errors.append(f"missing on disk: {rel}")

    tracked = subprocess.check_output(
        ["git", "ls-files", "frontend/pages/tenant"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).strip().splitlines()
    tracked_set = set(tracked)

    for rel in REQUIRED:
        norm = rel.replace("\\", "/")
        if norm not in tracked_set:
            errors.append(f"not tracked in git: {norm}")

    for rel in OBSOLETE:
        norm = rel.replace("\\", "/")
        if norm in tracked_set:
            errors.append(f"obsolete file still in git (remove): {norm}")

    if errors:
        print("FAIL validate-tenant-pages-git")
        for e in errors:
            print(" -", e)
        return 1

    print(f"OK tenant pages git ({len(REQUIRED)} required, tracked={len(tracked_set)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
