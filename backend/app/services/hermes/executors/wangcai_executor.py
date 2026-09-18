# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Wangcai Executor Plugin for Hermes Orchestration.

把既有旺财统一入口 `ask_wangcai_for_tenant`（公开站海关/出口问答，
router v1 知识管线 + 旧引擎降级）包成 ExecutorRegistry 插件，
使旺财能力可被任务图（DAG）调度，并经 ai_tasks 任务面派发。
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)


class WangcaiExecutor(BaseExecutor):
    """旺财贸易问答执行器。

    复用 `tenant_wangcai_service.ask_wangcai_for_tenant()`（唯一旺财调用点，
    已含 router v1 + 零回归降级），不做二次实现，只做契约适配。
    """

    @classmethod
    def get_executor_name(cls) -> str:
        return "wangcai"

    @staticmethod
    def _load_tenant(context: ExecutorContext) -> Optional[Any]:
        from app.models.tenant import Tenant

        try:
            return context.db.query(Tenant).filter(Tenant.id == context.tenant_id).first()
        except Exception:  # noqa: BLE001 - 查询异常按租户缺失处理，契约不抛错
            return None

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        params: dict[str, Any] = dict(node.input or {})
        message = str(params.get("message") or params.get("prompt") or "").strip()
        if not message:
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error="missing_message: wangcai 节点需提供 message",
            )

        tenant = self._load_tenant(context)
        if tenant is None:
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error=f"tenant_missing: 租户 {context.tenant_id} 不存在",
            )

        try:
            from app.services.tenant_wangcai_service import ask_wangcai_for_tenant

            data = ask_wangcai_for_tenant(
                context.db,
                tenant,
                message,
                source=str(params.get("source") or "hermes"),
                product_hint_override=params.get("product_hint"),
                language=params.get("language"),
            )
        except Exception as exc:  # noqa: BLE001 - contract requires return not raise
            logger.exception("WangcaiExecutor 执行失败 node=%s", node.id)
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
                error=f"ask_wangcai_for_tenant 返回类型异常: {type(data).__name__}",
            )

        out_data = dict(data)
        out_data.setdefault("answer", out_data.get("reply", ""))
        return ExecutorResult(
            node_id=node.id,
            status="succeeded",
            output=out_data,
        )

    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "wangcai.ask": {
                "desc": "旺财贸易问答：海关数据 / 出口可行性 / 蓝海市场 / HS 章节",
                "input": ["message", "prompt", "product_hint", "language", "source"],
                "output": [
                    "intent",
                    "reply",
                    "answer",
                    "category_key",
                    "tool_result",
                    "disclaimer",
                    "wangcai_meta",
                ],
                "cost": {"tokens": 500, "seconds": 10},
                "needs_approval": False,
            },
        }


ExecutorRegistry.register(WangcaiExecutor())
