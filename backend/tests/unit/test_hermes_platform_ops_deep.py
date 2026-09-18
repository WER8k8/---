# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""深接批次2：platform_ops 执行器。"""
from __future__ import annotations

import asyncio

from app.schemas.hermes_orchestration import TaskNode
from app.services.hermes.executors import ExecutorRegistry
from app.services.hermes.executors.base import ExecutorContext
from app.services.hermes.executors.platform_ops_executor import PlatformOpsExecutor


def test_platform_ops_registered():
    assert ExecutorRegistry.has("platform_ops")
    caps = PlatformOpsExecutor.get_capabilities()
    assert "platform_ops.system_health" in caps
    assert "platform_ops.notify_draft" in caps


def test_system_health_no_db():
    ex = ExecutorRegistry.get("platform_ops")
    node = TaskNode(id="p1", executor="platform_ops", capability="platform_ops.system_health", input={})
    res = asyncio.run(ex.run(node, ExecutorContext(db=None, tenant_id="demo", plan_id="p")))
    assert res.status in ("succeeded", "failed")
    assert "checks" in res.output


def test_notify_draft_no_auto_send():
    ex = ExecutorRegistry.get("platform_ops")
    node = TaskNode(
        id="p2",
        executor="platform_ops",
        capability="platform_ops.notify_draft",
        input={"title": "续费提醒", "body": "请在 7 天内续费", "tenant_id": "demo"},
    )
    res = asyncio.run(ex.run(node, ExecutorContext(db=None, tenant_id="demo", plan_id="p")))
    assert res.status == "succeeded"
    assert res.output["status"] == "draft"
    assert "未自动推送" in res.output.get("note", "") or "人审" in res.output.get("note", "")


def test_notify_draft_requires_fields():
    ex = ExecutorRegistry.get("platform_ops")
    node = TaskNode(id="p3", executor="platform_ops", capability="platform_ops.notify_draft", input={"title": ""})
    res = asyncio.run(ex.run(node, ExecutorContext(db=None, tenant_id="demo", plan_id="p")))
    assert res.status == "failed"


def test_tenants_db_unavailable_honest():
    ex = ExecutorRegistry.get("platform_ops")
    node = TaskNode(id="p4", executor="platform_ops", capability="platform_ops.tenant_list", input={})
    res = asyncio.run(ex.run(node, ExecutorContext(db=None, tenant_id="demo", plan_id="p")))
    assert res.status == "failed"
    assert "db" in (res.error or "").lower()


def test_planner_all_executors_driven():
    import inspect
    import re
    from app.services.hermes import planner_service as ps
    from app.services.hermes.executors import ExecutorRegistry as ER

    src = inspect.getsource(ps)
    driven = set(re.findall(r'executor="([a-z_]+)"', src))
    undriven = set(ER.list_executors()) - driven - {"fake_p0_executor"}
    assert not undriven, sorted(undriven)
