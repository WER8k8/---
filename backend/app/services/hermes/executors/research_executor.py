# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Research Executor Plugin for Hermes Orchestration.

把既有 hermes/research_brief_service + foreign_trade/customer_research_skill
包成 ExecutorRegistry 插件，使业务链深度研析环节可被任务图调度。

契约：
    node.executor   = "research"
    node.capability = "research.brief" | "research.prospect" | "default"
    node.input      = { topic?, company?, industry?, depth? }
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

_SUPPORTED_CAPABILITIES = frozenset({"research.brief", "research.prospect", "default"})


class ResearchExecutor(BaseExecutor):
    """深度研析执行器：市场简报 / 竞品拓客研究。

    复用既有 research_brief_service（市场简报）与 customer_research_skill（拓客研究），
    不做二次实现，只做契约适配。
    """

    @classmethod
    def get_executor_name(cls) -> str:
        return "research"

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        capability = (node.capability or "default").strip()
        if capability not in _SUPPORTED_CAPABILITIES:
            return ExecutorResult(
                node_id=node.id,
                status="skipped",
                output={},
                error=f"research 不支持 capability={capability!r}",
            )

        params: dict[str, Any] = dict(node.input or {})

        if capability in ("research.brief", "default"):
            return self._exec_research_brief(node, params, context)
        elif capability == "research.prospect":
            return self._exec_prospect_research(node, params, context)

        return ExecutorResult(node_id=node.id, status="failed", output={}, error=f"unreachable capability={capability!r}")

    def _exec_research_brief(
        self, node: TaskNode, params: dict[str, Any], context: ExecutorContext
    ) -> ExecutorResult:
        """Generate a market research brief."""
        topic = str(params.get("topic") or params.get("industry") or params.get("keyword") or "").strip()
        if not topic:
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error="missing_topic: research.brief 节点需提供 topic/industry/keyword",
            )

        try:
            from app.services.hermes.research_brief_service import (
                compose_research_brief,
            )

            result = compose_research_brief(
                context.db,
                topic={"key": topic, "label": topic, "lane": "GW-R"},
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("ResearchExecutor research.brief 执行失败 node=%s", node.id)
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error=f"{type(exc).__name__}: {exc}",
            )

        output = dict(result or {})
        output["executor"] = "research"
        output["capability"] = "research.brief"
        output["topic"] = topic
        output["depth"] = int(params.get("depth") or 3)
        return ExecutorResult(node_id=node.id, status="succeeded", output=output)

    def _exec_prospect_research(
        self, node: TaskNode, params: dict[str, Any], context: ExecutorContext
    ) -> ExecutorResult:
        """Prospect research: customer/company due diligence."""
        company = str(params.get("company") or params.get("target_company") or "").strip()
        if not company:
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error="missing_company: research.prospect 节点需提供 company/target_company",
            )

        # customer_research_skill 仅为 SKILL 提示模板（registry），无 research_customer
        # Python 执行函数；prospect 调研需 LLM 真源执行技能 → 未接线时如实 failed。
        return ExecutorResult(
            node_id=node.id,
            status="failed",
            output={
                "executor": "research",
                "capability": "research.prospect",
                "company": company,
                "status": "not_wired",
                "error": "prospect 调研需 LLM 真源执行 customer_research 技能，未接线",
            },
            error="research.prospect 未接线：customer_research_skill 为提示模板，无执行函数，待 P1 接 LLM 真源",
        )

    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "research.brief": {
                "desc": "市场研析简报（行业趋势/竞品/关键词机会）",
                "input": ["topic", "industry", "depth"],
                "output": ["summary", "keywords", "competitors"],
                "cost": {"tokens": 500, "seconds": 15},
                "needs_approval": False,
            },
            "research.prospect": {
                "desc": "拓客深研（目标公司尽调/市场定位/联系策略）",
                "input": ["company", "industry", "country"],
                "output": ["profile", "fit_score", "contact_strategy"],
                "cost": {"tokens": 300, "seconds": 10},
                "needs_approval": False,
            },
        }


ExecutorRegistry.register(ResearchExecutor())
