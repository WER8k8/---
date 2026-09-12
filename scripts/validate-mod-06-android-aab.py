#!/usr/bin/env python3
"""MOD-06 · Android AAB 提审前置校验."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANDROID = ROOT / "frontend/admin/android"
REPORT = ROOT / "docs/mod-06-android-aab-prep-latest.json"


def main() -> int:
    gradlew = ANDROID / "gradlew.bat"
    main_activity = ANDROID / "app/src/main/java/com/youding/chuhaiji/MainActivity.java"
    build_gradle = ANDROID / "app/build.gradle"
    gradle_text = build_gradle.read_text(encoding="utf-8") if build_gradle.is_file() else ""
    app_id_ok = "com.youding.chuhaiji" in gradle_text
    version_ok = bool(re.search(r"versionCode\s+\d+", gradle_text))
    assets_index = ANDROID / "app/src/main/assets/public/index.html"

    checks = {
        "android_dir": ANDROID.is_dir(),
        "gradlew_bat": gradlew.is_file(),
        "main_activity": main_activity.is_file(),
        "application_id": app_id_ok,
        "version_code": version_ok,
        "synced_web_assets": assets_index.is_file(),
    }
    ok = all(checks.values())
    out = {
        "ok": ok,
        "task": "MOD-06-android-aab",
        "checks": checks,
        "aab_command": "cd frontend/admin/android && .\\gradlew.bat bundleRelease",
        "human_pending": "JDK+Android SDK 环境下执行 bundleRelease 产出 AAB",
    }
    REPORT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
