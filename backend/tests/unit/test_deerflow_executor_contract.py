# -*- coding: utf-8 -*-
"""DeerFlow 适配器契约回归测试（不连真库）。

钉住 2026-09-10 端到端真跑 n3(seo.optimize) 暴露的两个真 bug：

1. 能力名不翻译：编排图下发的是 Hermes 能力名（seo.optimize），
   而 DeerFlow 的 _dispatch_by_intent 只认自己那 9 个 intent。
   能力名一路掉进 _exec_generic 兜底分支，撞上 paperclip 外键后
   还回了个假 completed，把整条计划拖崩。
2. 合成承载 job 时传了 title=：deerflow_jobs 表根本没有 title 列，
   直接 TypeError 让整个节点失败。
"""
from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from app.models.deerflow_job import DeerflowJob
from app.schemas.hermes_orchestration import TaskNode
from app.services.deerflow.executor import SubTaskExecutor
from app.services.deerflow.planner import SubTask
from app.services.hermes.executors.base import ExecutorContext
from app.services.hermes.executors.deerflow_executor import (
    _CAPABILITY_TO_INTENT,
    DeerflowExecutor,
)


def _dedicated_handler_name(intent: str) -> str:
    """_dispatch_by_intent 里该 intent 应当走到的专属处理函数名。"""
    return "_exec_" + intent


@pytest.mark.parametrize("capability, intent", sorted(_CAPABILITY_TO_INTENT.items()))
def test_mapped_intent_hits_a_dedicated_handler(capability, intent):
    """每个映射目标都必须是 DeerFlow 真实处理的 intent，不能掉进通用兜底。"""
    fake_self = MagicMock(spec=SubTaskExecutor)
    subtask = SubTask(id="s1", title="t", intent=intent, agent_ref="", parameters={})

    SubTaskExecutor._dispatch_by_intent(fake_self, subtask)

    fake_self._exec_generic.assert_not_called()
    handler = getattr(fake_self, _dedicated_handler_name(intent))
    assert handler.called, f"{capability} → {intent} 没走到专属处理函数"


def test_mapping_covers_the_dag_capabilities():
    """编排图里会落到 deerflow 执行器的能力名，映射表必须全覆盖。"""
    # 2026-09-10 真跑实测：模板图 7 节点里由 deerflow 承接的能力
    for cap in ("seo.optimize", "content.create", "research.deep_run",
                "outreach.letter", "publish.multi", "publish.single",
                "prospect.enrich"):
        assert cap in _CAPABILITY_TO_INTENT, f"能力 {cap} 缺 intent 映射"


def test_deerflow_job_has_no_title_column():
    """回归护栏：合成 job 时绝不能再传 title=（表里没这列）。"""
    cols = {c.name for c in DeerflowJob.__table__.columns}
    assert "title" not in cols
    assert {"id", "tenant_id", "intent", "status", "payload_json"} <= cols


def _run_node(capability: str, node_id: str = "n3"):
    """用假 DB 跑一次 DeerflowExecutor.run，返回 (result, 捕获的 intent)。"""
    ctx = ExecutorContext(db=MagicMock(), tenant_id="tenant-1", plan_id="plan-1")
    # 查不到真实 job → 逼它走合成 DeerflowJob 分支（正是原来炸 TypeError 的地方）
    ctx.db.query.return_value.filter.return_value.first.return_value = None

    captured: dict[str, str] = {}

    def fake_execute(self, subtask):
        captured["intent"] = subtask.intent
        res = MagicMock()
        res.success = True
        res.output = {"ok": True}
        res.error = None
        return res

    node = TaskNode(id=node_id, executor="deerflow", capability=capability,
                    depends_on=["n2"], input={"product_name": "冒烟产品"})

    with patch.object(SubTaskExecutor, "execute_subtask", fake_execute):
        result = asyncio.run(DeerflowExecutor().run(node, ctx))
    return result, captured.get("intent")


@pytest.mark.parametrize("capability,expected_intent", sorted(_CAPABILITY_TO_INTENT.items()))
def test_capability_is_translated_before_reaching_deerflow(capability, expected_intent):
    """执行器必须先把能力名翻成 intent 再交给 DeerFlow。"""
    result, sent_intent = _run_node(capability)

    assert sent_intent == expected_intent
    assert result.status == "succeeded"
    assert result.error in (None, "")


def test_unknown_capability_falls_back_to_raw_name():
    """表外能力保留原名（走通用分支），不静默改语义。"""
    result, sent_intent = _run_node("brand.new_thing")

    assert sent_intent == "brand.new_thing"
    assert result.status == "succeeded"


def test_executor_declares_the_mapped_capabilities():
    """能力声明与映射表一致，planner 动态读取时才不会漏。"""
    declared = set(DeerflowExecutor.get_capabilities().keys())
    assert declared <= set(_CAPABILITY_TO_INTENT)
    assert "seo.optimize" in declared
