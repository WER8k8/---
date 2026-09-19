# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""SEAM-P0 Hermes 任务中心契约."""
from __future__ import annotations

from pathlib import Path

WT = Path(__file__).resolve().parents[3]
ADMIN = WT / "frontend" / "admin" / "src"


def test_orchestration_exposes_hermes_task_center_routes():
    from app.api.v1.routes import orchestration as orch

    paths = [getattr(r, "path", "") for r in orch.router.routes]
    assert any(p.endswith("/hermes/tasks") or p == "/hermes/tasks" for p in paths)
    assert any("/hermes/tasks/{plan_id}" in p for p in paths)


def test_plan_summary_reads_golden_path_and_graph_source():
    from types import SimpleNamespace

    from app.api.v1.routes.orchestration import _hermes_plan_summary
    import json
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    task = SimpleNamespace(
        id="plan-1",
        task_type="hermes_plan",
        status="executing",
        priority=5,
        error_message=None,
        source="orchestration_api",
        created_at=now,
        started_at=now,
        finished_at=None,
        input_json=json.dumps(
            {
                "graph_source": "L1_template",
                "intent": "履约 PI",
                "context": {"golden_path": "GP-A", "plane": "task"},
            }
        ),
    )
    s = _hermes_plan_summary(task, child_count=3, node_statuses=["done", "executing", "created"])
    assert s["plan_id"] == "plan-1"
    assert s["golden_path"] == "GP-A"
    assert s["graph_source"] == "L1_template"
    assert s["child_count"] == 3
    assert s["plane"] == "task"


def test_frontend_task_center_and_menu():
    page = (ADMIN / "views/client/hermes-tasks.vue").read_text(encoding="utf-8", errors="ignore")
    assert "listHermesTasks" in page
    assert "getHermesTaskDetail" in page
    menus = (ADMIN / "constants/proShellMenus.ts").read_text(encoding="utf-8", errors="ignore")
    assert "Hermes 任务" in menus
    assert "/client/tasks" in menus
    router = (ADMIN / "router/index.ts").read_text(encoding="utf-8", errors="ignore")
    assert "ClientHermesTasks" in router
    ful = (ADMIN / "views/client/queues/fulfillment.vue").read_text(encoding="utf-8", errors="ignore")
    assert "/client/tasks" in ful
    assert "golden-path/fulfillment" in ful
