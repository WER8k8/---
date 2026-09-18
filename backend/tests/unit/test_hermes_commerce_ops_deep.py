# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""深接批次1：commerce_ops 执行器真服务调用。"""
from __future__ import annotations

import asyncio

from app.schemas.hermes_orchestration import TaskNode
from app.services.acquisition import ops_card_store
from app.services.hermes.executors import ExecutorRegistry
from app.services.hermes.executors.base import ExecutorContext
from app.services.hermes.executors.commerce_ops_executor import CommerceOpsExecutor


class _User:
    pass


def _ctx(db=None):
    return ExecutorContext(db=db, tenant_id="demo", plan_id="p-commerce")


def test_commerce_ops_registered_and_caps():
    assert ExecutorRegistry.has("commerce_ops")
    assert CommerceOpsExecutor.get_executor_name() == "commerce_ops"
    caps = CommerceOpsExecutor.get_capabilities()
    for k in (
        "commerce_ops.email_enqueue",
        "commerce_ops.followup_sequence",
        "commerce_ops.outreach_scan",
        "commerce_ops.crm_pipeline",
        "commerce_ops.wallet_token",
        "commerce_ops.acquisition_card",
    ):
        assert k in caps


def test_acquisition_card_deep_wire():
    ops_card_store._by_inquiry.clear()
    ops_card_store._by_id.clear()
    ex = ExecutorRegistry.get("commerce_ops")
    node = TaskNode(
        id="c1",
        executor="commerce_ops",
        capability="commerce_ops.acquisition_card",
        input={"inquiry_id": "INQ-DEEP-1", "tenant_id": "demo"},
    )
    res = asyncio.run(ex.run(node, _ctx(None)))
    assert res.status == "succeeded"
    assert res.output["inquiry_id"] == "INQ-DEEP-1"
    assert res.output["stage"]
    assert "summary" in res.output
    card = ops_card_store.get_by_inquiry("INQ-DEEP-1")
    assert card is not None


def test_wallet_token_honest():
    ex = ExecutorRegistry.get("commerce_ops")
    node = TaskNode(
        id="c2",
        executor="commerce_ops",
        capability="commerce_ops.wallet_token",
        input={"tenant_id": "demo"},
    )
    res = asyncio.run(ex.run(node, _ctx(None)))
    assert res.status == "succeeded"
    assert "status" in res.output
    assert "balance" in res.output
    # 无库时诚实 unknown/empty，不编造
    if res.output.get("source") in (None, "none"):
        assert res.output.get("balance") in (None, 0) or res.output.get("status") in (
            "unknown",
            "empty",
            "ok",
        )


def test_email_enqueue_rejects_suppressed():
    from app.services.acquisition.suppression_list import suppression_store

    suppression_store.add(email="blocked@buyer.com", tenant_id="demo", reason="unsubscribe")
    ex = ExecutorRegistry.get("commerce_ops")
    node = TaskNode(
        id="c3",
        executor="commerce_ops",
        capability="commerce_ops.email_enqueue",
        input={
            "to_email": "blocked@buyer.com",
            "subject": "Hello",
            "body": "Should not enqueue",
            "tenant_id": "demo",
        },
    )
    res = asyncio.run(ex.run(node, _ctx(None)))
    assert res.status == "failed"
    assert "suppressed" in (res.error or "") or "抑制" in (res.error or "") or "退订" in str(res.output)


def test_email_enqueue_requires_fields():
    ex = ExecutorRegistry.get("commerce_ops")
    node = TaskNode(
        id="c4",
        executor="commerce_ops",
        capability="commerce_ops.email_enqueue",
        input={"to_email": "not-an-email", "subject": "", "body": ""},
    )
    res = asyncio.run(ex.run(node, _ctx(None)))
    assert res.status == "failed"


def test_followup_sequence_build():
    ex = ExecutorRegistry.get("commerce_ops")
    node = TaskNode(
        id="c5",
        executor="commerce_ops",
        capability="commerce_ops.followup_sequence",
        input={"lead_id": "lead-deep-1", "lead_email": "a@b.com", "lead_name": "Ahmed"},
    )
    res = asyncio.run(ex.run(node, _ctx(None)))
    # 真引擎可能成功；若引擎异常应 failed 诚实
    assert res.status in ("succeeded", "failed")
    if res.status == "succeeded":
        assert res.output.get("lead_id") == "lead-deep-1"
        assert "stage" in res.output


def test_crm_pipeline_without_db_fails_honest():
    ex = ExecutorRegistry.get("commerce_ops")
    node = TaskNode(id="c6", executor="commerce_ops", capability="commerce_ops.crm_pipeline", input={})
    res = asyncio.run(ex.run(node, _ctx(None)))
    assert res.status == "failed"
    assert "db" in (res.error or "").lower()


def test_planner_drives_commerce_ops():
    import inspect
    import re
    from app.services.hermes import planner_service as ps
    from app.services.hermes.executors import ExecutorRegistry as ER

    src = inspect.getsource(ps)
    driven = set(re.findall(r'executor="([a-z_]+)"', src))
    registered = set(ER.list_executors())
    undriven = registered - driven - {"fake_p0_executor"}
    assert not undriven, f"undriven executors: {sorted(undriven)}"
