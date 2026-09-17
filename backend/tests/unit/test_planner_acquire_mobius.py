# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Planner L1 获客模板 + 技能召回单元测试。

不依赖 DB / 真实执行器：用 monkeypatch 注入已注册执行器与能力集合。
验收：获客莫比乌斯标准图节点合法、外发人审齐全、意图路由不劫持。
"""
from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.schemas.hermes_orchestration import IntentEvent, TaskGraph
from app.services.hermes import planner_service as ps


# ── 夹具：伪造「全部已注册」执行器环境 ─────────────────────
REGISTERED = {
    "site_builder", "content", "deerflow", "publish", "nurture", "egress",
    "accio", "lead", "trade_ai_agent", "inquiry", "order", "goodjob_crm",
    "billing", "logistics",
}


@pytest.fixture()
def fake_registry(monkeypatch):
    monkeypatch.setattr(ps, "_registered_executors", lambda: set(REGISTERED))
    caps = set(ps.FALLBACK_CAPABILITIES)
    # 执行器真实声明并集（与生产 get_capabilities 一致的关键能力）
    caps.update({
        "lead.search", "lead.score",
        "prospect.enrich", "prospect.scrape",
        "outreach.letter", "outreach.whatsapp",
        "inbox.classify",
        "inquiry.capture",
        "order.create",
        "document.generate_pi", "document.generate_trade_docs", "crm.sync_stage",
        "billing.meter",
        "logistics.track",
        "site.generate", "content.create", "seo.optimize",
        "publish.multi", "nurture.create", "egress.assign",
        "research.deep_run", "default",
    })
    monkeypatch.setattr(ps, "known_capabilities", lambda: frozenset(caps))
    return monkeypatch


def _intent(intent: str, **payload: Any) -> IntentEvent:
    return IntentEvent(
        event_id="evt-test-001",
        tenant_id="t-test",
        channel="test",
        intent=intent,
        payload=payload,
    )


# ── L1 模板构建 ─────────────────────────────────────────────

def test_outreach_graph_full_chain(fake_registry):
    """智能拓客：找客→背调→评分→信(人审)→计量。"""
    g = ps._outreach_graph("p1", "e1", {"keyword": "rockwool", "country": "SA"})
    assert isinstance(g, TaskGraph)
    ids = [n.id for n in g.nodes]
    assert ids == ["n1", "n2", "n3", "n4", "n5"]
    caps = [n.capability for n in g.nodes]
    assert caps == [
        "lead.search", "prospect.enrich", "lead.score",
        "outreach.letter", "billing.meter",
    ]
    # 外发必须人审
    assert "outreach.letter" in g.policies.approval_required
    # 信节点依赖评分
    letter = next(n for n in g.nodes if n.id == "n4")
    assert letter.depends_on == ["n3"]
    assert ps.validate_graph(g) == []


def test_fulfillment_graph_covers_order_to_logistics(fake_registry):
    """履约：询盘→订单→PI→定金→CRM→单证→物流→尾款。"""
    g = ps._fulfillment_graph("p2", "e2", {"message": "inquiry from SA", "incoterms": "CIF"})
    caps = [n.capability for n in g.nodes]
    assert caps[0] == "inquiry.capture"
    assert "order.create" in caps
    assert "document.generate_pi" in caps
    assert "document.generate_trade_docs" in caps
    assert "logistics.track" in caps
    # 定金与尾款两次 meter
    meters = [n for n in g.nodes if n.capability == "billing.meter"]
    assert len(meters) == 2
    # PI / 订单需人审
    assert "document.generate_pi" in g.policies.approval_required
    assert "order.create" in g.policies.approval_required
    # 物流在单证之后
    idx_docs = caps.index("document.generate_trade_docs")
    idx_log = caps.index("logistics.track")
    assert idx_log > idx_docs
    assert ps.validate_graph(g) == []


def test_social_outreach_requires_approval(fake_registry):
    """社媒WA：外发必须人审。"""
    g = ps._social_outreach_graph("p3", "e3", {"keyword": "gypsum", "country": "EG"})
    assert "outreach.whatsapp" in g.policies.approval_required
    caps = [n.capability for n in g.nodes]
    assert "prospect.scrape" in caps
    assert "inbox.classify" in caps
    assert ps.validate_graph(g) == []


def test_inquiry_convert_graph(fake_registry):
    """询盘转化：捕获→背调→回复草稿(人审)。"""
    g = ps._inquiry_convert_graph("p4", "e4", {"message": "need rockwool CIF Jeddah"})
    caps = [n.capability for n in g.nodes]
    assert caps[0] == "inquiry.capture"
    assert "outreach.letter" in g.policies.approval_required
    assert ps.validate_graph(g) == []


def test_site_launch_graph_approvals(fake_registry):
    g = ps._site_launch_graph("p5", "e5", {"product_name": "rockwool"})
    assert "publish.multi" in g.policies.approval_required
    assert "outreach.letter" in g.policies.approval_required
    assert ps.validate_graph(g) == []


# ── 意图路由（防 payload 劫持）──────────────────────────────

def test_match_template_by_structured_intent(fake_registry):
    """intent 字段优先：fulfillment 不应被 payload 里的「拓客」劫持。"""
    ev = _intent("fulfillment", message="随便拓客开发信")
    builder = ps._match_template(ev)
    assert builder is ps._fulfillment_graph

    ev2 = _intent("find_leads", keyword="rockwool")
    assert ps._match_template(ev2) is ps._outreach_graph

    ev3 = _intent("generate_site", product_name="panel")
    assert ps._match_template(ev3) is ps._site_launch_graph


def test_match_template_whatsapp_intent(fake_registry):
    ev = _intent("whatsapp_outreach", keyword="insulation")
    # intent 含 whatsapp 关键词
    ev.payload = {"keyword": "insulation"}
    ev2 = IntentEvent(
        event_id="e", tenant_id="t", channel="web",
        intent="whatsapp", payload={"keyword": "x"},
    )
    assert ps._match_template(ev2) is ps._social_outreach_graph


# ── decompose 主链 ─────────────────────────────────────────

def test_decompose_l1_template_with_skills(fake_registry, tmp_path):
    """命中 L1 + 有技能召回 → L1_hybrid；无技能 → L1_template。"""
    async def _run():
        ev = _intent("find_leads", keyword="rockwool", country="SA")
        with patch.object(ps, "_recall_skills", return_value=[]), \
             patch.object(ps, "_enrich_with_experience", side_effect=lambda e, d: dict(e.payload or {})):
            graph, source = await ps.decompose(ev, MagicMock())
        assert source == "L1_template"
        assert graph.plan_id
        assert "outreach.letter" in graph.policies.approval_required

        ev2 = _intent("find_leads", keyword="rockwool", country="SA")
        with patch.object(ps, "_recall_skills", return_value=[{"name": "prospecting", "score": 9, "description": "x", "version": "1"}]):
            def _enrich_sync(e, d):
                e.payload = dict(e.payload or {})
                e.payload["_skill_refs"] = [{"name": "prospecting", "score": 9, "description": "x", "version": "1"}]
                return e.payload
            with patch.object(ps, "_enrich_with_experience", side_effect=_enrich_sync):
                graph2, source2 = await ps.decompose(ev2, MagicMock())
        # 契约：命中 L1 模板统一返回 L1_template；技能在 payload._skill_refs
        assert source2 == "L1_template"
        assert graph2.nodes

    asyncio.get_event_loop_policy().new_event_loop().run_until_complete(_run())


def test_decompose_fulfillment_intent(fake_registry):
    async def _run():
        ev = _intent("fulfillment", message="PI for order", order_id="o1")
        with patch.object(ps, "_recall_skills", return_value=[]), \
             patch.object(ps, "_enrich_with_experience", side_effect=lambda e, d: dict(e.payload or {})):
            graph, source = await ps.decompose(ev, MagicMock())
        assert source in ("L1_template", "L1_hybrid")
        assert any(n.capability == "document.generate_pi" for n in graph.nodes)

    asyncio.get_event_loop_policy().new_event_loop().run_until_complete(_run())


def test_l3_minimal_when_no_template(fake_registry):
    """无模板且 L2 失败 → L3 最小图。"""
    async def _run():
        ev = _intent("totally_unknown_intent_xyz", foo="bar")
        with patch.object(ps, "_recall_skills", return_value=[]), \
             patch.object(ps, "_enrich_with_experience", side_effect=lambda e, d: dict(e.payload or {})), \
             patch.object(ps, "_llm_decompose", return_value=None):
            graph, source = await ps.decompose(ev, MagicMock())
        assert source == "L3_minimal"
        assert len(graph.nodes) == 1
        assert graph.nodes[0].executor == "deerflow"

    asyncio.get_event_loop_policy().new_event_loop().run_until_complete(_run())


# ── L2 强制人审 ─────────────────────────────────────────────

def test_llm_decompose_forces_approval_on_outreach(fake_registry):
    """LLM 出图若漏 approval，外发能力必须被强制补上。"""
    async def _run():
        ev = _intent("find something", message="need buyers")
        mock_result = {
            "content": '{"nodes":[{"id":"n1","executor":"accio","capability":"outreach.letter","depends_on":[],"input":{},"on_fail":"skip"}]}'
        }
        mock_gw = MagicMock()
        mock_gw.generate = MagicMock(return_value=mock_result)

        class _FakeGW:
            def __init__(self):
                pass
            async def generate(self, *a, **k):
                return mock_result

        with patch.object(ps, "_recall_skills", return_value=[]), \
             patch("app.services.model_gateway.ModelGateway", _FakeGW):
            graph = await ps._llm_decompose(ev, MagicMock())
        assert graph is not None
        assert "outreach.letter" in graph.policies.approval_required

    asyncio.get_event_loop_policy().new_event_loop().run_until_complete(_run())


# ── 安全阀 ─────────────────────────────────────────────────

def test_validate_graph_rejects_unknown_executor(fake_registry):
    g = ps._outreach_graph("p", "e", {"keyword": "x"})
    g.nodes[0].executor = "not_a_real_executor"
    problems = ps.validate_graph(g)
    assert any("未注册" in p for p in problems)


def test_validate_graph_rejects_unknown_capability(fake_registry):
    g = ps._outreach_graph("p", "e", {"keyword": "x"})
    g.nodes[1].capability = "no.such.cap"
    problems = ps.validate_graph(g)
    assert any("白名单" in p for p in problems)


# ── 技能召回 ────────────────────────────────────────────────

def test_recall_skills_empty_on_error():
    with patch("app.services.registry.skill_pack_loader.match_skill_pack", side_effect=RuntimeError("no disk")):
        assert ps._recall_skills("anything") == []


def test_recall_skills_returns_topk():
    fake_entry = MagicMock()
    fake_entry.name = "cold-email"
    fake_entry.version = "2.0.0"
    fake_entry.description = "B2B cold emails"
    with patch("app.services.registry.skill_pack_loader.match_skill_pack", return_value=[(fake_entry, 40)]):
        out = ps._recall_skills("cold email outreach", top_k=3)
    assert out and out[0]["name"] == "cold-email"
    assert out[0]["score"] == 40
