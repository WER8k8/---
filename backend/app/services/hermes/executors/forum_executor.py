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

        # 出站论坛发布当前无真实通道：forum_webhook_service 仅为入站 webhook，
        # 无 post_to_forums 出站实现 → 如实 failed，待 P1 接真实发布通道。
        return ExecutorResult(
            node_id=node.id,
            status="failed",
            output={
                "executor": "forum",
                "capability": capability,
                "status": "not_wired",
                "error": "出站论坛发布未接线（无 post_to_forums 真实通道）",
                "title": title,
            },
            error="出站论坛发布未接线：no outbound forum publisher implemented",
        )

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
