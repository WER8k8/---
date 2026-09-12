#!/usr/bin/env python3
"""DOC-02 / PM-07 · 周报摘要自动生成"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    s0 = load_json(ROOT / "docs" / "pm-gate-s0-signoff.json")
    comp = load_json(ROOT / "docs" / "compliance" / "comp-02-rz-validation.json")
    rehe = load_json(ROOT / "docs" / "pm-rehearsal-v2-check-latest.json")
    ip = load_json(ROOT / "docs" / "compliance" / "ip-04-weekly-scan-latest.json")

    lines = [
        f"# ECC 周报 · {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        "",
        "## Gate-S0",
        f"- automated items pass: {all(i.get('pass') for i in s0.get('items', [])) if s0 else 'n/a'}",
        f"- cert PNG: {s0.get('automated_checks', {}).get('cert_png_count', 0)}",
        "",
        "## COMP-02",
        f"- 60 pages valid: {comp.get('page_count') == 60 if comp else 'n/a'}",
        "",
        "## PM-03 彩排",
        f"- ready: {rehe.get('ready_for_rehearsal', False)}",
        "",
        "## IP-04",
        f"- risk: {ip.get('risk_level', 'n/a')}",
        "",
        "## Owner 阻塞",
        "- PM-06 Brand/Trial/窗口",
        "",
    ]
    out = ROOT / "docs" / "ecc-weekly-report-latest.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
