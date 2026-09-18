# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""深接批次6：data_ops。"""
from __future__ import annotations

import asyncio

from app.schemas.hermes_orchestration import TaskNode
from app.services.hermes.executors import ExecutorRegistry
from app.services.hermes.executors.base import ExecutorContext
from app.services.hermes.executors.data_ops_executor import DataOpsExecutor


def _ctx(db=None):
    return ExecutorContext(db=db, tenant_id="demo", plan_id="p-b6")


def test_data_ops_registered():
    assert ExecutorRegistry.has("data_ops")
    caps = DataOpsExecutor.get_capabilities()
    assert "data_ops.content_stats" in caps
    assert "data_ops.domain_resolve" in caps


def test_content_stats_no_db():
    ex = ExecutorRegistry.get("data_ops")
    node = TaskNode(id="d1", executor="data_ops", capability="data_ops.content_stats", input={})
    res = asyncio.run(ex.run(node, _ctx(None)))
    assert res.status == "failed"
    assert "db" in (res.error or "").lower()


def test_notify_draft_memory_only_honest():
    ex = ExecutorRegistry.get("data_ops")
    node = TaskNode(
        id="d2",
        executor="data_ops",
        capability="data_ops.notify_draft",
        input={"title": "续费提醒", "body": "请关注续费"},
    )
    res = asyncio.run(ex.run(node, _ctx(None)))
    assert res.status == "succeeded"
    assert res.output["status"] in ("draft_memory_only", "draft_saved")
    assert "未自动推送" in res.output.get("note", "")


def test_domain_resolve_requires_host():
    ex = ExecutorRegistry.get("data_ops")
    node = TaskNode(id="d3", executor="data_ops", capability="data_ops.domain_resolve", input={})
    res = asyncio.run(ex.run(node, _ctx(None)))
    assert res.status == "failed"


def test_planner_driven_data_ops():
    import inspect
    import re
    from app.services.hermes import planner_service as ps
    from app.services.hermes.executors import ExecutorRegistry as ER

    src = inspect.getsource(ps)
    driven = set(re.findall(r'executor="([a-z_]+)"', src))
    undriven = set(ER.list_executors()) - driven - {"fake_p0_executor"}
    assert not undriven, sorted(undriven)
