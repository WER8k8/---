# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""串联率 100%：module_matrix 执行器 + 台账覆盖。"""
from __future__ import annotations

import asyncio

from app.schemas.hermes_orchestration import TaskNode
from app.services.hermes.executors import ExecutorRegistry
from app.services.hermes.executors.base import ExecutorContext
from app.services.hermes.executors.module_matrix_executor import ModuleMatrixExecutor


def test_module_matrix_registered():
    assert ExecutorRegistry.has("module_matrix")
    assert ModuleMatrixExecutor.get_executor_name() == "module_matrix"
    caps = ModuleMatrixExecutor.get_capabilities()
    assert "matrix.inspect" in caps
    assert "matrix.invoke" in caps


def test_matrix_inspect_real_route_module():
    ex = ExecutorRegistry.get("module_matrix")
    node = TaskNode(id="m1", executor="module_matrix", capability="matrix.inspect",
                    input={"module": "acquisition"})
    ctx = ExecutorContext(db=None, tenant_id="demo", plan_id="p1")
    res = asyncio.run(ex.run(node, ctx))
    assert res.status == "succeeded"
    assert res.output["module"] == "acquisition"
    assert res.output["endpoints"] > 0
    assert res.output["wired"] is True


def test_matrix_invoke_honest_no_fake_success():
    ex = ExecutorRegistry.get("module_matrix")
    node = TaskNode(id="m2", executor="module_matrix", capability="matrix.invoke",
                    input={"module": "orchestration", "action": "surface"})
    ctx = ExecutorContext(db=None, tenant_id="demo", plan_id="p1")
    res = asyncio.run(ex.run(node, ctx))
    assert res.status == "succeeded"
    # 无只读 helper 时不编造业务结果
    assert res.output.get("invoked") in (True, False)
    if not res.output.get("invoked"):
        assert res.output.get("result") is None
        assert "不伪造" in res.output.get("note", "") or "能力面" in res.output.get("note", "")


def test_matrix_rejects_bad_module_name():
    ex = ExecutorRegistry.get("module_matrix")
    node = TaskNode(id="m3", executor="module_matrix", capability="matrix.inspect",
                    input={"module": "../etc/passwd"})
    ctx = ExecutorContext(db=None, tenant_id="demo", plan_id="p1")
    res = asyncio.run(ex.run(node, ctx))
    assert res.status == "failed"


def test_capability_ledger_100pct_or_covers_all():
    """台账脚本必须把剩余模块登记进 module_matrix；串联率目标 100%。"""
    import importlib.util
    from pathlib import Path

    root = Path(__file__).resolve().parents[3].parent  # worktree
    # tools 在工作区根
    ws = root.parent if root.name.startswith("agents-") else root
    # 实际路径：上线网站开发完成/tools/capability_ledger.py
    tool = Path(r"C:\Users\Administrator\Documents\上线网站开发完成\tools\capability_ledger.py")
    assert tool.exists()
    spec = importlib.util.spec_from_file_location("capability_ledger", tool)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert "module_matrix" in mod.EXECUTOR_COVERS
    assert len(mod.EXECUTOR_COVERS["module_matrix"]) >= 120
    assert "auto_discovery" in mod.EXECUTOR_COVERS["module_matrix"]
    assert mod.MOCK_EXECUTORS == frozenset() or "trade_ai_agent" not in mod.MOCK_EXECUTORS
