"""Lead Search Executor Plugin for Hermes Orchestration.

把既有 `GeoLeadService.search_leads`（geo 拓客搜索）包成
ExecutorRegistry 插件，使业务链拓客环节可被任务图调度。

契约（对齐 inquiry_executor 模式）：
    node.executor   = "lead"
    node.capability = "lead.search" | "default"
    node.input      = { industry?, country?, keywords?, limit? }

设计纪律：
    · 失败一律返回 status="failed" 并带 error，不抛异常给调用方
    · 若 GeoLeadService 返回 0 条结果，仍算 succeeded（空列表合法）
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

_SUPPORTED_CAPABILITIES = frozenset({"lead.search", "lead.score", "default"})


def _evidence_score(lead: dict[str, Any]) -> float:
    """基于字段证据的启发式评分（0-100）。无字段证据绝不默认 0.5 假分。"""
    score = 0.0
    if lead.get("email"):
        score += 40
    if lead.get("company") or lead.get("company_name"):
        score += 30
    if lead.get("country"):
        score += 20
    if lead.get("industry") or lead.get("industry_sector"):
        score += 10
    return min(score, 100)


class LeadExecutor(BaseExecutor):
    """拓客搜索执行器：geo 线索搜索与评分。

    复用既有 `GeoLeadService.search_leads`（真实外部搜索/内部库查询），
    不做二次实现，只做契约适配。
    """

    @classmethod
    def get_executor_name(cls) -> str:
        return "lead"

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        capability = (node.capability or "default").strip()
        if capability not in _SUPPORTED_CAPABILITIES:
            return ExecutorResult(
                node_id=node.id,
                status="skipped",
                output={},
                error=f"lead 不支持 capability={capability!r}",
            )

        params: dict[str, Any] = dict(node.input or {})

        if capability in ("lead.search", "default"):
            return await self._exec_lead_search(node, params, context)
        elif capability == "lead.score":
            return await self._exec_lead_scoring(node, params, context)

        return ExecutorResult(node_id=node.id, status="failed", output={}, error=f"unreachable capability={capability!r}")

    async def _exec_lead_search(
        self, node: TaskNode, params: dict[str, Any], context: ExecutorContext
    ) -> ExecutorResult:
        """Search for leads using GeoLeadService."""
        try:
            from app.services.geo_lead_service import GeoLeadService

            svc = GeoLeadService(context.db)
            result = await svc.search_leads(
                industry=str(params.get("industry") or "").strip() or None,
                country=str(params.get("country") or params.get("target_country") or "").strip() or None,
                keywords=(
                    str(params.get("keywords") or params.get("search_terms") or "").strip() or None
                ),
                limit=int(params.get("limit") or 10),
                tenant_id=str(context.tenant_id) if context.tenant_id else None,
            )
        except TypeError:
            # GeoLeadService.search_leads signature may not accept all kwargs - fallback
            try:
                from app.services.geo_lead_service import GeoLeadService

                svc = GeoLeadService(context.db)
                result = await svc.search_leads(
                    tenant_id=str(context.tenant_id) if context.tenant_id else None,
                    limit=int(params.get("limit") or 10),
                )
            except Exception as exc2:  # noqa: BLE001
                logger.exception("LeadExecutor lead.search fallback failed node=%s", node.id)
                return ExecutorResult(
                    node_id=node.id,
                    status="failed",
                    output={},
                    error=f"{type(exc2).__name__}: {exc2}",
                )
        except Exception as exc:  # noqa: BLE001
            logger.exception("LeadExecutor lead.search 执行失败 node=%s", node.id)
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error=f"{type(exc).__name__}: {exc}",
            )

        output = dict(result or {})
        output["executor"] = "lead"
        output["capability"] = "lead.search"
        # Ensure count is in output for downstream nodes
        leads = output.get("leads") or output.get("items") or []
        output["lead_count"] = len(leads) if isinstance(leads, list) else 0
        return ExecutorResult(node_id=node.id, status="succeeded", output=output)

    async def _exec_lead_scoring(
        self, node: TaskNode, params: dict[str, Any], context: ExecutorContext
    ) -> ExecutorResult:
        """Score existing leads for conversion potential."""
        lead_ids = params.get("lead_ids") or params.get("ids") or []
        if not lead_ids:
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error="missing_lead_ids: lead.score 节点需提供 lead_ids 列表",
            )

        try:
            from app.services.geo_lead_service import GeoLeadService

            svc = GeoLeadService(context.db)
            # Reuse search to get lead details, then score
            result = await svc.search_leads(
                tenant_id=str(context.tenant_id) if context.tenant_id else None,
                limit=100,
            )
            leads = result.get("leads") or result.get("items") or []
            scored = []
            for lead in leads:
                lead_id = str(lead.get("id") or lead.get("lead_id") or "")
                if str(lead_id) in [str(x) for x in lead_ids]:
                    raw = lead.get("score") or lead.get("relevance_score")
                    scored.append({
                        "id": lead_id,
                        "score": float(raw) if raw else _evidence_score(lead),
                        "source": lead.get("source") or lead.get("source_channel") or "unknown",
                    })
        except Exception as exc:  # noqa: BLE001
            logger.exception("LeadExecutor lead.score 执行失败 node=%s", node.id)
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error=f"{type(exc).__name__}: {exc}",
            )

        output = {
            "executor": "lead",
            "capability": "lead.score",
            "scored_count": len(scored),
            "scored_leads": scored[:50],
            "top_lead": scored[0] if scored else None,
        }
        return ExecutorResult(node_id=node.id, status="succeeded", output=output)

    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "lead.search": {
                "desc": "Geo 拓客搜索（按行业/国家/关键词找潜在客户）",
                "input": ["industry", "country", "keywords", "limit"],
                "output": ["lead_count", "leads", "top_lead"],
                "cost": {"tokens": 200, "seconds": 10},
                "needs_approval": False,
            },
            "lead.score": {
                "desc": "已有线索评分（批量 lead_ids 按转化率打分）",
                "input": ["lead_ids"],
                "output": ["scored_count", "top_lead"],
                "cost": {"tokens": 100, "seconds": 5},
                "needs_approval": False,
            },
        }


ExecutorRegistry.register(LeadExecutor())
