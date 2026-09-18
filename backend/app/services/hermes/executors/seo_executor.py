# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""SEO Executor Plugin for Hermes Orchestration.

把既有 SEO 服务（rank tracking / inclusion check / site audit）包成
ExecutorRegistry 插件，使业务链 SEO 环节可被任务图调度。

契约（对齐 inquiry_executor 模式）：
    node.executor   = "seo"
    node.capability = "seo.rank" | "seo.audit" | "seo.inclusion" | "default"

设计纪律：
    · 失败一律返回 status="failed" 并带 error，不抛异常给调用方
    · 不静默假成功——若底层是 mock/降级，output 中标记 degraded=True
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

_SUPPORTED_CAPABILITIES = frozenset({"seo.rank", "seo.audit", "seo.inclusion", "default"})


class SeoExecutor(BaseExecutor):
    """SEO 执行器：排名追踪 / 站点审计 / 收录检查。

    复用既有 seo services（seo_tasks / inclusion_check_service），
    不做二次实现，只做契约适配。
    """

    @classmethod
    def get_executor_name(cls) -> str:
        return "seo"

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        capability = (node.capability or "default").strip()
        if capability not in _SUPPORTED_CAPABILITIES:
            return ExecutorResult(
                node_id=node.id,
                status="skipped",
                output={},
                error=f"seo 不支持 capability={capability!r}",
            )

        params: dict[str, Any] = dict(node.input or {})

        if capability == "seo.rank" or capability == "default":
            return await self._exec_rank_check(node, params, context)
        elif capability == "seo.audit":
            return await self._exec_site_audit(node, params, context)
        elif capability == "seo.inclusion":
            return await self._exec_inclusion_check(node, params, context)

        return ExecutorResult(node_id=node.id, status="failed", output={}, error=f"unreachable capability={capability!r}")

    async def _exec_rank_check(
        self, node: TaskNode, params: dict[str, Any], context: ExecutorContext
    ) -> ExecutorResult:
        """Check keyword ranking for a tenant's target keywords."""
        keyword = str(params.get("keyword") or params.get("target_keyword") or "").strip()
        domain = str(params.get("domain") or params.get("site_domain") or "").strip()

        if not keyword:
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error="missing_keyword: seo.rank 节点需提供 keyword",
            )

        # 排名检查无同步实现（seo_rank_service 未落地），走真实 Celery 异步任务。
        # check_single_keyword_ranking 契约参数为 keyword_id，以节点提供的 keyword 传入。
        try:
            from app.tasks.seo_tasks import check_single_keyword_ranking

            task_result = check_single_keyword_ranking.delay(keyword_id=keyword)
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={
                    "executor": "seo",
                    "capability": "seo.rank",
                    "keyword": keyword,
                    "ranking_task_id": str(getattr(task_result, "id", "")),
                    "degraded": True,
                    "note": "排名检查已入队为 Celery 异步任务（非即时，结果异步回填）",
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("SeoExecutor seo.rank Celery 执行失败 node=%s", node.id)
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error=f"{type(exc).__name__}: {exc}",
            )

    async def _exec_site_audit(
        self, node: TaskNode, params: dict[str, Any], context: ExecutorContext
    ) -> ExecutorResult:
        """Run a site audit for the tenant's domain."""
        domain = str(params.get("domain") or params.get("site_domain") or "").strip()

        # 站点审计无同步实现（seo_audit_service 未落地），走真实 Celery 异步任务。
        # run_site_audit 契约参数为 url，以节点提供的 domain 传入。
        try:
            from app.tasks.seo_tasks import run_site_audit

            task_result = run_site_audit.delay(url=domain)
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={
                    "executor": "seo",
                    "capability": "seo.audit",
                    "domain": domain,
                    "audit_task_id": str(getattr(task_result, "id", "")),
                    "degraded": True,
                    "note": "站点审计已入队为 Celery 异步任务（非即时，结果异步回填）",
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("SeoExecutor seo.audit Celery 执行失败 node=%s", node.id)
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error=f"{type(exc).__name__}: {exc}",
            )

    async def _exec_inclusion_check(
        self, node: TaskNode, params: dict[str, Any], context: ExecutorContext
    ) -> ExecutorResult:
        """Check Google/Bing inclusion status for published content."""
        try:
            from app.services.seo.inclusion_check_service import inclusion_probe_status

            result = inclusion_probe_status()
        except Exception as exc:  # noqa: BLE001
            logger.exception("SeoExecutor seo.inclusion 执行失败 node=%s", node.id)
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error=f"{type(exc).__name__}: {exc}",
            )

        output = dict(result or {})
        output["executor"] = "seo"
        output["capability"] = "seo.inclusion"
        return ExecutorResult(node_id=node.id, status="succeeded", output=output)

    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "seo.rank": {
                "desc": "关键词排名追踪（租户 domain 在 Google/Bing 的 SERP 位次）",
                "input": ["keyword", "domain", "tenant_id"],
                "output": ["position", "url", "serp_snapshot"],
                "cost": {"tokens": 100, "seconds": 10},
                "needs_approval": False,
            },
            "seo.audit": {
                "desc": "站点 SEO 全量审计（meta/links/速度/schema）",
                "input": ["domain", "tenant_id"],
                "output": ["score", "issues", "recommendations"],
                "cost": {"tokens": 500, "seconds": 30},
                "needs_approval": False,
            },
            "seo.inclusion": {
                "desc": "收录状态探测（已发布内容是否在搜索引擎索引中）",
                "input": [],
                "output": ["included_count", "pending_count", "last_probe_at"],
                "cost": {"tokens": 0, "seconds": 5},
                "needs_approval": False,
            },
        }


ExecutorRegistry.register(SeoExecutor())
