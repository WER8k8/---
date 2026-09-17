# -*- coding: utf-8 -*-
"""InquiryExecutor 契约回归测试（不连真库）。"""
from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from app.schemas.hermes_orchestration import TaskNode
from app.services.hermes.executors.base import ExecutorContext
from app.services.hermes.executors.inquiry_executor import InquiryExecutor


def _ctx() -> ExecutorContext:
    return ExecutorContext(db=MagicMock(), tenant_id="tenant-1", plan_id="plan-1")


def _node(**inp) -> TaskNode:
    return TaskNode(id="n1", executor="inquiry", capability="inquiry.capture",
                    depends_on=[], input=inp)


def test_success_returns_real_inquiry_id():
    """成功路径：真实 create_public_lead 返回 dict，执行器透传字段。"""
    fake_row = {"id": "inq-001", "name": "买家A", "message": "询价",
                "source_channel": "hermes", "status": "new"}
    with patch("app.services.inquiries_unified_service.InquiriesUnifiedService") as MockSvc:
        MockSvc.return_value.create_public_lead.return_value = fake_row
        result = asyncio.run(InquiryExecutor().run(
            _node(name="买家A", message="询价", email="a@b.com"), _ctx()))

    assert result.status == "succeeded"
    assert result.output["inquiry_id"] == "inq-001"
    assert result.output["source_channel"] == "hermes"


def test_missing_name_fails():
    """缺 name 必须返回 failed，不静默成功。"""
    result = asyncio.run(InquiryExecutor().run(_node(message="询价"), _ctx()))
    assert result.status == "failed"
    assert "missing_name" in (result.error or "")


def test_missing_message_fails():
    """缺 message 必须返回 failed。"""
    result = asyncio.run(InquiryExecutor().run(_node(name="买家A"), _ctx()))
    assert result.status == "failed"
    assert "missing_message" in (result.error or "")


def test_service_exception_returns_failed_not_raise():
    """底层异常不抛出，契约要求 failed + error。"""
    with patch("app.services.inquiries_unified_service.InquiriesUnifiedService") as MockSvc:
        MockSvc.return_value.create_public_lead.side_effect = RuntimeError("db down")
        result = asyncio.run(InquiryExecutor().run(
            _node(name="买家A", message="询价"), _ctx()))

    assert result.status == "failed"
    assert "RuntimeError" in (result.error or "")
