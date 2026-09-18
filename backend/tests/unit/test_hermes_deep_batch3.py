# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""深接批次3：trade_ops / content_deep / outreach_loop。"""
from __future__ import annotations

import asyncio

from app.schemas.hermes_orchestration import TaskNode
from app.services.acquisition import ops_card_store
from app.services.hermes.executors import ExecutorRegistry
from app.services.hermes.executors.base import ExecutorContext
from app.services.hermes.executors.content_deep_executor import ContentDeepExecutor
from app.services.hermes.executors.outreach_loop_executor import OutreachLoopExecutor
from app.services.hermes.executors.trade_ops_executor import TradeOpsExecutor


def _ctx(db=None):
    return ExecutorContext(db=db, tenant_id="demo", plan_id="p-b3")


def test_batch3_registered():
    for name, cls in (
        ("trade_ops", TradeOpsExecutor),
        ("content_deep", ContentDeepExecutor),
        ("outreach_loop", OutreachLoopExecutor),
    ):
        assert ExecutorRegistry.has(name)
        assert cls.get_executor_name() == name
        assert cls.get_capabilities()


def test_pi_precheck_blocks_or_warns():
    ops_card_store._by_inquiry.clear()
    ops_card_store._by_id.clear()
    ops_card_store.materialize(tenant_id="demo", inquiry_id="INQ-PI-CHK", grade="D", score=15)
    ex = ExecutorRegistry.get("trade_ops")
    node = TaskNode(
        id="t1",
        executor="trade_ops",
        capability="trade_ops.pi_precheck",
        input={"inquiry_id": "INQ-PI-CHK", "auto_pi": True, "deposit_ratio": 0, "country": "IN"},
    )
    res = asyncio.run(ex.run(node, _ctx(None)))
    assert res.status == "succeeded"
    assert res.output.get("auto_pi_allowed") is False or res.output.get("level") in ("high", "medium")
    assert "executor" in res.output


def test_fulfillment_node_write():
    ops_card_store.materialize(tenant_id="demo", inquiry_id="INQ-FL-1")
    ex = ExecutorRegistry.get("trade_ops")
    node = TaskNode(
        id="t2",
        executor="trade_ops",
        capability="trade_ops.fulfillment_node",
        input={"inquiry_id": "INQ-FL-1", "key": "pi", "status": "active", "ref": "PI-TEST-1"},
    )
    res = asyncio.run(ex.run(node, _ctx(None)))
    assert res.status == "succeeded"
    assert res.output["inquiry_id"] == "INQ-FL-1"
    keys = {n["key"] for n in res.output.get("nodes") or []}
    assert "pi" in keys
    card = ops_card_store.get_by_inquiry("INQ-FL-1")
    assert any(getattr(n, "key", "") == "pi" for n in card.fulfillment_nodes)


def test_goodjob_pi_not_configured_honest():
    import os
    os.environ.pop("GOODJOB_BASE_URL", None)
    ex = ExecutorRegistry.get("trade_ops")
    node = TaskNode(
        id="t3",
        executor="trade_ops",
        capability="trade_ops.goodjob_pi",
        input={"inquiry_id": "INQ-PI-GJ"},
    )
    res = asyncio.run(ex.run(node, _ctx(None)))
    assert res.status == "failed"
    assert "GOODJOB" in (res.error or "") or res.output.get("status") == "not_configured"


def test_content_deep_knowledge_and_attr():
    ex = ExecutorRegistry.get("content_deep")
    node = TaskNode(id="c1", executor="content_deep", capability="content_deep.knowledge", input={"tenant_id": "demo"})
    res = asyncio.run(ex.run(node, _ctx(None)))
    assert res.status == "succeeded"
    assert "plain_summary" in res.output

    node2 = TaskNode(
        id="c2",
        executor="content_deep",
        capability="content_deep.acquisition",
        input={"content_id": "art-1", "inquiry_id": "INQ-ATTR-1", "tenant_id": "demo"},
    )
    res2 = asyncio.run(ex.run(node2, _ctx(None)))
    assert res2.status == "succeeded"
    assert res2.output.get("linked") is True


def test_seo_meta_degraded_flag():
    ex = ExecutorRegistry.get("content_deep")
    node = TaskNode(
        id="c3",
        executor="content_deep",
        capability="content_deep.seo_meta",
        input={"product_name": "Rockwool Board", "industry": "building materials"},
    )
    res = asyncio.run(ex.run(node, _ctx(None)))
    # 诚实契约：凡能产出 meta 的路径，output 标 degraded 时顶层 status 不得伪装 succeeded；
    # AiSiteEngine 不可导入等失败路径 → 如实 failed（空 output），同样可接受。
    if res.output.get("executor"):
        assert res.output.get("executor") == "content_deep"
        assert "degraded" in res.output
        if res.output.get("degraded"):
            assert res.status == "degraded", "seo_meta 为模板/降级却报 succeeded = 假成功"


def test_outreach_gate_blocks_without_research():
    ops_card_store.materialize(tenant_id="demo", inquiry_id="INQ-OUT-1")
    ops_card_store.set_research_level("INQ-OUT-1", "none")
    ex = ExecutorRegistry.get("outreach_loop")
    node = TaskNode(
        id="o1",
        executor="outreach_loop",
        capability="outreach_loop.gate",
        input={"inquiry_id": "INQ-OUT-1", "research_level": "none", "email": "x@y.com", "tenant_id": "demo"},
    )
    res = asyncio.run(ex.run(node, _ctx(None)))
    assert res.status == "succeeded"
    assert res.output.get("allowed") is False
    assert res.output.get("approval_required") is True


def test_outreach_gate_after_osint():
    ops_card_store.materialize(tenant_id="demo", inquiry_id="INQ-OUT-2")
    ops_card_store.set_research_level("INQ-OUT-2", "osint")
    ex = ExecutorRegistry.get("outreach_loop")
    node = TaskNode(
        id="o2",
        executor="outreach_loop",
        capability="outreach_loop.gate",
        input={"inquiry_id": "INQ-OUT-2", "email": "ok@buyer.com", "tenant_id": "demo"},
    )
    res = asyncio.run(ex.run(node, _ctx(None)))
    assert res.status == "succeeded"
    assert res.output.get("allowed") is True
    assert res.output.get("approval_required") is True  # 人审红线不消失


def test_planner_all_driven_batch3():
    import inspect
    import re
    from app.services.hermes import planner_service as ps
    from app.services.hermes.executors import ExecutorRegistry as ER

    src = inspect.getsource(ps)
    driven = set(re.findall(r'executor="([a-z_]+)"', src))
    undriven = set(ER.list_executors()) - driven - {"fake_p0_executor"}
    assert not undriven, sorted(undriven)
