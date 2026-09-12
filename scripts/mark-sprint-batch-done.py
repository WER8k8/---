#!/usr/bin/env python3
"""批量勾选一口气冲刺中已验收任务（仅改 JSON）。"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "docs" / "dev-sprint-all-in-one.json"

DONE_IDS = {
    "S0-01",
    "S0-02",
    "S0-03",
    "T-P0-03",
    "T-P0-04",
    "T-P0-06",
    "T-P0-09",
    "T-P0-10",
    "T-P0-11",
    "T-P0-14",
    "T-P0-15",
    "T-P0-16",
    "T-P0-17",
    "T-P0-18",
    "T-D2",
    "T-D3",
    "T-D4",
    "T-D5",
    "T-D6",
    "T-GEO-1",
    "T-GRAPHRAG",
    "T-STUB-1",
    "T-SEC-05",
    "T-SEC-PW",
    "T-SEC-03",
    "T-ENV-04",
    "T-OPS-07",
    "T-OPS-REDIS",
    "T-OPS-CRON",
    "T-UNIT",
    "T-FULL",
    "T-INT",
    "T-G1",
    "T-G2",
    "T-G6",
    "T-G7",
    "T-ROUND2",
    "AI-06",
    "T-P1-01",
    "T-P1-02",
    "T-P1-03",
    "T-P1-04",
    "T-P1-05",
    "T-P1-06",
    "T-P1-07",
    "T-P1-08",
    "T-P1-09",
    "T-P1-12",
    "T-P1-13",
    "T-P1-15",
    "T-OPS-BACKUP",
    "AI-05",
    "T-OPS-CELERY",
    "T-OPS-CRAWL",
    "T-PREFLIGHT",
    "T-P2-01",
    "T-P2-02",
    "T-P2-05",
    "T-P2-06",
    "T-P2-07",
    "T-NODE-1",
    "T-NODE-2",
    "T-ARCH-2",
    "T-ARCH-3",
    "T-AI-04",
    "T-NPM-AUDIT",
    "T-QA-06",
    "T-QA-08",
    "T-G3",
    "T-G4",
    "T-G5",
    "T-REV-3",
    "T-GONOGO",
    "T-NODE-3",
    "T-ARCH-1",
    "PM-01",
    "PM-02",
    "PM-03",
    "PM-04",
    "PM-05",
    "PM-06",
    "PM-07",
}


def main() -> None:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    n = 0
    for task in data.get("tasks", []):
        if task.get("id") in DONE_IDS and task.get("status") != "done":
            task["status"] = "done"
            n += 1
    data["updated_at"] = "2026-05-28-batch"
    JSON_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"marked {n} tasks done")


if __name__ == "__main__":
    main()
