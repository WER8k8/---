# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""软著导出脚本 + 拓客 L1 链契约。"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from app.schemas.hermes_orchestration import IntentEvent, TaskNode
from app.services.hermes import planner_service as ps


def test_export_script_exists_and_excludes_secrets():
    script = Path(__file__).resolve().parents[2] / "scripts" / "export_clean_source_bundle.py"
    assert script.exists()
    spec = importlib.util.spec_from_file_location("export_clean", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert "_external" in mod.EXCLUDE_PARTS
    assert any("backend/app" in d for d in mod.INCLUDE_DIRS)
    assert ".venv" in mod.EXCLUDE_PARTS
    assert ".env" in mod.EXCLUDE_NAMES or any(".env" in s for s in mod.EXCLUDE_SUFFIX)


def test_find_leads_graph_still_has_human_approval():
    g = ps._outreach_graph("p", "e", {"keyword": "rockwool", "country": "SA"})
    assert "outreach.letter" in g.policies.approval_required
    executors = [n.executor for n in g.nodes]
    assert executors[0] == "lead"
    assert "billing" in executors


def test_fulfillment_n1_contract():
    g = ps._fulfillment_graph("p", "e", {"inquiry_id": "INQ-X", "name": "Ahmed", "message": "PI please", "country": "SA"})
    n1 = next(n for n in g.nodes if n.id == "n1")
    assert n1.input["name"] == "Ahmed"
    assert "PI" in n1.input["message"]
    assert n1.input.get("source_channel")


def test_research_graph_includes_deep_executors():
    g = ps._research_analysis_graph("p", "e", {"topic": "cement", "module": "acquisition"})
    execs = {n.executor for n in g.nodes}
    assert {"module_matrix", "commerce_ops", "platform_ops", "content_deep", "outreach_loop", "growth_probe", "agent_ops", "compliance_ops", "portal_ops", "data_ops"}.issubset(execs)


def test_dispatch_injection_keys_in_route_source():
    from app.api.v1.routes import acquisition as acq
    import inspect
    src = inspect.getsource(acq.acquisition_dispatch)
    assert "inquiry_id" in src
    assert "setdefault" in src
