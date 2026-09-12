#!/usr/bin/env python3
"""GW-P-GSC-02 · GSC/Ads webhook 单测门禁。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / "backend" / ".venv" / "Scripts" / "python.exe"
if not PY.is_file():
    PY = Path(sys.executable)


def main() -> int:
    proc = subprocess.run(
        [str(PY), "-m", "pytest", "tests/unit/test_gsc_ads_attribution_webhook.py", "-q"],
        cwd=ROOT / "backend",
        capture_output=True,
        text=True,
    )
    print(proc.stdout + proc.stderr)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
