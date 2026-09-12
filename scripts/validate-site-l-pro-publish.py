#!/usr/bin/env python3
"""SITE-DESIGN-01 · L-Pro 发布门禁（契约 + 可选 site_content 实校验）。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / ".project" / "site-design-target.json"
PIPELINE = ROOT / "backend" / "app" / "data" / "hermes_site_builder_pipeline.json"
REPORT = ROOT / "docs" / "site-l-pro-publish-gate-latest.json"


def _contract_issues() -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not CONTRACT.is_file():
        issues.append({"severity": "P0", "check": "contract", "detail": "missing .project/site-design-target.json"})
        return issues

    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if data.get("target_model", {}).get("id") != "L-Pro":
        issues.append({"severity": "P0", "check": "target_model", "detail": "target_model.id must be L-Pro"})
    pages = {p.get("path") for p in data.get("page_map", [])}
    required = {"/", "/about", "/products", "/solutions", "/downloads", "/contact"}
    missing = sorted(required - pages)
    if missing:
        issues.append(
            {
                "severity": "P0",
                "check": "page_map",
                "detail": f"missing paths: {', '.join(missing)}",
            }
        )

    if not PIPELINE.is_file():
        issues.append({"severity": "P0", "check": "pipeline", "detail": "missing hermes_site_builder_pipeline.json"})
    else:
        pipe = json.loads(PIPELINE.read_text(encoding="utf-8"))
        lessons = pipe.get("reference_lessons") or {}
        if "ydalison.com" not in lessons or "t-global.com" not in lessons:
            issues.append(
                {
                    "severity": "P1",
                    "check": "reference_lessons",
                    "detail": "pipeline must include ydalison.com and t-global.com positive targets",
                }
            )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate L-Pro publish gate")
    parser.add_argument(
        "--site-content",
        type=Path,
        help="JSON file with site_content object or { site_content: ... }",
    )
    parser.add_argument(
        "--environment",
        default="development",
        help="development | production (affects placeholder checks)",
    )
    args = parser.parse_args()

    issues = _contract_issues()

    site_gate: dict | None = None
    if args.site_content:
        if not args.site_content.is_file():
            issues.append(
                {
                    "severity": "P0",
                    "check": "site_content_file",
                    "detail": f"not found: {args.site_content}",
                }
            )
        else:
            raw = json.loads(args.site_content.read_text(encoding="utf-8"))
            site_content = raw.get("site_content") if isinstance(raw, dict) and "site_content" in raw else raw
            from app.services.site_l_pro_service import validate_l_pro_publish_gate

            site_gate = validate_l_pro_publish_gate(site_content, environment=args.environment)
            for item in site_gate.get("issues") or []:
                if isinstance(item, dict):
                    issues.append(item)

    p0 = [i for i in issues if i.get("severity") == "P0"]
    p1 = [i for i in issues if i.get("severity") == "P1"]
    ok = len(p0) == 0

    REPORT.write_text(
        json.dumps(
            {
                "ok": ok,
                "p0": len(p0),
                "p1": len(p1),
                "issues": issues,
                "site_content_gate": site_gate,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    for item in issues:
        print(f"[{item['severity']}] {item['check']}: {item['detail']}")

    if p0:
        print(f"FAIL P0={len(p0)} — see {REPORT}")
        return 1
    print(f"PASS — see {REPORT}")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "backend"))
    sys.exit(main())
