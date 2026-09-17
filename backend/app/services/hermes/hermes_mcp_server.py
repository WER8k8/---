# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Hermes MCP Server.
Exposes the internal TaskGraph (Plan-as-Data) generation and dispatch as an MCP tool
so that the outer DeepSeek Harness can call it when a structured multi-step process is needed.
"""
import logging
from typing import Dict, Any, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class GeneratePlanToolInput(BaseModel):
    tenant_id: str = Field(..., description="Tenant ID (multi-tenant isolation)")
    intent: str = Field(..., description="The highly specific business intent (e.g., 'site.build.seo', 'outreach.b2b')")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters extracted by Harness (e.g., {'target_region': 'middle_east'})")


class HermesMCPServer:
    """Acts as a bridge between MCP protocol and internal Hermes engine."""

    @classmethod
    def get_tool_manifest(cls) -> List[Dict[str, Any]]:
        return [
            {
                "name": "hermes_orchestrate",
                "description": "Generate and execute a multi-agent deterministic TaskGraph for complex B2B workflows.",
                "input_schema": GeneratePlanToolInput.model_json_schema()
            }
        ]

    @classmethod
    async def call_tool(cls, name: str, arguments: Dict[str, Any], db=None) -> Dict[str, Any]:
        """接真实拆解链：intent → decompose → TaskGraph，返回真实 plan_id。

        仅当传入 db（SQLAlchemy Session）时拆解并翻库；无 db 时如实返回 not_configured，
        绝不再返回硬编码假 plan_id（历史假桩已废弃）。
        """
        if name != "hermes_orchestrate":
            raise ValueError(f"Unknown Hermes MCP tool: {name}")

        def _flatten(value: Any) -> Any:
            if isinstance(value, BaseModel):
                return value.model_dump()
            return value

        tenant_id = str(arguments.get("tenant_id") or "")
        intent = str(arguments.get("intent") or "").strip()
        parameters = arguments.get("parameters") or {}
        if not tenant_id:
            raise ValueError("tenant_id 必填（多租户隔离红线）")
        if not intent:
            raise ValueError("intent 必填")

        if db is None:
            logger.info("Hermes MCP: 无 db，跳过拆解（仅返回配置状态）")
            return {"status": "not_configured", "plan_id": None,
                    "message": "Hermes MCP 需要 db 才能拆解意图"}

        from app.services.hermes.harness_gateway import HarnessGateway

        graph, source = await HarnessGateway(db).plan(
            tenant_id=tenant_id,
            channel=str(arguments.get("channel") or "mcp"),
            raw_text=intent,
            payload={k: _flatten(v) for k, v in parameters.items()},
        )
        logger.info("Hermes MCP: hermes_orchestrate → plan=%s source=%s nodes=%d",
                    graph.plan_id, source, len(graph.nodes))
        return {
            "status": "success",
            "plan_id": graph.plan_id,
            "graph_source": source,
            "node_count": len(graph.nodes),
        }
