# -*- coding: utf-8 -*-
"""advance_plan 闸门顺序回归测试（不连真库）。

钉住 2026-09-10 端到端真跑 n4(publish.multi) 的 P0：
DAG Governor 的人工审批闸在「解析上游数据依赖」之前就 continue 掉了，
节点一旦停在 wait_human 就再也不会回到这段逻辑，
于是人工放行后执行器只拿得到 static_input，真实内容字段全缺，
报 missing_content 失败并连带把下游整枝取消。

这里锁死顺序：解析 effective_input 必须发生在任何闸门判定之前。
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from app.services.hermes.task_control_supervisor import advance_plan


def _mk_child(node_id: str, status: str, cfg: dict, output: dict | None = None):
    task = MagicMock()
    task.id = f"task-{node_id}"
    task.status = status
    task.task_type = f"hermes_node:{cfg.get('executor', 'x')}"
    task.tenant_id = "tenant-1"
    task.parent_task_id = "plan-1"
    task.input_json = json.dumps(cfg, ensure_ascii=False)
    task.output_json = json.dumps(output, ensure_ascii=False) if output else None
    return task


def _run_advance(children, policies):
    db = MagicMock()
    plan_task = MagicMock()
    plan_task.id = "plan-1"
    plan_task.status = "executing"
    plan_task.input_json = json.dumps({"policies": policies}, ensure_ascii=False)

    db.query.return_value.filter.return_value.first.return_value = plan_task
    db.query.return_value.filter.return_value.all.side_effect = [children, children]

    with patch("app.tasks.orchestration_tasks.process_ai_task") as celery_task:
        dispatched = advance_plan(db, "plan-1")
    return db, plan_task, dispatched, celery_task


def _cfg_of(task) -> dict:
    return json.loads(task.input_json)


def test_approval_gated_node_still_gets_upstream_content():
    """命中审批闸的节点，停靠时就必须带上解析好的 effective_input。"""
    upstream = _mk_child("n1", "done",
                         {"node_id": "n1", "executor": "site_builder",
                          "capability": "site.generate", "depends_on": []},
                         output={"title": "铝合金幕墙系统", "url": "https://demo.example.com"})
    gated = _mk_child("n4", "paused",
                      {"node_id": "n4", "executor": "publish",
                       "capability": "publish.multi", "depends_on": ["n1"],
                       "static_input": {"channels": ["wechat", "zhihu"]},
                       "input_from": {"title": "n1.output.title",
                                      "url": "n1.output.url"}})

    _db, _plan, dispatched, celery_task = _run_advance(
        [upstream, gated], {"approval_required": ["publish.*"], "max_parallel": 5}
    )

    assert gated.status == "wait_human", "命中审批闸应挂起待人工"
    eff = _cfg_of(gated).get("effective_input")
    assert eff, "审批门停靠的节点绝不能没有 effective_input（放行后必然报缺内容）"
    assert eff["title"] == "铝合金幕墙系统"
    assert eff["url"] == "https://demo.example.com"
    assert eff["channels"] == ["wechat", "zhihu"], "static_input 必须一并保留"
    assert gated.id not in dispatched
    celery_task.delay.assert_not_called()


def test_non_gated_node_dispatches_with_resolved_input():
    """未命中审批闸的节点照常派发，且带解析后的入参。"""
    upstream = _mk_child("n1", "done",
                         {"node_id": "n1", "executor": "site_builder",
                          "capability": "site.generate", "depends_on": []},
                         output={"title": "玻璃钢格栅"})
    ready = _mk_child("n3", "paused",
                      {"node_id": "n3", "executor": "deerflow",
                       "capability": "seo.optimize", "depends_on": ["n1"],
                       "input_from": {"title": "n1.output.title"}})

    _db, _plan, dispatched, celery_task = _run_advance(
        [upstream, ready], {"approval_required": ["publish.*"], "max_parallel": 5}
    )

    assert ready.status == "created"
    assert _cfg_of(ready)["effective_input"]["title"] == "玻璃钢格栅"
    assert dispatched == [ready.id]
    celery_task.delay.assert_called_once_with(ready.id)


def test_unsatisfied_dependency_stays_parked():
    """上游没跑完的节点继续 paused，且不写 effective_input。"""
    running = _mk_child("n1", "executing",
                        {"node_id": "n1", "executor": "site_builder",
                         "capability": "site.generate", "depends_on": []})
    waiting = _mk_child("n2", "paused",
                        {"node_id": "n2", "executor": "content",
                         "capability": "content.create", "depends_on": ["n1"],
                         "input_from": {"title": "n1.output.title"}})

    _db, _plan, dispatched, celery_task = _run_advance([running, waiting], {})

    assert waiting.status == "paused"
    assert "effective_input" not in _cfg_of(waiting)
    assert dispatched == []
    celery_task.delay.assert_not_called()


def test_budget_breaker_parks_node_with_reason_and_content():
    """预算熔断同样要在挂起前解析好内容字段。"""
    upstream = _mk_child("n1", "done",
                         {"node_id": "n1", "executor": "site_builder",
                          "capability": "site.generate", "depends_on": []},
                         output={"title": "石英砖"})
    gated = _mk_child("n4", "paused",
                      {"node_id": "n4", "executor": "publish",
                       "capability": "publish.multi", "depends_on": ["n1"],
                       "input_from": {"title": "n1.output.title"}})
    upstream.budget_used = 999.0

    _db, _plan, dispatched, _celery = _run_advance(
        [upstream, gated],
        {"approval_required": [], "budget_cap": {"max_tokens_total": 100}},
    )

    cfg = _cfg_of(gated)
    assert gated.status == "paused"
    assert str(cfg.get("blocked_reason", "")).startswith("budget_exceeded")
    assert cfg.get("effective_input", {}).get("title") == "石英砖"
    assert dispatched == []
