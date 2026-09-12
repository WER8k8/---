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
            from app.services.hermes.research_brief_service import generate_brief

            result = generate_brief(
                topic=topic,
                depth=int(params.get("depth") or 3),
                tenant_id=str(context.tenant_id) if context.tenant_id else None,
                db=context.db,
            )
        except (ImportError, AttributeError):
            # 降级：生成空简报骨架（非假成功，明确标记）
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={
                    "executor": "research",
                    "capability": "research.brief",
                    "topic": topic,
                    "status": "brief_pending",
                    "degraded": True,
                    "note": "research_brief_service.generate_brief 未完整实现，返回空骨架",
                },
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

        try:
            from app.services.foreign_trade.customer_research_skill import research_customer

            result = research_customer(
                company_name=company,
                industry=str(params.get("industry") or "").strip() or None,
                db=context.db,
            )
        except (ImportError, AttributeError):
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={
                    "executor": "research",
                    "capability": "research.prospect",
                    "company": company,
                    "status": "research_pending",
                    "degraded": True,
                    "note": "customer_research_skill.research_customer 未完整落地",
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("ResearchExecutor research.prospect 执行失败 node=%s", node.id)
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error=f"{type(exc).__name__}: {exc}",
            )

        output = dict(result or {})
        output["executor"] = "research"
        output["capability"] = "research.prospect"
        return ExecutorResult(node_id=node.id, status="succeeded", output=output)

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
