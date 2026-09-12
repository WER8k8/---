#!/usr/bin/env python3
"""专家自治 CLI：自动修补 + 站会 + 通知 Owner。"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("YOUDING_REPO_ROOT", str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Expert autonomy cycle")
    parser.add_argument(
        "phase",
        choices=["remediate", "standup", "notify", "full"],
        nargs="?",
        default="full",
    )
    parser.add_argument("--no-notify", action="store_true")
    args = parser.parse_args()

    from app.services.ops_expert_autonomy_service import (
        auto_remediate,
        build_standup,
        notify_owner,
        run_full_cycle,
    )

    if args.phase == "full":
        out = run_full_cycle(notify=not args.no_notify)
    elif args.phase == "remediate":
        out = {"remediate": auto_remediate()}
    elif args.phase == "standup":
        rem = auto_remediate()
        out = {"standup": build_standup(remediate=rem)}
        if not args.no_notify:
            out["notification"] = notify_owner(standup=out["standup"])
    else:
        standup_path = ROOT / "docs/ops/expert-standup-latest.json"
        standup = json.loads(standup_path.read_text(encoding="utf-8")) if standup_path.is_file() else {}
        out = {"notification": notify_owner(standup=standup)}

    print(json.dumps(out, ensure_ascii=False, indent=2))
    standup = out.get("standup") or {}
    if standup.get("needs_owner"):
        return 2
    if out.get("remediate") and not out["remediate"].get("auto_fixed") and (out.get("standup") or {}).get("owner_review_count", 0) > 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
