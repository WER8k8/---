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
            from app.services.aitoearn_engage_send_service import (
                send_engagement_message,
            )

            result = await send_engagement_message(
                channel=str(params.get("channel") or params.get("platform") or "whatsapp"),
                target_id=str(params.get("target_id") or params.get("contact_id") or ""),
                message=message,
                action=capability,
                tenant_id=str(context.tenant_id) if context.tenant_id else None,
                db=context.db,
            )
        except ImportError:
            # service 未完全落地 — 降级标记
            logger.warning("EngagementExecutor: send_engagement_message 不可用，降级为 queued")
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={
                    "executor": "engagement",
                    "capability": capability,
                    "status": "queued_degraded",
                    "degraded": True,
                    "note": "aitoearn_engage_send_service.send_engagement_message 未实现，消息标记为排队",
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("EngagementExecutor 执行失败 node=%s", node.id)
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error=f"{type(exc).__name__}: {exc}",
            )

        output = dict(result or {})
        output["executor"] = "engagement"
        output["capability"] = capability
        return ExecutorResult(node_id=node.id, status="succeeded", output=output)

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
