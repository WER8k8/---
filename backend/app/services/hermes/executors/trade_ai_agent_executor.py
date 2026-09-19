# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""trade_ai_agent 执行器 —— **本项目的拓客能力域**（爱马仕原生直驱，无外桥）。

  · TradeAI = 优丁拓客（检索 / 触达 / 分类），不是第二套系统
  · 调度主权 Hermes；记录与真相写优丁 PG；**进程内直驱**
  · 无 Key / 无 SMTP → 诚实 failed，不伪造 sent
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

_CAPS = frozenset({
    "prospect.scrape", "prospect_search", "scrape_prospects",
    "prospect.enrich", "scraper", "prospecting", "lead-research-assistant", "data_cleaner",
    "outreach.whatsapp", "whatsapp_send", "auto_sender", "social",
    "outreach.email", "email_campaign", "cold_email", "emails",
    "inbox.classify", "intent_classify", "ai_reply", "rag",
})


class TradeAiAgentExecutor(BaseExecutor):
    """优丁拓客执行器：native_acquisition → 优丁 PG。"""

    @classmethod
    def get_executor_name(cls) -> str:
        return "trade_ai_agent"

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        capability = (node.capability or "").lower().strip()
        for prefix in ("trade_ai.", "tradeai."):
            if capability.startswith(prefix):
                capability = capability.split(".", 1)[1]
        params: dict[str, Any] = dict(node.input or {})

        if capability not in _CAPS:
            return ExecutorResult(
                node_id=node.id,
                status="skipped",
                output={"capability": capability},
                error=f"trade_ai_agent 不支持 capability={capability!r}；能力集={sorted(_CAPS)}",
            )

        from app.services.tradeai import native_acquisition as native
        db = context.db

        if capability in ("prospect.scrape", "prospect_search", "scrape_prospects", "prospect.enrich", "scraper", "prospecting", "lead-research-assistant", "data_cleaner"):
            out = native.prospect_scrape(
                tenant_id=context.tenant_id,
                keyword=str(params.get("keyword") or params.get("q") or ""),
                country=params.get("country"),
                limit=int(params.get("limit") or 20),
                db=db,
                params=params,
            )
            return ExecutorResult(
                node_id=node.id,
                status="succeeded" if out.get("success") else "failed",
                output={**out, "executor": self.get_executor_name(), "capability": capability},
                error=None if out.get("success") else str(out.get("error") or "native_prospect_failed"),
            )

        if capability in ("outreach.whatsapp", "whatsapp_send", "auto_sender", "social"):
            out = native.outreach_whatsapp(
                tenant_id=context.tenant_id,
                phone=str(params.get("whatsapp") or params.get("to") or params.get("phone") or ""),
                message=str(params.get("message") or params.get("body") or ""),
                template_id=params.get("template_id"),
                inquiry_id=str(params.get("inquiry_id") or "") or None,
                lead_id=str(params.get("lead_id") or "") or None,
                db=db,
                params=params,
            )
            return ExecutorResult(
                node_id=node.id,
                status="succeeded" if out.get("success") else "failed",
                output={**out, "executor": self.get_executor_name(), "capability": capability},
                error=None if out.get("success") else str(out.get("error") or "native_whatsapp_failed"),
            )

        if capability in ("outreach.email", "email_campaign", "cold_email", "emails"):
            out = native.outreach_email(
                tenant_id=context.tenant_id,
                to_email=str(params.get("email") or params.get("to") or ""),
                subject=str(params.get("subject") or ""),
                body=str(params.get("body") or params.get("message") or ""),
                inquiry_id=str(params.get("inquiry_id") or "") or None,
                lead_id=str(params.get("lead_id") or "") or None,
                db=db,
                params=params,
            )
            return ExecutorResult(
                node_id=node.id,
                status="succeeded" if out.get("success") else "failed",
                output={**out, "executor": self.get_executor_name(), "capability": capability},
                error=None if out.get("success") else str(out.get("error") or "native_email_failed"),
            )

        out = native.classify_inbox(
            tenant_id=context.tenant_id,
            message=str(params.get("message") or params.get("content") or ""),
            db=db,
            params=params,
        )
        return ExecutorResult(
            node_id=node.id,
            status="succeeded" if out.get("success") else "failed",
            output={**out, "executor": self.get_executor_name(), "capability": capability},
            error=None if out.get("success") else str(out.get("error") or "native_classify_failed"),
        )

    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "prospect.scrape": {
                "desc": "拓客检索（优丁 prospect_leads/inquiries；外挖无引擎诚实失败）",
                "input": ["keyword", "country", "limit"],
                "output": ["prospects", "hit_count", "source"],
                "cost": {"tokens": 0, "seconds": 3},
                "needs_approval": False,
            },
            "outreach.whatsapp": {
                "desc": "WhatsApp 触达（优丁 WA + PG；无 Key 诚实 failed）",
                "input": ["whatsapp", "message", "template_id"],
                "output": ["success", "status", "persisted"],
                "cost": {"tokens": 0, "seconds": 8},
                "needs_approval": True,
            },
            "outreach.email": {
                "desc": "邮件触达（优丁 SMTP + contact_events；无 SMTP 诚实 failed）",
                "input": ["email", "subject", "body"],
                "output": ["success", "email_status"],
                "cost": {"tokens": 0, "seconds": 10},
                "needs_approval": True,
            },
            "inbox.classify": {
                "desc": "收件箱/询盘意图分类（优丁规则真源）",
                "input": ["message"],
                "output": ["detected_intent", "priority_tier"],
                "cost": {"tokens": 0, "seconds": 1},
                "needs_approval": False,
            },
        }


ExecutorRegistry.register(TradeAiAgentExecutor())
