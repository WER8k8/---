#!/usr/bin/env python3
"""QA · 七步⑤ staging 路由探针（ITER-03c / COMM-QA-02）。"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    ("backend/app/api/v1/routes/inquiry_channels.py", "/inquiries/channels"),
    ("backend/app/api/v1/routes/client.py", "wecom-push-config"),
    ("backend/app/api/v1/routes/social_interactions.py", "webhook/douyin"),
    ("backend/app/services/onboarding_progress_service.py", "build_onboarding_roadmap"),
    ("frontend/admin/src/components/tenant/OnboardingPlainRoadmap.vue", "onboarding-roadmap"),
    ("docs/qa-step5-inquiry-im-acceptance.md", "5b"),
    ("frontend/composables/useImRouting.ts", "im-routing/channels"),
]

SCREENSHOT_DIR = ROOT / "docs" / "mod-04-rehearsal" / "step5"
ROUND2_DIR = ROOT / "docs" / "出海计" / "screenshots" / "round2"
EXPECTED_SHOTS = ["5a-inbound-webhook.png", "5b-wecom-push.png", "5c-douyin-reply.png"]


def _https_domain_configured() -> bool:
    return bool(os.getenv("DEMO_HTTPS_DOMAIN", "").strip())


def main() -> int:
    missing = []
    for rel, needle in REQUIRED:
        path = ROOT / rel
        if not path.is_file():
            missing.append(f"missing:{rel}")
            continue
        if needle not in path.read_text(encoding="utf-8", errors="replace"):
            missing.append(f"snippet:{rel}:{needle}")

    screenshots = list(SCREENSHOT_DIR.glob("5*.png")) if SCREENSHOT_DIR.is_dir() else []
    round2 = list(ROUND2_DIR.glob("step5-*.png")) if ROUND2_DIR.is_dir() else []
    all_shots = screenshots + round2
    screenshots_ready = len(all_shots) >= 3

    blocked_by = []
    if not screenshots_ready:
        if not _https_domain_configured():
            blocked_by.append("O-1")
        blocked_by.append("O-2")

    routes_ok = len(missing) == 0
    status = "pass"
    if not routes_ok:
        status = "fail"
    elif not screenshots_ready:
        status = "blocked"

    out = {
        "task": "COMM-QA-02",
        "also": "ITER-03c",
        "status": status,
        "routes_ok": routes_ok,
        "screenshots_count": len(all_shots),
        "screenshots_ready": screenshots_ready,
        "expected_files": EXPECTED_SHOTS,
        "blocked_by": blocked_by if not screenshots_ready else [],
        "demo_https_domain_set": _https_domain_configured(),
        "missing": missing,
        "hint": "拍完后放入 docs/mod-04-rehearsal/step5/ 或 docs/出海计/screenshots/round2/",
        "out_of_scope": "无 HTTPS 域不得伪造截图",
    }
    latest = ROOT / "docs" / "qa-step5-staging-validation-latest.json"
    latest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(out, ensure_ascii=False, indent=2))

    if not routes_ok:
        return 1
    if not screenshots_ready:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
