# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Agent Ops Executor — 代理业绩/知识检索深接。

    agent_ops.performance   代理业绩摘要（真 DB 可查则查，否则诚实）
    agent_ops.knowledge_q   知识检索（vector/search 路径，失败诚实）
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

_CAPS = {
    "agent_ops.performance": {
        "desc": "代理/业务员业绩摘要",
        "input": ["agent_id?", "tenant_id?"],
        "output": ["stats", "source"],
    },
    "agent_ops.knowledge_q": {
        "desc": "知识库检索",
        "input": ["query", "limit?"],
        "output": ["query", "hits", "source"],
    },
}


class AgentOpsExecutor(BaseExecutor):
    @classmethod
    def get_executor_name(cls) -> str:
        return "agent_ops"

    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return dict(_CAPS)

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        cap = (node.capability or "").strip()
        p = dict(node.input or {})
        try:
            if cap in ("agent_ops.performance", "default"):
                return self._performance(node, context, p)
            if cap == "agent_ops.knowledge_q":
                return self._knowledge(node, p)
            return ExecutorResult(node_id=node.id, status="skipped", output={}, error=f"unsupported {cap}")
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=str(exc)[:300])

    def _performance(self, node, context, p) -> ExecutorResult:
        if context.db is None:
            return ExecutorResult(node_id=node.id, status="failed", output={"source": "none"}, error="db_unavailable")
        try:
            from app.services.acquisition import ops_card_store
            from sqlalchemy import text

            agent = str(p.get("agent_id") or p.get("owner_user_id") or "")
            # 从跟单卡汇总业务员
            cards = list(ops_card_store._by_inquiry.values())
            if agent:
                cards = [c for c in cards if getattr(c, "owner_user_id", "") == agent]
            won = sum(1 for c in cards if getattr(c, "stage", "") == "won")
            lost = sum(1 for c in cards if getattr(c, "stage", "") == "lost")
            active = sum(1 for c in cards if getattr(c, "stage", "") not in ("won", "lost"))
            # 可选：代理佣金表
            commission = None
            try:
                commission = context.db.execute(
                    text("select count(*) from agent_commission_rules")
                ).scalar()
            except Exception:
                commission = None
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={
                    "agent_id": agent,
                    "stats": {
                        "cards": len(cards),
                        "won": won,
                        "lost": lost,
                        "active": active,
                        "commission_rules": commission,
                    },
                    "source": "ops_card_store+pg",
                    "executor": self.get_executor_name(),
                },
            )
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=str(exc))

    def _knowledge(self, node, p) -> ExecutorResult:
        q = str(p.get("query") or p.get("message") or "").strip()
        if not q:
            return ExecutorResult(node_id=node.id, status="failed", output={}, error="missing_query")
        limit = max(1, min(20, int(p.get("limit") or 5)))
        # 1) 本地知识队列关键词命中（真数据，非编造）
        hits = []
        try:
            from app.services.acquisition.knowledge_queue import knowledge_queue_store

            qlow = q.lower()
            for item in knowledge_queue_store.list():
                blob = f"{item.get('title','')} {item.get('plain','')} {item.get('category','')}".lower()
                if any(tok in blob for tok in qlow.split() if len(tok) >= 2):
                    hits.append({
                        "id": item.get("id"),
                        "title": item.get("title"),
                        "plain": item.get("plain"),
                        "source": "knowledge_queue",
                    })
        except Exception:
            pass
        # 2) 向量库可选（无则不编造）
        vec_hits = []
        try:
            from app.services.vector_search_service import search as vsearch  # type: ignore

            raw = vsearch(q, limit=limit)
            if isinstance(raw, list):
                vec_hits = raw[:limit]
        except Exception:
            vec_hits = []
        return ExecutorResult(
            node_id=node.id,
            status="succeeded",
            output={
                "query": q,
                "hits": (hits + vec_hits)[:limit],
                "local_count": len(hits),
                "vector_count": len(vec_hits),
                "source": "knowledge_queue" + ("+vector" if vec_hits else ""),
                "hint": "无向量命中时只报本地知识，不编造检索结果",
                "executor": self.get_executor_name(),
            },
        )


ExecutorRegistry.register(AgentOpsExecutor())
