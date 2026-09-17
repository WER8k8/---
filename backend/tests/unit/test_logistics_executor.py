# -*- coding: utf-8 -*-
"""LogisticsExecutor 契约回归测试（不连真库）。"""
from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from app.schemas.hermes_orchestration import TaskNode
from app.services.hermes.executors.base import ExecutorContext
from app.services.hermes.executors.logistics_executor import LogisticsExecutor


def _ctx() -> ExecutorContext:
    return ExecutorContext(db=MagicMock(), tenant_id="tenant-1", plan_id="plan-1")


def _node(**inp) -> TaskNode:
    return TaskNode(id="n1", executor="logistics", capability="logistics.track",
                    depends_on=[], input=inp)


def test_success_returns_real_payload():
    """成功路径：真实 fetch_tracking_payload 返回 dict，执行器透传字段。"""
    fake_payload = {
        "tracking_number": "SF123456789",
        "carrier": "sf",
        "status": "in_transit",
        "events": [{"description": "揽收", "timestamp": "2024-01-01T00:00:00Z"}],
        "estimated_delivery": "2024-01-03T00:00:00Z",
        "demo": True,
        "provider": "demo",
    }
    with patch("app.services.logistics_tracking_service.fetch_tracking_payload") as mock_fn:
        mock_fn.return_value = fake_payload
        result = asyncio.run(LogisticsExecutor().run(
            _node(tracking_number="SF123456789", carrier="sf"), _ctx()))

    assert result.status == "succeeded"
    assert result.output["status"] == "in_transit"
    assert isinstance(result.output["events"], list)
    assert result.output["simulated"] is True


def test_missing_tracking_number_fails():
    """缺 tracking_number 必须返回 failed。"""
    result = asyncio.run(LogisticsExecutor().run(_node(), _ctx()))
    assert result.status == "failed"
    assert "missing_tracking_number" in (result.error or "")


def test_provider_exception_returns_failed_not_raise():
    """底层异常不抛出，契约要求 failed + error。"""
    with patch("app.services.logistics_tracking_service.fetch_tracking_payload") as mock_fn:
        mock_fn.side_effect = ConnectionError("kuaidi100 timeout")
        result = asyncio.run(LogisticsExecutor().run(
            _node(tracking_number="SF123456789"), _ctx()))

    assert result.status == "failed"
    assert "ConnectionError" in (result.error or "")
