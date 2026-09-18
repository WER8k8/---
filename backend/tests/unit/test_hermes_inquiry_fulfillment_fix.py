# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""履约询盘节点入参修复验证。"""
from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

from app.schemas.hermes_orchestration import IntentEvent, TaskNode
from app.services.hermes import planner_service as ps
from app.services.hermes.executors.base import ExecutorContext
from app.services.hermes.executors.inquiry_executor import InquiryExecutor


def test_fulfillment_graph_inquiry_input_has_name_message():
    g = ps._fulfillment_graph("p", "e", {"inquiry_id": "INQ-1", "country": "SA", "message": "need PI"})
    n1 = next(n for n in g.nodes if n.id == "n1")
    assert n1.executor == "inquiry"
    assert n1.input.get("name")
    assert n1.input.get("message")
    assert n1.input.get("source_channel")


def test_inquiry_executor_accepts_raw_text_fallback():
    ex = InquiryExecutor()
    ctx = ExecutorContext(db=None, tenant_id="demo", plan_id="p")
    node = TaskNode(
        id="i1",
        executor="inquiry",
        capability="inquiry.capture",
        input={"raw_text": "客户要 CIF 报价", "name": "", "email": "a@b.com"},
    )
    captured = {}

    class _Svc:
        def __init__(self, db):
            pass

        def create_public_lead(self, **kw):
            captured.update(kw)
            return {"id": "inq-ok", "subject": "x"}

    with patch("app.services.inquiries_unified_service.InquiriesUnifiedService", _Svc):
        res = asyncio.run(ex.run(node, ctx))
    assert res.status == "succeeded"
    assert res.output.get("inquiry_id") == "inq-ok"
    assert captured.get("name")
    assert "CIF" in (captured.get("message") or "")


def test_inquiry_executor_still_fails_without_any_message():
    ex = InquiryExecutor()
    ctx = ExecutorContext(db=None, tenant_id="demo", plan_id="p")
    node = TaskNode(id="i2", executor="inquiry", capability="inquiry.capture", input={})
    res = asyncio.run(ex.run(node, ctx))
    assert res.status == "failed"


def test_dispatch_route_injects_inquiry_name():
    # 确保 acquisition dispatch 仍会注入 name/message
    import inspect
    from app.api.v1.routes import acquisition as acq

    src = inspect.getsource(acq.acquisition_dispatch)
    assert "payload.setdefault" in src or "name" in src
