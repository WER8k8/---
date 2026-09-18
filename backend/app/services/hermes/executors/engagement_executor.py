# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Engagement Executor Plugin for Hermes Orchestration.

把既有 aitoearn_engage_send_service（社媒互动/触达）包成
ExecutorRegistry 插件，使业务链社媒拓客互动环节可被任务图调度。

契约：
    node.executor   = "engagement"
    node.capability = "engagement.send" | "engagement.reply" | "default"
    node.input      = { channel?, target_id?, message?, action? }
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

_SUPPORTED_CAPABILITIES = frozenset({"engagement.send", "engagement.reply", "default"})


class EngagementExecutor(BaseExecutor):
    """社媒互动执行器：发送/回复触达消息。

    复用既有 aitoearn_engage_send_service（真实社媒发送），
    不做二次实现，只做契约适配。
    """

    @classmethod
    def get_executor_name(cls) -> str:
        return "engagement"

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        capability = (node.capability or "default").strip()
        if capability not in _SUPPORTED_CAPABILITIES:
            return ExecutorResult(
                node_id=node.id,
                status="skipped",
                output={},
                error=f"engagement 不支持 capability={capability!r}",
            )

        params: dict[str, Any] = dict(node.input or {})
        message = str(params.get("message") or params.get("text") or "").strip()

        if not message:
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error="missing_message: engagement 节点需提供 message/text",
            )

        try:
            # 真源当前仅支持「既有已批准互动上发送」(approve_and_send_via_aitoearn_sync)，
            # 与本节点「直发 message 给 target_id」契约不对齐。
            from app.services.aitoearn_engage_send_service import (  # noqa: F401
                approve_and_send_via_aitoearn_sync,
            )

            raise NotImplementedError(
                "engagement 直发契约未落地：真源需既有已批准互动（interaction_id），"
                "本节点为 channel/target_id 直发，待 P1 接真源统一"
            )
        except (ImportError, NotImplementedError, AttributeError) as exc:
            # 未接线 → 如实 failed，绝不伪装 queued/succeeded
            logger.warning("EngagementExecutor: 直发未接线，如实失败 %s", type(exc).__name__)
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={
                    "executor": "engagement",
                    "capability": capability,
                    "status": "not_wired",
                    "error": f"engagement 直发未接线: {type(exc).__name__}",
                },
                error=f"engagement 直发未接线: {exc}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("EngagementExecutor 执行失败 node=%s", node.id)
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error=f"{type(exc).__name__}: {exc}",
            )

    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "engagement.send": {
                "desc": "社媒触达发送（WhatsApp/LinkedIn 主动消息）",
                "input": ["channel", "target_id", "message"],
                "output": ["send_id", "delivery_status"],
                "cost": {"tokens": 200, "seconds": 5},
                "needs_approval": False,
            },
            "engagement.reply": {
                "desc": "回复已有会话线索",
                "input": ["channel", "target_id", "message", "thread_id"],
                "output": ["reply_id", "delivery_status"],
                "cost": {"tokens": 200, "seconds": 5},
                "needs_approval": False,
            },
        }


ExecutorRegistry.register(EngagementExecutor())
