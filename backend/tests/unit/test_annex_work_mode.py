# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""附属工作模式契约 + 黄金路径 GP-A/B（Hermes 默认 L1 · 双平面）."""
from __future__ import annotations

import uuid

import pytest

from app.schemas.hermes_orchestration import IntentEvent
from app.services.hermes import planner_service
from app.services.hermes.annex_work_mode import (
    GOLDEN_PATH_A,
    GOLDEN_PATH_B,
    PLANE_INTERACTIVE,
    PLANE_TASK,
    SEAMLESS_BODY,
    classify_plane,
    golden_path_for_executors,
    preferred_decompose_source,
    seamless_gap_score,
    work_mode_report,
)


def test_dual_plane_classification():
    assert classify_plane("查看客户列表") == PLANE_INTERACTIVE
    assert classify_plane("list orders") == PLANE_INTERACTIVE
    assert classify_plane("生成形式发票 PI") == PLANE_TASK
    assert classify_plane("外贸履约跟单") == PLANE_TASK
    assert classify_plane("社媒拓客 WhatsApp 触达") == PLANE_TASK


def test_task_plane_defaults_to_l1_not_dsh():
    assert preferred_decompose_source("履约 PI") == "L1_template"
    assert preferred_decompose_source("拓客") == "L1_template"
    assert preferred_decompose_source("查看列表") == "n/a_interactive"
    report = work_mode_report()
    assert report["dsh_required_every_task"] is False
    assert report["default_task_source"] == "L1_template"


def test_layer_stack_places_annex_under_hermes():
    report = work_mode_report()
    layers = [x["layer"] for x in report["layer_stack"]]
    assert layers.index("dsh_optional") < layers.index("hermes")
    assert layers.index("hermes") < layers.index("executors_parallel")
    assert set(report["annex_executors"]) == {"trade_ai_agent", "goodjob_crm"}


def test_golden_path_coverage_helper():
    gp = golden_path_for_executors(["inquiry", "order", "goodjob_crm", "billing", "media"])
    assert gp and gp["id"] == GOLDEN_PATH_A["id"]
    gp_b = golden_path_for_executors(["trade_ai_agent", "lead"])
    assert gp_b and gp_b["id"] == GOLDEN_PATH_B["id"]
    assert golden_path_for_executors(["deerflow"]) is None


@pytest.mark.asyncio
async def test_gp_a_fulfillment_resolves_l1_with_goodjob():
    """GP-A：履约意图应走 L1 模板，且含 goodjob_crm 节点（不经 DSH 必经叙事）。"""
    event = IntentEvent(
        event_id=str(uuid.uuid4()),
        tenant_id="t-gp-a",
        channel="web",
        intent="fulfillment",
        payload={
            "message": "履约：客户要 PI，订单跟单发货",
            "name": "GP-A Buyer",
            "product": "EPS board",
            "order_id": "",
            "inquiry_id": "",
        },
    )
    graph, source = await planner_service.decompose(event, db=None)
    assert source == "L1_template"
    executors = {n.executor for n in graph.nodes}
    assert "goodjob_crm" in executors
    caps = {n.capability for n in graph.nodes}
    assert "document.generate_pi" in caps
    gp = golden_path_for_executors(executors)
    assert gp is not None and gp["id"] == "GP-A"


@pytest.mark.asyncio
async def test_gp_b_social_outreach_resolves_l1_trade_ai():
    event = IntentEvent(
        event_id=str(uuid.uuid4()),
        tenant_id="t-gp-b",
        channel="web",
        intent="social_outreach",
        payload={"message": "社交媒体拓客 WhatsApp 私域触达", "keywords": ["tiles"]},
    )
    graph, source = await planner_service.decompose(event, db=None)
    assert source == "L1_template"
    executors = {n.executor for n in graph.nodes}
    assert executors == {"trade_ai_agent"} or "trade_ai_agent" in executors
    gp = golden_path_for_executors(executors)
    assert gp is not None and gp["id"] == "GP-B"


def test_seamless_body_standards_present():
    report = work_mode_report()
    assert "seamless_body" in report
    ids = {s["id"] for s in SEAMLESS_BODY["standards"]}
    assert ids >= {"S1", "S2", "S3", "S4", "S5", "S6", "S7"}
    score = seamless_gap_score({s: True for s in ids})
    assert score["seamless"] is True and score["passed"] == len(ids)
    partial = seamless_gap_score({"S1": True, "S2": True})
    assert partial["seamless"] is False and partial["passed"] == 2
