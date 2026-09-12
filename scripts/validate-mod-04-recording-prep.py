#!/usr/bin/env python3
"""MOD-04 · 七步录屏前置（清单 + 归档目录）校验."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/mod-04-recording-prep-latest.json"
CHECKLIST = ROOT / "docs/compliance/MOD-04-seven-step-recording-checklist.md"
ARCHIVE = ROOT / "docs/compliance/mod-04-recordings"
STEPS = 7


def main() -> int:
    existing = list(ARCHIVE.glob("*")) if ARCHIVE.is_dir() else []
    recordings = [p.name for p in existing if p.suffix.lower() in {".mp4", ".webm", ".txt", ".md"}]
    checklist_text = CHECKLIST.read_text(encoding="utf-8") if CHECKLIST.is_file() else ""
    step_rows = sum(1 for i in range(1, STEPS + 1) if f"| {i} |" in checklist_text)

    checks = {
        "checklist_md": CHECKLIST.is_file(),
        "archive_dir": ARCHIVE.is_dir(),
        "archive_readme": (ARCHIVE / "README.md").is_file(),
        "seven_steps_in_checklist": step_rows >= STEPS,
    }
    ok = all(checks.values())
    report = {
        "ok": ok,
        "task": "MOD-04-prep",
        "checks": checks,
        "recordings_present": recordings,
        "human_pending": "HTTPS 域就绪后按清单录屏",
        "archive_path": str(ARCHIVE.relative_to(ROOT)),
    }
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
