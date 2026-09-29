# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""trade_ai_agent 执行器 —— **本项目的拓客能力域**（爱马仕原生直驱，无外桥）。

  · TradeAI = 优丁拓客（检索 / 触达 / 分类），不是第二套系统
  · 调度主权 Hermes；记录与真相写优丁 PG；**进程内直驱**
  · 无 Key / 无 SMTP → 诚实 failed，不伪造 sent
  · 双路径：技能批适配器（services/adapters/tradeai，可用时优先，诚实定级）
    优先，不可用时回落原生单发 —— 2026-09-27 实测确认技能批为**在用路径**，
    勿按"死链"删除（此前误判已撤销）。
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
            # 1) 技能批路径（auto_sender 等）：诚实定级（成功才 sent）
            skill_out = await self._run_outreach_skill(context, "auto_sender", params, artifact_kind="send")
            if skill_out is not None:
                status, output, error = skill_out
                return ExecutorResult(
                    node_id=node.id,
                    status=status,
                    output={**output, "executor": self.get_executor_name(), "capability": capability},
                    error=error,
                )
            # 2) 原生单发（无 Key 诚实 failed）
            phone = str(params.get("whatsapp") or params.get("to") or params.get("phone") or "")
            message = str(params.get("message") or params.get("body") or "")
            # 从 customers 提取第一个可用 phone
            if not phone:
                for c in params.get("customers") or []:
                    if isinstance(c, dict):
                        phone = str(c.get("whatsapp") or c.get("to") or c.get("phone") or "")
                        if phone:
                            if not message:
                                message = str(c.get("message") or c.get("body") or "")
                            break
            out = native.outreach_whatsapp(
                tenant_id=context.tenant_id,
                phone=phone,
                message=message,
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
            # 草稿技能：message_generator → succeeded 但 sent=False
            draft = await self._run_outreach_skill(context, "message_generator", params, artifact_kind="draft")
            if draft is not None:
                status, output, error = draft
                return ExecutorResult(
                    node_id=node.id,
                    status=status,
                    output={**output, "executor": self.get_executor_name(), "capability": capability},
                    error=error,
                )
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

    async def _run_outreach_skill(
        self,
        context: ExecutorContext,
        skill_name: str,
        params: dict[str, Any],
        *,
        artifact_kind: str,
    ) -> tuple[str, dict[str, Any], str | None] | None:
        """调用 tradeai 适配技能并诚实定级。

        返回 (status, output, error)；技能不可用时返回 None 走原生路径。
        发送类：只有真实发出 success_count>0 且非 dry_run 才 succeeded/sent=True。
        """
        try:
            from app.services.adapters import tradeai

            if not tradeai.is_available():
                return None
            orch = tradeai.tenant_orchestrator(getattr(context, "tenant_id", "") or "")
            skills = list(orch.list_skills() or [])
            skill = next((s for s in skills if getattr(s, "name", "") == skill_name), None)
            if skill is None:
                return None
            result = await skill.run(None)
            if not isinstance(result, dict):
                result = {}
        except Exception as exc:  # noqa: BLE001
            logger.warning("outreach skill %s failed: %s", skill_name, exc)
            return None

        if artifact_kind == "draft":
            body = result.get("body") or result.get("message") or ""
            ok = bool(body)
            return (
                "succeeded" if ok else "failed",
                {
                    "success": ok,
                    "native": False,
                    "artifact_kind": "draft",
                    "sent": False,
                    **result,
                },
                None if ok else "draft_empty",
            )

        results = list(result.get("results") or [])
        success = int(result.get("success_count") or 0)
        failed = int(result.get("failed_count") or 0)
        scheduled = int(result.get("scheduled_count") or 0)
        dry_run = bool(result.get("dry_run"))
        has_recipients = bool(params.get("customers") or params.get("recipients") or params.get("to"))

        if dry_run and success > 0:
            return (
                "degraded",
                {
                    "success": False,
                    "native": False,
                    "artifact_kind": artifact_kind,
                    "sent": False,
                    "success_count": success,
                    "failed_count": failed,
                    "scheduled_count": scheduled,
                    "dry_run": True,
                    "results": results,
                },
                "未真实发送（dry_run）；未伪造 sent",
            )
        if success > 0 and not dry_run:
            return (
                "succeeded",
                {
                    "success": True,
                    "native": False,
                    "artifact_kind": artifact_kind,
                    "sent": True,
                    "success_count": success,
                    "failed_count": failed,
                    "scheduled_count": scheduled,
                    "results": results,
                },
                None,
            )
        if not results and not has_recipients and success == 0 and failed == 0:
            return (
                "skipped",
                {
                    "success": False,
                    "native": False,
                    "artifact_kind": artifact_kind,
                    "sent": False,
                    "success_count": 0,
                    "failed_count": 0,
                    "results": results,
                },
                "未伪造 sent；无收件人/无发送动作",
            )
        return (
            "failed",
            {
                "success": False,
                "native": False,
                "artifact_kind": artifact_kind,
                "sent": False,
                "success_count": success,
                "failed_count": failed,
                "scheduled_count": scheduled,
                "results": results,
            },
            "未伪造 sent",
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
