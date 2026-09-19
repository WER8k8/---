# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""GP-A/B 黄金路径 API 与 TradeAI 技能白名单 · Compose annex-domain-merge."""
from __future__ import annotations

import uuid

import pytest

from app.schemas.hermes_orchestration import IntentEvent
from app.services.hermes import planner_service
from app.services.hermes.annex_work_mode import (
    golden_path_for_executors,
    preferred_decompose_source,
    work_mode_report,
)


def test_tradeai_skill_capabilities_in_fallback_whitelist():
    caps = planner_service.FALLBACK_CAPABILITIES
    for name in (
        "trade_ai.social_scraper",
        "trade_ai.auto_sender",
        "trade_ai.ai_reply",
        "skill.social_scraper",
    ):
        assert name in caps, name


@pytest.mark.asyncio
async def test_gp_a_api_intent_anchor_resolves_l1():
    event = IntentEvent(
        event_id=str(uuid.uuid4()),
        tenant_id="t-gp-a-api",
        channel="api",
        intent="履约推进与形式发票 履约 fulfillment PI 订单跟单",
        payload={"message": "订单履约 PI", "order_id": "", "inquiry_id": ""},
    )
    graph, source = await planner_service.decompose(event, db=None)
    assert source == "L1_template"
    ex = {n.executor for n in graph.nodes}
    assert "goodjob_crm" in ex
    gp = golden_path_for_executors(ex)
    assert gp and gp["id"] == "GP-A"
    assert preferred_decompose_source("履约 PI") == "L1_template"


@pytest.mark.asyncio
async def test_gp_b_outreach_still_l1_trade_ai():
    event = IntentEvent(
        event_id=str(uuid.uuid4()),
        tenant_id="t-gp-b-api",
        channel="api",
        intent="社媒拓客 WhatsApp 私域触达 prospect social_outreach",
        payload={"keywords": ["tiles"]},
    )
    graph, source = await planner_service.decompose(event, db=None)
    assert source == "L1_template"
    assert "trade_ai_agent" in {n.executor for n in graph.nodes}


def test_work_mode_reports_composite_and_no_privilege():
    report = work_mode_report()
    assert report["default_task_source"] == "L1_template"
    assert report["dsh_required_every_task"] is False
    domains = report["seamless_body"]["function_domains"]
    assert all(d["privileged"] is False for d in domains)
    # 复合航道能力集：拓客 + 履约 执行器并存时覆盖 GP-A
    mixed = {"trade_ai_agent", "inquiry", "order", "goodjob_crm", "billing"}
    gp = golden_path_for_executors(mixed)
    assert gp["id"] == "GP-A"


def test_orchestration_router_exposes_golden_paths():
    from app.api.v1.routes import orchestration as orch

    paths = []
    for r in orch.router.routes:
        p = getattr(r, "path", "")
        if p:
            paths.append(p)
    assert any("golden-path/fulfillment" in p for p in paths)
    assert any("golden-path/outreach" in p for p in paths)
    assert any("golden-path/work-mode" in p for p in paths)
