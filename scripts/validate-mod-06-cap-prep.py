#!/usr/bin/env python3
"""MOD-06 · 读取 cap-sync-prep 构建报告."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/mod-06-cap-prep-validation-latest.json"
PREP = ROOT / "docs/mod-06-cap-sync-prep-latest.json"
PKG = ROOT / "frontend/admin/package.json"


def main() -> int:
    prep_ok = False
    if PREP.is_file():
        prep_ok = bool(json.loads(PREP.read_text(encoding="utf-8-sig")).get("pass"))
    pkg = json.loads(PKG.read_text(encoding="utf-8-sig"))
    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    cap_installed = "@capacitor/core" in deps
    android_dir = (ROOT / "frontend/admin/android").is_dir()
    ok = prep_ok and cap_installed and android_dir
    out = {
        "ok": ok,
        "task": "MOD-06-cap-prep",
        "build_prep_pass": prep_ok,
        "capacitor_in_package_json": cap_installed,
        "android_dir": android_dir,
    }
    REPORT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
