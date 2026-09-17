# -*- coding: utf-8 -*-
"""WangcaiExecutor 契约回归测试（不连真库，H.5）。"""
from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from app.schemas.hermes_orchestration import TaskNode
from app.services.hermes.executors.base import ExecutorContext, ExecutorRegistry
from app.services.hermes.executors.wangcai_executor import WangcaiExecutor


def _ctx() -> ExecutorContext:
    return ExecutorContext(db=MagicMock(), tenant_id="tenant-1", plan_id="plan-1")


def _node(**inp) -> TaskNode:
    return TaskNode(id="n1", executor="wangcai", capability="wangcai.ask",
                    depends_on=[], input=inp)


def test_success_returns_wangcai_payload():
    """成功路径：真实 ask_wangcai_for_tenant 返回 dict，执行器透传字段。"""
    fake_reply = {
        "intent": "blue_ocean",
        "reply": "Top markets for insulation board...",
        "category_key": "insulation_board",
        "disclaimer": "public stats only",
        "language": "en",
        "wangcai_meta": {"engine": "wangcai-router-v1", "source": "hermes"},
    }
    with patch(
        "app.services.tenant_wangcai_service.ask_wangcai_for_tenant"
    ) as MockAsk:
        MockAsk.return_value = fake_reply
        result = asyncio.run(WangcaiExecutor().run(
            _node(message="哪些国家适合出口岩棉板？"), _ctx()))

    assert result.status == "succeeded"
    assert result.output["intent"] == "blue_ocean"
    assert result.output["category_key"] == "insulation_board"
    # 执行器必须走统一入口，且 source 落 hermes
    args = MockAsk.call_args
    assert args.kwargs.get("source") == "hermes"


def test_missing_message_fails():
    """缺 message 必须返回 failed，不静默成功。"""
    result = asyncio.run(WangcaiExecutor().run(_node(), _ctx()))
    assert result.status == "failed"
    assert "missing_message" in (result.error or "")


def test_tenant_missing_fails():
    """租户不存在 → failed tenant_missing。"""
    ctx = _ctx()
    ctx.db.query.return_value.filter.return_value.first.return_value = None
    result = asyncio.run(
        WangcaiExecutor().run(_node(message="岩棉板能出口美国吗？"), ctx))
    assert result.status == "failed"
    assert "tenant_missing" in (result.error or "")


def test_service_exception_returns_failed_not_raise():
    """底层异常不抛出，契约要求 failed + error。"""
    with patch(
        "app.services.tenant_wangcai_service.ask_wangcai_for_tenant"
    ) as MockAsk:
        MockAsk.side_effect = RuntimeError("db down")
        result = asyncio.run(
            WangcaiExecutor().run(_node(message="岩棉板能出口美国吗？"), _ctx()))
    assert result.status == "failed"
    assert "RuntimeError" in (result.error or "")


def test_wangcai_registered_in_registry_and_bridge():
    """执行器注册 + 桥 ROUTERS 收录 wangcai_intent（H.5 收口判定）。"""
    executor = ExecutorRegistry.get("wangcai")
    assert isinstance(executor, WangcaiExecutor)
    assert "wangcai.ask" in WangcaiExecutor.get_capabilities()

    from app.services.tasks.hermes_task_bridge import ROUTERS

    assert "wangcai_intent" in ROUTERS
