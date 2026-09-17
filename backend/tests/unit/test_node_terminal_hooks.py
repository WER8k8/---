# -*- coding: utf-8 -*-
"""节点终态钩子链回归测试（H.7：D 类 Evolution/Pipeline 变钩子）。"""
from __future__ import annotations

import os
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.hermes.node_terminal_hooks import fire_node_terminal_hooks


def _task(task_type: str = "hermes_node:content", **kw) -> SimpleNamespace:
    base = dict(
        id=str(uuid.uuid4()),
        task_type=task_type,
        tenant_id="tenant-1",
        parent_task_id=None,
        input_json='{"message": "m"}',
        status="created",
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _db(count: int = 1) -> MagicMock:
    db = MagicMock()
    db.query.return_value.filter.return_value.scalar.return_value = count
    return db


def test_done_node_records_evolution():
    """节点 done → 进化引擎数据入口被调用（经验回流触发点）。"""
    with patch("app.services.evolution.engine.EvolutionEngine") as MockEng:
        inst = MockEng.return_value
        inst.record_task_execution.return_value = SimpleNamespace(id="rec-1")
        inst.run_experience_extraction.return_value = {"created": 0}
        report = fire_node_terminal_hooks(
            _db(), _task(), success=True, result={"summary": "built 3 pages"})

    assert report.evolution_recorded is True
    assert report.evolution_record_id == "rec-1"
    args = inst.record_task_execution.call_args.kwargs
    assert args["task_type"] == "content"
    assert args["executor_type"] == "hermes"
    assert args["success"] is True
    assert args["tenant_id"] == "tenant-1"


def test_failed_node_records_failure_detail():
    """节点 failed → 失败明细（error_code/message）必须进进化数据入口。"""
    with patch("app.services.evolution.engine.EvolutionEngine") as MockEng:
        inst = MockEng.return_value
        inst.record_task_execution.return_value = SimpleNamespace(id="rec-2")
        report = fire_node_terminal_hooks(
            _db(), _task(), success=False,
            error_code="executor_failed", error_message="all platforms failed")

    args = inst.record_task_execution.call_args.kwargs
    assert args["success"] is False
    assert args["error_code"] == "executor_failed"
    assert args["error_message"] == "all platforms failed"
    # 失败路径不打管线关卡
    assert report.pipeline_gate in ("off", "skipped")


def test_pipeline_gate_off_by_default():
    """特性开关默认关 → 关卡标记 off，零回归。"""
    with patch.dict(os.environ, {}, clear=False), \
         patch("app.services.pipeline.chains.gate_content") as MockGate:
        os.environ.pop("PIPELINE_GATES_ENABLED", None)
        report = fire_node_terminal_hooks(
            _db(), _task(), success=True, result={"reply": "hello"})
    assert report.pipeline_gate == "off"
    MockGate.assert_not_called()


def test_pipeline_gate_marker_on_content_node():
    """开关开 + 内容族节点 → 关卡 verdict 进入报告（标记语义）。"""
    with patch.dict(os.environ, {"PIPELINE_GATES_ENABLED": "1"}), \
         patch("app.services.pipeline.chains.gate_content") as MockGate:
        MockGate.return_value = SimpleNamespace(verdict="needs_review")
        report = fire_node_terminal_hooks(
            _db(), _task(task_type="hermes_node:content"),
            success=True, result={"reply": "post body"})
    assert report.pipeline_gate == "needs_review"
    assert MockGate.called


def test_pipeline_gate_skips_non_content_node():
    """非内容族节点不介入管线关卡。"""
    with patch.dict(os.environ, {"PIPELINE_GATES_ENABLED": "1"}), \
         patch("app.services.pipeline.chains.gate_content") as MockGate:
        report = fire_node_terminal_hooks(
            _db(), _task(task_type="hermes_node:site_builder"),
            success=True, result={"summary": "site ok"})
    assert report.pipeline_gate == "skipped"
    MockGate.assert_not_called()


def test_evolution_failure_does_not_raise():
    """进化钩子异常被吞掉，钩子链永不抛出（主链终态已落定）。"""
    with patch("app.services.evolution.engine.EvolutionEngine") as MockEng:
        MockEng.return_value.record_task_execution.side_effect = RuntimeError("pg down")
        report = fire_node_terminal_hooks(
            _db(), _task(), success=True, result={})

    assert "evolution" in report.errors
    assert "RuntimeError" in report.errors["evolution"]
    assert report.evolution_recorded is False


def test_extraction_triggers_at_threshold():
    """回溯窗口内记录数达阈值 → 触发一次经验沉淀。"""
    with patch("app.services.evolution.engine.EvolutionEngine") as MockEng:
        inst = MockEng.return_value
        inst.record_task_execution.return_value = SimpleNamespace(id="rec-3")
        inst.run_experience_extraction.return_value = {"created": 2}
        report = fire_node_terminal_hooks(
            _db(count=5), _task(), success=True, result={})

    inst.run_experience_extraction.assert_called_once()
    assert report.experiences_created == 2


def test_bridge_dispatch_fires_terminal_hooks():
    """桥的派发路径（done）会触发终态钩子，且钩子失败不影响派发返回。"""
    from app.services.tasks.hermes_task_bridge import dispatch_ai_task

    task = _task(task_type="wangcai_intent", parent_task_id=None)
    db = MagicMock()
    with patch("app.services.tasks.hermes_task_bridge.TaskControlService") as MockCtl, \
         patch("app.services.tasks.hermes_task_bridge.ROUTERS") as MockRouters, \
         patch("app.services.hermes.node_terminal_hooks.fire_node_terminal_hooks") as MockHooks:
        MockCtl.return_value.get_task.return_value = task
        MockRouters.get.return_value = lambda d, t: {"reply": "hs 6806"}
        MockHooks.return_value = SimpleNamespace(summary=lambda: "ok")

        out = dispatch_ai_task(db, str(task.id), tenant_id="tenant-1")

    assert out is task
    assert MockHooks.called
    assert MockHooks.call_args.kwargs["success"] is True
    assert MockHooks.call_args.kwargs["result"] == {"reply": "hs 6806"}
