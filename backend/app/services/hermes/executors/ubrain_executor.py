# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""UBrain Executor Plugin for Hermes Orchestration.

把既有 `ubrain_orchestrator.chat` 包成 ExecutorRegistry 插件，
使 UBrain 的自然语言助手能力可被任务图（DAG）调度。
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)


class UbrainExecutor(BaseExecutor):
    """UBrain 统一助手执行器。

    复用 `ubrain_orchestrator.chat()`（已有意图分发逻辑），
    不做二次实现，只做契约适配。
    """

    @classmethod
    def get_executor_name(cls) -> str:
        return "ubrain"

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        params: dict[str, Any] = dict(node.input or {})
        message = str(params.get("message") or params.get("prompt") or "").strip()
        if not message:
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error="missing_message: ubrain 节点需提供 message",
            )

        try:
            from app.services.ubrain.orchestrator import ubrain_orchestrator

            data = ubrain_orchestrator.chat(
                message,
                db=context.db,
                tenant_id=str(context.tenant_id) if context.tenant_id else None,
                context=params.get("context") or {},
            )
        except Exception as exc:  # noqa: BLE001 - contract requires return not raise
            logger.exception("UbrainExecutor 执行失败 node=%s", node.id)
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error=f"{type(exc).__name__}: {exc}",
            )

        if not isinstance(data, dict):
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error=f"ubrain.chat 返回类型异常: {type(data).__name__}",
            )

        return ExecutorResult(
            node_id=node.id,
            status="succeeded",
            output=dict(data),
        )

    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "ubrain.chat": {
                "desc": "UBrain 统一助手：意图检测与内部工具执行",
                "input": ["message", "prompt", "context"],
                "output": ["intent", "reply", "tool_result", "needs_confirmation"],
                "cost": {"tokens": 2000, "seconds": 30},
                "needs_approval": False,
            },
        }


ExecutorRegistry.register(UbrainExecutor())
