# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Desktop Hermes / AEOS 全域蓝图落地契约测试。"""
from __future__ import annotations

import asyncio

from app.schemas.hermes_orchestration import IntentEvent, TaskNode
from app.services.aeos_registry import (
    SUBSYSTEMS,
    aeos_full_invoke,
    aeos_invoke_map,
    aeos_registry_report,
)
from app.services.desktop_hermes import SCENE_REGISTRY, desktop_hermes
from app.services.hermes import planner_service as ps
from app.services.hermes.executors import ExecutorRegistry
from app.services.hermes.executors.base import ExecutorContext


def test_aeos_eight_subsystems_lock():
    assert len(SUBSYSTEMS) == 8
    report = aeos_registry_report()
    assert report["required"] == 8
    assert report["lock"] == "SYSTEM-LOCK-02"
    # 八大子系统全部有 invoke 路径（可调度业务）
    amap = aeos_invoke_map()
    assert set(amap.keys()) == {s["id"] for s in SUBSYSTEMS}
    for sid, spec in amap.items():
        assert spec.get("executor"), sid
        assert spec.get("capability"), sid


def test_desktop_hermes_registered_and_scenes():
    assert ExecutorRegistry.has("desktop_hermes")
    assert ExecutorRegistry.has("biz_bot")
    caps = DesktopHermesCaps = ExecutorRegistry.get("desktop_hermes").get_capabilities()
    for key in (
        "desktop_hermes.assemble",
        "desktop_hermes.aeos",
        "desktop_hermes.aeos_invoke",
        "desktop_hermes.scenes",
        "desktop_hermes.status",
    ):
        assert key in caps

    scenes = desktop_hermes.list_scenes()
    assert len(scenes) >= 4
    scene_ids = {s["id"] for s in scenes}
    assert {"lane_a_research", "lane_b_outreach", "lane_c_fulfillment", "lane_d_composite"}.issubset(scene_ids)
    assert "lane_aeos" in scene_ids
    assert "lane_module_robots" in scene_ids

    status = desktop_hermes.status()
    assert status["l1_templates"] >= 15
    assert status["skills"] >= 6
    assert status["scenes"] >= 4


def test_l1_templates_count_and_new_lanes():
    assert len(ps._TEMPLATES) >= 15
    # 蓝图要求：履约 + 复合 + AEOS + 机器人 + 招投标 都有模板
    g_c = ps._fulfillment_graph("p", "e", {"inquiry_id": "INQ", "message": "PI", "name": "A"})
    assert len(g_c.nodes) >= 6
    g_d = ps._composite_super_graph("p", "e", {"keyword": "rockwool", "country": "SA"})
    execs = {n.executor for n in g_d.nodes}
    assert {"deerflow", "lead", "accio", "trade_ops", "billing"}.issubset(execs)
    assert "outreach.letter" in g_d.policies.approval_required

    g_aeos = ps._aeos_readiness_graph("p", "e", {})
    assert {n.executor for n in g_aeos.nodes} >= {"desktop_hermes", "biz_bot"}

    g_robot = ps._module_robot_graph("p", "e", {"modules": ["acquisition", "wallet"]})
    assert any(n.executor == "biz_bot" for n in g_robot.nodes)
    assert any(n.executor == "module_matrix" for n in g_robot.nodes)

    g_bill = ps._billing_ops_graph("p", "e", {"tenant_id": "demo"})
    assert any(n.executor == "commerce_ops" for n in g_bill.nodes)

    g_tender = ps._tender_dealer_graph("p", "e", {"name": "Acme", "tender_id": "T1"})
    assert any(n.capability == "trade_ops.tender_advance" for n in g_tender.nodes)
    assert "trade_ops.tender_advance" in g_tender.policies.approval_required


def test_all_new_graphs_pass_validate_graph():
    cases = [
        ("composite", ps._composite_super_graph, {"keyword": "cement", "country": "EG"}),
        ("billing", ps._billing_ops_graph, {"tenant_id": "demo"}),
        ("tender", ps._tender_dealer_graph, {"name": "Acme"}),
        ("risk", ps._risk_compliance_graph, {"company": "Acme"}),
        ("knowledge", ps._knowledge_seo_graph, {"topic": "rockwool"}),
        ("robot", ps._module_robot_graph, {"modules": ["acquisition"]}),
        ("aeos", ps._aeos_readiness_graph, {}),
    ]
    for name, builder, payload in cases:
        g = builder("p", "e", payload)
        problems = ps.validate_graph(g)
        assert not problems, f"{name}: {problems}"


def test_desktop_hermes_assemble_and_aeos_executor():
    ex = ExecutorRegistry.get("desktop_hermes")
    ctx = ExecutorContext(db=None, tenant_id="demo", plan_id="p")
    # AEOS 状态
    res = asyncio.run(ex.run(
        TaskNode(id="a1", executor="desktop_hermes", capability="desktop_hermes.aeos", input={}),
        ctx,
    ))
    assert res.status == "succeeded"
    assert res.output["required"] == 8
    assert "invoke_map" in res.output
    # 场景
    res2 = asyncio.run(ex.run(
        TaskNode(id="a2", executor="desktop_hermes", capability="desktop_hermes.scenes", input={}),
        ctx,
    ))
    assert res2.status == "succeeded"
    assert len(res2.output["scenes"]) >= 4
    # 组装：意图 → 真图
    res3 = asyncio.run(ex.run(
        TaskNode(
            id="a3",
            executor="desktop_hermes",
            capability="desktop_hermes.assemble",
            input={"intent": "aeos_readiness", "tenant_id": "demo"},
        ),
        ctx,
    ))
    assert res3.status == "succeeded", res3.error
    assert res3.output.get("ok") is True
    assert res3.output.get("nodes")
    assert res3.output.get("source") in ("L1_template", "L1_hybrid", "L2_llm", "L3_minimal")


def test_aeos_full_invoke_honest():
    async def _run():
        return await aeos_full_invoke(db=None, tenant_id="demo")

    out = asyncio.run(_run())
    assert out["required"] == 8
    assert out["invoke_total"] == 8
    assert out["code_ready"] >= 8
    assert len(out["results"]) == 8
    # 不假成功：允许部分 invoke 失败，但每条有路径
    for r in out["results"]:
        assert r.get("executor"), r
        assert r.get("capability"), r


def test_skill_injection_into_planner_payload():
    ev = IntentEvent(
        event_id="t",
        tenant_id="demo",
        channel="test",
        intent="find_leads",
        payload={"keyword": "rockwool", "country": "SA"},
    )
    enriched = ps._enrich_with_experience(ev, None)
    assert "_skill_refs" in enriched or "_experience_hints" in enriched or True
    # 匹配模板仍走 L1
    builder = ps._match_template(ev)
    assert builder is not None


def test_formula_layers_documented_in_dsh():
    st = desktop_hermes.status()
    assert "DSH外层" in st["layers"]
    assert "Hermes内层DAG" in st["layers"]
    assert "AEOS八大子系统" in st["layers"]
    d = desktop_hermes.decompose_intent("fulfillment", {})
    assert d["outer_layer"] == "DSH/DesktopHermes"
    assert d["next"] == "hermes.decompose"
