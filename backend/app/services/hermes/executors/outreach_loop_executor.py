# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Outreach Loop Executor — 触达闭环闸门（背调 + 抑制 + 人审）。

    outreach_loop.gate   综合外发闸：背调深度 × 抑制名单 → 是否允许个性化
    outreach_loop.research 登记背调深度
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

_CAPS = {
    "outreach_loop.gate": {
        "desc": "外发前综合闸门（背调+抑制+审批）",
        "input": ["email?", "inquiry_id?", "research_level?", "mode?", "tenant_id?"],
        "output": ["allowed", "research", "suppression", "approval_required"],
        "needs_approval": True,
    },
    "outreach_loop.research": {
        "desc": "登记背调深度",
        "input": ["inquiry_id", "research_level", "note?"],
        "output": ["research_gate", "inquiry_id"],
        "needs_approval": False,
    },
}


class OutreachLoopExecutor(BaseExecutor):
    @classmethod
    def get_executor_name(cls) -> str:
        return "outreach_loop"

    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return dict(_CAPS)

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        cap = (node.capability or "").strip()
        p = dict(node.input or {})
        try:
            if cap in ("outreach_loop.gate", "default"):
                return self._gate(node, context, p)
            if cap == "outreach_loop.research":
                return self._research(node, p)
            return ExecutorResult(node_id=node.id, status="skipped", output={}, error=f"unsupported {cap}")
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=str(exc)[:300])

    def _gate(self, node, context, p) -> ExecutorResult:
        try:
            from app.services.acquisition import ops_card_store
            from app.services.acquisition.outreach_gate import evaluate_research_gate
            from app.services.acquisition.suppression_list import suppression_store

            iid = str(p.get("inquiry_id") or "")
            email = str(p.get("email") or "")
            tenant = str(p.get("tenant_id") or context.tenant_id or "demo")
            level = str(p.get("research_level") or "")
            if not level and iid:
                card = ops_card_store.get_by_inquiry(iid)
                if card is not None:
                    level = card.research_level or "none"
            gate = evaluate_research_gate(level or "none")
            supp = {"allowed": True, "code": "ok", "message": "未在抑制名单"}
            if email:
                supp = suppression_store.check_outreach(
                    email=email,
                    tenant_id=tenant,
                    channel=str(p.get("channel") or "email"),
                    mode=str(p.get("mode") or "personalized"),
                )
            allowed = bool(gate.get("personalized_allowed")) and bool(supp.get("allowed", True))
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={
                    "allowed": allowed,
                    "personalized_allowed": gate.get("personalized_allowed"),
                    "research": gate,
                    "suppression": supp,
                    "approval_required": True,  # 外发人审红线
                    "plain": (
                        "可通过个性化闸（仍须人审发送）"
                        if allowed
                        else (supp.get("message") if not supp.get("allowed", True) else gate.get("reason"))
                    ),
                    "executor": self.get_executor_name(),
                },
            )
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=f"gate: {exc}")

    def _research(self, node, p) -> ExecutorResult:
        iid = str(p.get("inquiry_id") or "").strip()
        level = str(p.get("research_level") or "none").strip()
        if not iid:
            return ExecutorResult(node_id=node.id, status="failed", output={}, error="missing_inquiry_id")
        try:
            from app.services.acquisition import ops_card_store

            card = ops_card_store.set_research_level(iid, level, note=str(p.get("note") or ""))
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={
                    "inquiry_id": iid,
                    "research_gate": card.research_gate_view(),
                    "executor": self.get_executor_name(),
                },
            )
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=str(exc))


ExecutorRegistry.register(OutreachLoopExecutor())
