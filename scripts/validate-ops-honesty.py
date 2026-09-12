#!/usr/bin/env python3
"""运维诚实门禁：禁止假绿、假站会、假自动修。"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "ops" / "ops-honesty-latest.json"


def _load(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _parse_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def main() -> int:
    findings: list[dict] = []
    today = datetime.now().astimezone().strftime("%Y-%m-%d")

    daily = _load(ROOT / "docs/ops/expert-daily-latest.json") or {}
    standup = _load(ROOT / "docs/ops/expert-standup-latest.json") or {}
    remediate = _load(ROOT / "docs/ops/expert-auto-remediate-latest.json") or {}
    health = _load(ROOT / "docs/ops/daily-health-latest.json") or {}

    run_kind = daily.get("run_kind") or "unknown"
    if run_kind != "full_roster":
        findings.append(
            {
                "id": "no_full_roster_today",
                "severity": "P1",
                "message": f"今日无 full_roster 扫描（当前 run_kind={run_kind}），不得宣称 7 专家已巡检",
            }
        )
    if daily.get("day") != today:
        findings.append(
            {
                "id": "daily_stale",
                "severity": "P1",
                "message": f"expert-daily-latest 日期={daily.get('day')} 非今日 {today}",
            }
        )

    if remediate.get("auto_fixed") and not (
        (remediate.get("after_probe") or {}).get("backend_health")
        and (remediate.get("after_probe") or {}).get("admin_login")
    ):
        findings.append(
            {
                "id": "fake_auto_fixed",
                "severity": "P0",
                "message": "auto_fixed=true 但探针未全绿（假修复）",
            }
        )

    finished = _parse_iso(daily.get("finished_at"))
    if finished and (datetime.now(timezone.utc) - finished).total_seconds() > 86400 * 2:
        findings.append(
            {
                "id": "roster_too_old",
                "severity": "P1",
                "message": "全量扫描超过 48h 未更新",
            }
        )

    pre_p0 = [f for f in findings if f["severity"] == "P0"]
    pre_p1 = [f for f in findings if f["severity"] == "P1"]
    if standup.get("needs_owner") is False and (pre_p0 or pre_p1):
        findings.append(
            {
                "id": "standup_false_green",
                "severity": "P0",
                "message": "站会 needs_owner=false 但与诚实检查冲突（假绿）",
            }
        )

    # health-only must not pretend to be full roster
    if health.get("run_kind") == "health_only" and daily.get("run_kind") != "full_roster":
        pass  # expected; covered by no_full_roster

    p0 = [f for f in findings if f["severity"] == "P0"]
    p1 = [f for f in findings if f["severity"] == "P1"]
    report = {
        "ok": len(p0) == 0,
        "task": "ops-honesty-gate",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "p0_count": len(p0),
        "p1_count": len(p1),
        "findings": findings,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if p0 else (2 if p1 else 0)


if __name__ == "__main__":
    raise SystemExit(main())
