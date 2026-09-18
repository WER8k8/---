# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""深接批次5：compliance_ops + portal_ops。"""
from __future__ import annotations

import asyncio
import hashlib

from app.schemas.hermes_orchestration import TaskNode
from app.services.acquisition import ops_card_store
from app.services.hermes.executors import ExecutorRegistry
from app.services.hermes.executors.base import ExecutorContext
from app.services.hermes.executors.compliance_ops_executor import ComplianceOpsExecutor
from app.services.hermes.executors.portal_ops_executor import PortalOpsExecutor


def _ctx(db=None):
    return ExecutorContext(db=db, tenant_id="demo", plan_id="p-b5")


def test_batch5_registered():
    assert ExecutorRegistry.has("compliance_ops")
    assert ExecutorRegistry.has("portal_ops")
    assert ComplianceOpsExecutor.get_capabilities().get("compliance_ops.hash")
    assert PortalOpsExecutor.get_capabilities().get("portal_ops.media_status")


def test_compliance_hash_deterministic():
    ex = ExecutorRegistry.get("compliance_ops")
    text = "Rockwool export compliance"
    node = TaskNode(id="c1", executor="compliance_ops", capability="compliance_ops.hash", input={"text": text})
    res = asyncio.run(ex.run(node, _ctx(None)))
    assert res.status == "succeeded"
    assert res.output["sha256"] == hashlib.sha256(text.encode()).hexdigest()
    assert res.output["algo"] == "sha256"


def test_compliance_overview_no_db():
    ex = ExecutorRegistry.get("compliance_ops")
    node = TaskNode(id="c2", executor="compliance_ops", capability="compliance_ops.overview", input={})
    res = asyncio.run(ex.run(node, _ctx(None)))
    assert res.status == "failed"
    assert "db" in (res.error or "").lower()


def test_portal_media_status_honest():
    ex = ExecutorRegistry.get("portal_ops")
    node = TaskNode(id="p1", executor="portal_ops", capability="portal_ops.media_status", input={})
    res = asyncio.run(ex.run(node, _ctx(None)))
    assert res.status == "succeeded"
    assert res.output["status"] in ("configured", "not_configured")
    assert "detail" in res.output


def test_portal_agent_summary_from_ops_card():
    ops_card_store._by_inquiry.clear()
    ops_card_store._by_id.clear()
    ops_card_store.materialize(tenant_id="demo", inquiry_id="INQ-AG-1", owner_user_id="agent1")
    ops_card_store.record_win("INQ-AG-1", amount=5000, note="ok")
    ex = ExecutorRegistry.get("portal_ops")
    node = TaskNode(
        id="p2",
        executor="portal_ops",
        capability="portal_ops.agent_summary",
        input={"agent_id": "agent1"},
    )
    res = asyncio.run(ex.run(node, _ctx(None)))
    assert res.status == "succeeded"
    assert res.output["summary"]["won"] >= 1
    assert res.output["summary"]["won_amount"] >= 5000


def test_planner_all_driven_batch5():
    import inspect
    import re
    from app.services.hermes import planner_service as ps
    from app.services.hermes.executors import ExecutorRegistry as ER

    src = inspect.getsource(ps)
    driven = set(re.findall(r'executor="([a-z_]+)"', src))
    undriven = set(ER.list_executors()) - driven - {"fake_p0_executor"}
    assert not undriven, sorted(undriven)
