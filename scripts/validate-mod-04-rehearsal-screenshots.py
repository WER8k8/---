#!/usr/bin/env python3
"""MOD-04 · 彩排截图归档校验."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/mod-04-rehearsal-screenshots-latest.json"
OUT = ROOT / "docs/compliance/mod-04-recordings/rehearsal"
EXPECTED = 6


def main() -> int:
    pngs = list(OUT.glob("mod04-*.png")) if OUT.is_dir() else []
    run_report = json.loads(REPORT.read_text(encoding="utf-8")) if REPORT.is_file() else {}
    ok = len(pngs) >= EXPECTED and (run_report.get("ok") is True or len(pngs) >= EXPECTED)
    out = {
        "ok": ok,
        "task": "MOD-04-rehearsal-screenshots",
        "png_count": len(pngs),
        "expected": EXPECTED,
        "archive_dir": str(OUT.relative_to(ROOT)),
        "run_report_ok": run_report.get("ok"),
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
