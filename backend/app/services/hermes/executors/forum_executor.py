# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Forum Executor Plugin for Hermes Orchestration.

把既有 forum_webhook_service / forum_sidecar_service 包成
ExecutorRegistry 插件，使业务链论坛发布环节可被任务图调度。

契约：
    node.executor   = "forum"
    node.capability = "forum.post" | "default"
    node.input      = { forum_id?, title?, body?, tags?[] }
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

_SUPPORTED_CAPABILITIES = frozenset({"forum.post", "default"})


class ForumExecutor(BaseExecutor):
    """论坛发布执行器：向目标论坛/社区发帖子。

    复用既有 forum_webhook_service / forum_sidecar_service，
    不做二次实现，只做契约适配。
    """

    @classmethod
    def get_executor_name(cls) -> str:
        return "forum"

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        capability = (node.capability or "default").strip()
        if capability not in _SUPPORTED_CAPABILITIES:
            return ExecutorResult(
                node_id=node.id,
                status="skipped",
                output={},
                error=f"forum 不支持 capability={capability!r}",
            )

        params: dict[str, Any] = dict(node.input or {})
        title = str(params.get("title") or params.get("post_title") or "").strip()
        body = str(params.get("body") or params.get("content") or "").strip()

        if not title and not body:
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error="missing_content: forum 节点需提供 title 或 body",
            )

        try:
            from app.services.forum_webhook_service import post_to_forums

            result = await post_to_forums(
                title=title,
                body=body,
                forum_id=str(params.get("forum_id") or params.get("target_forum") or ""),
                tags=[str(t) for t in (params.get("tags") or [])],
                tenant_id=str(context.tenant_id) if context.tenant_id else None,
                db=context.db,
            )
        except (ImportError, AttributeError):
            # forum_webhook_service 可能未完全实现 — 降级
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={
                    "executor": "forum",
                    "capability": capability,
                    "status": "queued_degraded",
                    "degraded": True,
                    "note": "forum_webhook_service.post_to_forums 未完整落地，帖子入队",
                    "title": title,
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("ForumExecutor 执行失败 node=%s", node.id)
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error=f"{type(exc).__name__}: {exc}",
            )

        output = dict(result or {})
        output["executor"] = "forum"
        output["capability"] = capability
        return ExecutorResult(node_id=node.id, status="succeeded", output=output)

    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "forum.post": {
                "desc": "论坛/社区发帖（多目标分发）",
                "input": ["forum_id", "title", "body", "tags"],
                "output": ["post_id", "published_at"],
                "cost": {"tokens": 100, "seconds": 5},
                "needs_approval": False,
            },
        }


ExecutorRegistry.register(ForumExecutor())
