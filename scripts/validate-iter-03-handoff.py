#!/usr/bin/env python3
"""ITER-03 PM 交付物存在性门禁 — 文档与 API 路由探针。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DOCS = [
    "docs/iter-03-onboarding-sales-channel.md",
    "docs/pm-multidisciplinary-journey-review.md",
    "docs/pm-owner-blockers-20260604.md",
    "docs/qa-step5-inquiry-im-acceptance.md",
    "docs/pm-r1-closeout-checklist.md",
    "docs/guides/customer-wecom-push-5min.md",
    "docs/guides/agent-onboarding-roadmap-onepage.md",
    "docs/compliance/MOD-02-im-prod-handoff-checklist.md",
    "docs/mod-04-rehearsal/step5/README.md",
]

REQUIRED_ROUTE_SNIPPETS = [
    ("backend/app/api/v1/routes/client.py", "wecom-push-config"),
    ("backend/app/api/v1/routes/client.py", "onboarding-guides"),
    ("backend/app/api/v1/routes/client.py", "douyin-comments/pull"),
    ("backend/app/api/v1/routes/client.py", "sales-channel-rehearsal/inbound"),
    ("backend/app/services/sales_channel_rehearsal_service.py", "run_inbound_rehearsal"),
    ("backend/app/api/v1/routes/social_interactions.py", "webhook/douyin"),
    ("backend/app/services/onboarding_progress_service.py", "build_onboarding_roadmap"),
    ("backend/app/services/douyin_comment_pull_service.py", "pull_and_ingest_for_tenant"),
    ("frontend/admin/src/views/client/dashboard.vue", "onboarding-guides"),
    ("backend/app/services/journey_health_service.py", "build_journey_health"),
    ("backend/app/api/v1/routes/client.py", "/journey-health"),
    ("frontend/admin/src/views/client/dashboard.vue", "journey-health-panel"),
]


def main() -> int:
    missing: list[str] = []
    for rel in REQUIRED_DOCS:
        if not (ROOT / rel).is_file():
            missing.append(f"doc:{rel}")

    for rel, needle in REQUIRED_ROUTE_SNIPPETS:
        path = ROOT / rel
        if not path.is_file():
            missing.append(f"code:{rel}")
            continue
        if needle not in path.read_text(encoding="utf-8", errors="replace"):
            missing.append(f"snippet:{rel}:{needle}")

    out = {
        "task": "ITER-03",
        "ok": len(missing) == 0,
        "required_docs": len(REQUIRED_DOCS),
        "missing": missing,
    }
    latest = ROOT / "docs" / "iter-03-handoff-validation-latest.json"
    latest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    if missing:
        print("ITER-03 handoff FAIL")
        for m in missing:
            print(f"  - {m}")
        return 1
    print("ITER-03 handoff PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
