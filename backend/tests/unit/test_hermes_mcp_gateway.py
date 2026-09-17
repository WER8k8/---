# -*- coding: utf-8 -*-
"""Hermes MCP Server 串联修复测试（假桩已死：不再返回硬编码 plan_abc123）。"""
from __future__ import annotations

import asyncio

import pytest

from app.services.hermes.hermes_mcp_server import HermesMCPServer


def _call(*args, **kwargs):
    return asyncio.run(HermesMCPServer.call_tool(*args, **kwargs))


def test_call_tool_without_db_returns_not_configured():
    result = _call(
        "hermes_orchestrate",
        {"tenant_id": "t1", "intent": "generate_site", "parameters": {}},
        db=None,
    )
    assert result["status"] == "not_configured"
    assert result["plan_id"] is None
    assert "plan_abc123" not in str(result)


def test_call_tool_requires_tenant_id():
    with pytest.raises(ValueError, match="tenant_id"):
        _call("hermes_orchestrate", {"intent": "x"})


def test_call_tool_requires_intent():
    with pytest.raises(ValueError, match="intent"):
        _call("hermes_orchestrate", {"tenant_id": "t1", "intent": ""})


def test_unknown_tool_rejected():
    with pytest.raises(ValueError, match="Unknown Hermes MCP tool"):
        _call("no_such_tool", {})


def test_manifest_requires_tenant_id():
    schema = HermesMCPServer.get_tool_manifest()[0]["input_schema"]
    assert "tenant_id" in schema["required"]
