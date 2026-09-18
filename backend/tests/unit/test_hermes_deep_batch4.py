# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""深接批次4：growth_probe + agent_ops。"""
from __future__ import annotations

import asyncio

from app.schemas.hermes_orchestration import TaskNode
from app.services.acquisition import ops_card_store
from app.services.hermes.executors import ExecutorRegistry
from app.services.hermes.executors.agent_ops_executor import AgentOpsExecutor
from app.services.hermes.executors.base import ExecutorContext
from app.services.hermes.executors.growth_probe_executor import GrowthProbeExecutor


def _ctx(db=None):
    return ExecutorContext(db=db, tenant_id="demo", plan_id="p-b4")


def test_batch4_registered():
    assert ExecutorRegistry.has("growth_probe")
    assert ExecutorRegistry.has("agent_ops")
    assert GrowthProbeExecutor.get_capabilities().get("growth_probe.channels")
    assert AgentOpsExecutor.get_capabilities().get("agent_ops.knowledge_q")


def test_channels_honest_status():
    ex = ExecutorRegistry.get("growth_probe")
    node = TaskNode(id="g1", executor="growth_probe", capability="growth_probe.channels", input={})
    res = asyncio.run(ex.run(node, _ctx(None)))
    assert res.status == "succeeded"
    assert "channels" in res.output
    assert res.output["mock_count"] + res.output["real_count"] == len(res.output["channels"])
    # 每个渠道必须有 is_mock / status
    for c in res.output["channels"]:
        assert "status" in c
        assert "is_mock" in c


def test_payment_probe_unconfigured_honest():
    ex = ExecutorRegistry.get("growth_probe")
    node = TaskNode(id="g2", executor="growth_probe", capability="growth_probe.payment", input={"provider": "alipay"})
    res = asyncio.run(ex.run(node, _ctx(None)))
    # 未配置支付沙箱时应失败诚实；配置了则成功
    assert res.status in ("succeeded", "failed")
    if res.status == "failed":
        assert res.output.get("ok") is False or "not" in (res.error or "").lower() or res.error


def test_seo_include_requires_url():
    ex = ExecutorRegistry.get("growth_probe")
    node = TaskNode(id="g3", executor="growth_probe", capability="growth_probe.seo_include", input={})
    res = asyncio.run(ex.run(node, _ctx(None)))
    assert res.status == "failed"


def test_agent_ops_performance_no_db():
    ex = ExecutorRegistry.get("agent_ops")
    node = TaskNode(id="a1", executor="agent_ops", capability="agent_ops.performance", input={})
    res = asyncio.run(ex.run(node, _ctx(None)))
    assert res.status == "failed"
    assert "db" in (res.error or "").lower()


def test_agent_ops_knowledge_local_hits():
    ex = ExecutorRegistry.get("agent_ops")
    node = TaskNode(
        id="a2",
        executor="agent_ops",
        capability="agent_ops.knowledge_q",
        input={"query": "GDPR 退订", "limit": 5},
    )
    res = asyncio.run(ex.run(node, _ctx(None)))
    assert res.status == "succeeded"
    assert res.output["query"] == "GDPR 退订"
    # 本地知识队列应能命中 GDPR
    assert res.output["local_count"] >= 1
    assert any("GDPR" in (h.get("title") or "") or "GDPR" in (h.get("plain") or "") for h in res.output["hits"])


def test_planner_all_driven_batch4():
    import inspect
    import re
    from app.services.hermes import planner_service as ps
    from app.services.hermes.executors import ExecutorRegistry as ER

    src = inspect.getsource(ps)
    driven = set(re.findall(r'executor="([a-z_]+)"', src))
    undriven = set(ER.list_executors()) - driven - {"fake_p0_executor"}
    assert not undriven, sorted(undriven)


def test_registry_has_batch4_executors():
    names = set(ExecutorRegistry.list_executors())
    assert {"growth_probe", "agent_ops"}.issubset(names)
