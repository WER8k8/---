#!/usr/bin/env python3
"""合并产业带调研 deliverable → industry_belt_hebei_insulation.json（PM 审核后运行）。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BELT_PATH = ROOT / "backend" / "app" / "data" / "industry_belt_hebei_insulation.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def merge_survey(belt_data: dict, survey: dict, *, belt_id: str = "langfang_dacheng_insulation") -> dict:
    if survey.get("pm_review", {}).get("status") != "approved":
        status = survey.get("pm_review", {}).get("status") or "pending"
        raise SystemExit(
            f"调研包 {survey.get('survey_id')} 未 PM 审核通过 "
            f"(pm_review.status={status!r}，须为 approved)，拒绝合并。"
            " 联网初稿请先实地复核。"
        )

    target = next((b for b in belt_data.get("belts", []) if b.get("id") == belt_id), None)
    if not target:
        raise SystemExit(f"产业带 {belt_id} 不存在于 {BELT_PATH}")

    cats = target.setdefault("product_categories", {})
    typical: list[str] = list(target.get("typical_products") or [])
    added = 0

    for block in survey.get("categories") or []:
        cid = block.get("category_id") or "misc"
        names = cats.setdefault(cid, [])
        existing = set(names)
        for prod in block.get("products") or []:
            name = str(prod.get("name") or "").strip()
            if not name or name in existing:
                continue
            names.append(name)
            existing.add(name)
            added += 1
            if len(typical) < 20 and name not in typical:
                typical.append(name)

    target["typical_products"] = typical
    target["last_survey_merge"] = {
        "survey_id": survey.get("survey_id"),
        "survey_date": survey.get("survey_date"),
        "surveyor": survey.get("surveyor"),
        "products_added": added,
    }
    belt_data["last_survey_merge"] = target["last_survey_merge"]
    return belt_data


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge industry belt survey JSON into belt catalog")
    parser.add_argument("survey_json", type=Path, help="Path to approved survey deliverable")
    parser.add_argument("--belt-id", default="langfang_dacheng_insulation")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not BELT_PATH.is_file():
        print(f"Missing belt file: {BELT_PATH}", file=sys.stderr)
        return 1
    if not args.survey_json.is_file():
        print(f"Missing survey: {args.survey_json}", file=sys.stderr)
        return 1

    belt_data = _load_json(BELT_PATH)
    survey = _load_json(args.survey_json)
    merged = merge_survey(belt_data, survey, belt_id=args.belt_id)

    if args.dry_run:
        print(json.dumps(merged.get("belts", [{}])[0].get("last_survey_merge"), ensure_ascii=False, indent=2))
        return 0

    BELT_PATH.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Merged into {BELT_PATH} (+{merged['belts'][0]['last_survey_merge']['products_added']} products)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
