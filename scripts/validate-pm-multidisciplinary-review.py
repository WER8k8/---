#!/usr/bin/env python3
"""八角色联合旅程审查交付物门禁（PM-MKT-02）。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DOCS = [
    "docs/pm-multidisciplinary-journey-review.md",
    "docs/pm-marketing-journey-review-matrix.md",
]

REQUIRED_SNIPPETS = [
    ("backend/app/services/journey_health_service.py", "build_journey_health"),
    ("backend/app/services/journey_health_service.py", "role_insights"),
    ("backend/app/api/v1/routes/client.py", "/journey-health"),
    ("backend/app/services/client_today_service.py", "journey_health"),
    ("frontend/admin/src/views/client/dashboard.vue", "journey-health-panel"),
    ("frontend/admin/src/views/client/dashboard.vue", "journeyInsight"),
]


def main() -> int:
    missing: list[str] = []

    for rel in REQUIRED_DOCS:
        if not (ROOT / rel).is_file():
            missing.append(f"doc:{rel}")

    multi = ROOT / "docs" / "pm-multidisciplinary-journey-review.md"
    role_count = 0
    if multi.is_file():
        body = multi.read_text(encoding="utf-8", errors="replace")
        for role in ("产品经理", "营销", "策略", "市场调研", "用户研究", "数据分析", "UX", "UI"):
            if role in body:
                role_count += 1
        if role_count < 8:
            missing.append(f"roles_documented:{role_count}<8")

    for rel, needle in REQUIRED_SNIPPETS:
        path = ROOT / rel
        if not path.is_file():
            missing.append(f"code:{rel}")
            continue
        if needle not in path.read_text(encoding="utf-8", errors="replace"):
            missing.append(f"snippet:{rel}:{needle}")

    out = {
        "task": "PM-MKT-02",
        "ok": len(missing) == 0,
        "roles_documented": role_count,
        "missing": missing,
    }
    latest = ROOT / "docs" / "pm-multidisciplinary-validation-latest.json"
    latest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    if missing:
        print("PM-MKT-02 multidisciplinary FAIL")
        for m in missing:
            print(f"  - {m}")
        return 1
    print("PM-MKT-02 multidisciplinary PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
