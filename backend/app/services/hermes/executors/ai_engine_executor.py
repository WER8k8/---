# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""AI Engine Executor Plugin for Hermes Orchestration.

把既有 AI 能力层（DeepSeek Harness / ubrain / deerflow L1 路由）
包成统一的 ExecutorRegistry 插件，使 L3 执行层能调度任意 AI 推理任务。

契约：
    node.executor   = "ai_engine"
    node.capability = "ai.chat" | "ai.reason" | "default"
    node.input      = { prompt?, model?, temperature?, max_tokens? }
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

_SUPPORTED_CAPABILITIES = frozenset({"ai.chat", "ai.reason", "default"})


class AiEngineExecutor(BaseExecutor):
    """AI 引擎执行器：统一 LLM 推理入口。"""

    @classmethod
    def get_executor_name(cls) -> str:
        return "ai_engine"

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        capability = (node.capability or "default").strip()
        if capability not in _SUPPORTED_CAPABILITIES:
            return ExecutorResult(
                node_id=node.id,
                status="skipped",
                output={},
                error=f"ai_engine 不支持 capability={capability!r}",
            )

        params: dict[str, Any] = dict(node.input or {})
        # input_from 可能把上游字符串塞进 prompt/context
        raw_prompt = params.get("prompt") or params.get("text") or params.get("instruction") or params.get("message") or params.get("context")
        if isinstance(raw_prompt, dict):
            raw_prompt = raw_prompt.get("reply") or raw_prompt.get("text") or raw_prompt.get("message") or ""
        prompt = str(raw_prompt or "").strip()

        if not prompt:
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error="missing_prompt: ai_engine 节点需提供 prompt/text/instruction",
            )

        try:
            # 走 ubrain（统一助手层）作为 AI 入口；保证 message/prompt 均为字符串
            from app.services.hermes.executors.ubrain_executor import UbrainExecutor

            ubrain = UbrainExecutor()
            try:
                inp = dict(node.input or {})
            except Exception:
                inp = {}
            inp["message"] = prompt
            inp["prompt"] = prompt
            if hasattr(node, "model_copy"):
                node2 = node.model_copy(update={"input": inp})
            else:
                node2 = node
            result = await ubrain.run(node2, context)
            if result.status == "succeeded":
                output = dict(result.output or {})
                output["executor"] = "ai_engine"
                output["capability"] = capability
                return ExecutorResult(node_id=node.id, status="succeeded", output=output)
            return result
        except Exception as exc:  # noqa: BLE001
            logger.exception("AiEngineExecutor 执行失败 node=%s", node.id)
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=f"{type(exc).__name__}: {exc}")

    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "ai.chat": {
                "desc": "LLM 对话推理（统一入口，路由到 ubrain/deerflow）",
                "input": ["prompt", "model", "temperature"],
                "output": ["response", "model_used", "tokens"],
                "cost": {"tokens": 500, "seconds": 15},
                "needs_approval": False,
            },
            "ai.reason": {
                "desc": "多步推理（规划/分析/决策）",
                "input": ["prompt", "reasoning_depth"],
                "output": ["analysis", "steps", "conclusion"],
                "cost": {"tokens": 1000, "seconds": 30},
                "needs_approval": False,
            },
        }


ExecutorRegistry.register(AiEngineExecutor())
