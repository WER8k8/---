# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""全模块业务机器人覆盖率 + 真实业务动作抽查。"""
from __future__ import annotations

import asyncio
from pathlib import Path

from app.schemas.hermes_orchestration import TaskNode
from app.services.hermes.biz_bot_actions import (
    MODULE_BUSINESS,
    all_route_modules,
    coverage_report,
    run_module_business,
)
from app.services.hermes.executors import ExecutorRegistry
from app.services.hermes.executors.base import ExecutorContext


def test_all_route_modules_have_business_robot():
    cov = coverage_report()
    assert cov["route_modules"] >= 150
    assert cov["all_covered"] is True, f"missing={cov['missing'][:20]}"
    assert cov["coverage_pct"] == 100.0
    # 每个真实路由模块都在注册表
    mods = all_route_modules()
    for m in mods:
        assert m in MODULE_BUSINESS, m


def test_biz_bot_registered_and_coverage_cap():
    assert ExecutorRegistry.has("biz_bot")
    ex = ExecutorRegistry.get("biz_bot")
    caps = ex.get_capabilities()
    assert "biz_bot.run" in caps
    assert "biz_bot.coverage" in caps
    node = TaskNode(id="c1", executor="biz_bot", capability="biz_bot.coverage", input={})
    ctx = ExecutorContext(db=None, tenant_id="demo", plan_id="p")
    res = asyncio.run(ex.run(node, ctx))
    assert res.status == "succeeded"
    assert res.output["coverage"]["all_covered"] is True


def test_sample_modules_run_business_mode_not_surface():
    samples = [
        "acquisition", "crm_pipeline", "wallet", "tenants",
        "orchestration", "knowledge", "compliance", "system_health",
        "skill_store", "growth_loop", "email_queue", "seo_matrix",
        "logistics", "agent_portal", "deepseek_harness", "products",
    ]
    ex = ExecutorRegistry.get("biz_bot")
    ctx = ExecutorContext(db=None, tenant_id="demo", plan_id="p")
    for m in samples:
        node = TaskNode(
            id=f"biz-{m}",
            executor="biz_bot",
            capability="biz_bot.run",
            input={"module": m, "tenant_id": "demo"},
        )
        res = asyncio.run(ex.run(node, ctx))
        assert res.status == "succeeded", f"{m}: {res.error}"
        assert res.output["mode"] == "business", m
        assert res.output["business_robot"] is True
        assert res.output["result"], m


def test_all_modules_mode_business_via_run_module_business():
    """每个路由模块业务机器人 mode=business（可无 DB）。"""
    mods = all_route_modules()
    assert len(mods) >= 150
    bad = []
    for m in mods:
        out = run_module_business(m, payload={"module": m, "tenant_id": "demo"}, db=None)
        if out.get("mode") != "business" or not out.get("business_robot"):
            bad.append(m)
    assert not bad, f"not business robots: {bad[:20]}"


def test_deep_executor_result_present_when_runner_used():
    def fake_deep(ex, cap, payload):
        return {"status": "succeeded", "output": {"fake": True}, "executor": ex, "capability": cap}

    out = run_module_business(
        "acquisition",
        payload={"tenant_id": "demo"},
        db=None,
        deep_runner=fake_deep,
    )
    assert out["mode"] == "business"
    assert out["deep_result"] is not None
    assert out["deep_result"]["executor"] == "commerce_ops"


def test_capability_ledger_covers_biz_bot_all_modules():
    import importlib.util

    tool = Path(r"C:\Users\Administrator\Documents\上线网站开发完成\tools\capability_ledger.py")
    assert tool.exists()
    spec = importlib.util.spec_from_file_location("capability_ledger_biz", tool)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert "biz_bot" in mod.EXECUTOR_COVERS
    assert "desktop_hermes" in mod.EXECUTOR_COVERS
    assert len(mod.EXECUTOR_COVERS["biz_bot"]) >= 150
    assert "module_matrix" in mod.EXECUTOR_COVERS
    assert len(mod.EXECUTOR_COVERS["module_matrix"]) >= 150
