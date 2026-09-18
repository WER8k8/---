# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Logistics Tracking Executor Plugin for Hermes Orchestration.

把既有 `fetch_tracking_payload` 包成 ExecutorRegistry 插件，
使业务链第 17 步（物流可查）可被任务图调度。

契约（见 docs/串联驱动设计-2026-09-10.md §3）：
    node.executor   = "logistics"
    node.capability = "logistics.track" | "default"
    node.input      = { tracking_number, carrier? }

设计纪律（对齐项目"不假交付"铁律）：
    · 失败一律返回 status="failed" 并带 error，不抛异常给调用方
    · 不静默吞异常（记录完整堆栈）
    · 结果中的 provider / demo 标记原样透出，不篡改降级路径
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

_SUPPORTED_CAPABILITIES = frozenset({"logistics.track", "default"})


class LogisticsExecutor(BaseExecutor):
    """物流轨迹查询执行器：真实调外部物流接口。"""

    @classmethod
    def get_executor_name(cls) -> str:
        return "logistics"

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        capability = (node.capability or "default").strip()
        if capability not in _SUPPORTED_CAPABILITIES:
            return ExecutorResult(
                node_id=node.id,
                status="skipped",
                output={},
                error=f"logistics 不支持 capability={capability!r}",
            )

        params: dict[str, Any] = dict(node.input or {})
        tracking_number = str(
            params.get("tracking_number")
            or params.get("trackingNumber")
            or ""
        ).strip()
        if not tracking_number:
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error="missing_tracking_number: 物流节点需提供 tracking_number",
            )

        carrier = params.get("carrier") or None

        try:
            from app.services.logistics_tracking_service import fetch_tracking_payload

            result = fetch_tracking_payload(
                tracking_number=tracking_number,
                carrier=carrier,
            )
        except Exception as exc:  # noqa: BLE001 — 契约要求失败返回而非抛出
            logger.exception("LogisticsExecutor 执行失败 node=%s", node.id)
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error=f"{type(exc).__name__}: {exc}",
            )

        output = dict(result or {})
        output["executor"] = self.get_executor_name()
        # 透出 provider / demo 标记，供上层判定是否"真交付"（不篡改）
        output.setdefault("simulated", bool(output.get("demo")))
        # 统一口径：物流源为 demo/simulated 属模拟交付 → 顶层如实 degraded，不伪装 succeeded
        status = "degraded" if output.get("simulated") else "succeeded"
        return ExecutorResult(node_id=node.id, status=status, output=output)

    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "logistics.track": {
                "desc": "物流轨迹查询（kuaidi100 / demo 降级）",
                "input": ["tracking_number", "carrier"],
                "output": ["events", "status", "estimated_delivery"],
                "cost": {"tokens": 0, "seconds": 3},
                "needs_approval": False,
            },
        }


ExecutorRegistry.register(LogisticsExecutor())
