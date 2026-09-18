# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Portal Ops Executor — 代理门户 / 媒体剪辑深接。

    portal_ops.agent_summary   代理仪表盘摘要（真 DB 可查则查）
    portal_ops.media_status    媒体工厂/剪辑引擎状态（未配置诚实）
    portal_ops.moss_version    Moss VL 版本状态
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

_CAPS = {
    "portal_ops.agent_summary": {
        "desc": "代理门户业绩摘要",
        "input": ["agent_id?", "tenant_id?"],
        "output": ["summary", "source"],
    },
    "portal_ops.media_status": {
        "desc": "媒体/剪辑服务可用性",
        "input": [],
        "output": ["status", "detail"],
    },
    "portal_ops.moss_version": {
        "desc": "Moss VL 版本状态",
        "input": [],
        "output": ["version", "ok"],
    },
}


class PortalOpsExecutor(BaseExecutor):
    @classmethod
    def get_executor_name(cls) -> str:
        return "portal_ops"

    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return dict(_CAPS)

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        cap = (node.capability or "").strip()
        p = dict(node.input or {})
        try:
            if cap in ("portal_ops.agent_summary", "default"):
                return self._agent_summary(node, context, p)
            if cap == "portal_ops.media_status":
                return self._media_status(node)
            if cap == "portal_ops.moss_version":
                return self._moss(node)
            return ExecutorResult(node_id=node.id, status="skipped", output={}, error=f"unsupported {cap}")
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=str(exc)[:300])

    def _agent_summary(self, node, context, p) -> ExecutorResult:
        # 复用 acquisition 跟单卡 + 佣金规则（与 agent_ops 呼应，门户视角）
        try:
            from app.services.acquisition import ops_card_store

            cards = list(ops_card_store._by_inquiry.values())
            agent = str(p.get("agent_id") or "")
            if agent:
                cards = [c for c in cards if getattr(c, "owner_user_id", "") == agent]
            won = [c for c in cards if getattr(c, "stage", "") == "won"]
            amount = sum(float(getattr(c, "won_amount", 0) or 0) for c in won)
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={
                    "summary": {
                        "cards": len(cards),
                        "won": len(won),
                        "won_amount": amount,
                        "lost": sum(1 for c in cards if getattr(c, "stage", "") == "lost"),
                    },
                    "agent_id": agent,
                    "source": "ops_card_store",
                    "note": "门户摘要来自跟单卡；真佣金报表待 finance 联调",
                    "executor": self.get_executor_name(),
                },
            )
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=str(exc))

    def _media_status(self, node) -> ExecutorResult:
        import os

        checks = {}
        # Media factory / video engine keys 诚实探测
        for key in ("AI_VIDEO_API_KEY", "WAN_VIDEO_API_KEY", "MOSS_VL_API_KEY", "MEDIA_FACTORY_ENABLED"):
            checks[key] = bool((os.getenv(key) or "").strip())
        configured = any(checks.values())
        return ExecutorResult(
            node_id=node.id,
            status="succeeded",
            output={
                "status": "configured" if configured else "not_configured",
                "detail": checks,
                "note": "未配置媒体 Key 时剪辑/成片节点应降级，不假装出片",
                "executor": self.get_executor_name(),
            },
        )

    def _moss(self, node) -> ExecutorResult:
        try:
            # Moss 路由内通常有状态函数；无则诚实 unknown
            from app.services.moss_vl_service import MossVLService  # type: ignore

            svc = MossVLService() if callable(MossVLService) else None
            ver = getattr(svc, "current_version", None) if svc else None
            if callable(ver):
                ver = ver()
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={
                    "version": ver if ver else "unknown",
                    "ok": True,
                    "executor": self.get_executor_name(),
                },
            )
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={"ok": False},
                error=f"moss: {exc}",
            )


ExecutorRegistry.register(PortalOpsExecutor())
