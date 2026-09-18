# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Commerce Ops Executor — 商业链深接（真服务调用）。

契约：
    node.executor = "commerce_ops"
    capability:
      commerce_ops.email_enqueue      入队开发信（真 EmailQueueService）
      commerce_ops.followup_sequence  构建跟进序列（真 FollowUpEngine）
      commerce_ops.outreach_scan      到期 outreach 入队（真 acquisition_outreach）
      commerce_ops.crm_pipeline       询盘机会/管道统计（真 DB）
      commerce_ops.wallet_token       Token 余额（真账本）
      commerce_ops.acquisition_card   跟单卡摘要（真 ops_card_store）

纪律：失败 failed+error；不把 mock 当成功；人审外发不自动发送。
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

_CAPS = {
    "commerce_ops.email_enqueue": {
        "desc": "把开发信写入邮件队列（不等于已发送）",
        "input": ["to_email", "subject", "body", "tenant_id?"],
        "output": ["queue_id", "status"],
        "needs_approval": True,
    },
    "commerce_ops.followup_sequence": {
        "desc": "为线索构建跟进序列",
        "input": ["lead_id", "lead_email?", "lead_name?"],
        "output": ["lead_id", "stage", "attempts"],
        "needs_approval": False,
    },
    "commerce_ops.outreach_scan": {
        "desc": "扫描到期 draft outreach → queued",
        "input": ["limit?"],
        "output": ["queued", "job_ids"],
        "needs_approval": False,
    },
    "commerce_ops.crm_pipeline": {
        "desc": "CRM 商机统计（按阶段）",
        "input": ["tenant_id?"],
        "output": ["stats", "counts"],
        "needs_approval": False,
    },
    "commerce_ops.wallet_token": {
        "desc": "Token/钱包余额查询",
        "input": ["tenant_id?"],
        "output": ["balance", "status"],
        "needs_approval": False,
    },
    "commerce_ops.acquisition_card": {
        "desc": "获客跟单卡摘要/建卡",
        "input": ["inquiry_id", "tenant_id?"],
        "output": ["inquiry_id", "stage", "summary"],
        "needs_approval": False,
    },
}


class CommerceOpsExecutor(BaseExecutor):
    @classmethod
    def get_executor_name(cls) -> str:
        return "commerce_ops"

    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return dict(_CAPS)

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        cap = (node.capability or "").strip()
        params = dict(node.input or {})
        handlers = {
            "commerce_ops.email_enqueue": self._email_enqueue,
            "commerce_ops.followup_sequence": self._followup_sequence,
            "commerce_ops.outreach_scan": self._outreach_scan,
            "commerce_ops.crm_pipeline": self._crm_pipeline,
            "commerce_ops.wallet_token": self._wallet_token,
            "commerce_ops.acquisition_card": self._acquisition_card,
            "default": self._crm_pipeline,
        }
        fn = handlers.get(cap)
        if fn is None:
            return ExecutorResult(
                node_id=node.id,
                status="skipped",
                output={},
                error=f"commerce_ops 不支持 {cap!r}",
            )
        try:
            return await fn(node, context, params)
        except Exception as exc:  # noqa: BLE001
            logger.exception("commerce_ops failed cap=%s", cap)
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=str(exc)[:300])

    async def _email_enqueue(self, node, context, params) -> ExecutorResult:
        to = str(params.get("to_email") or "").strip()
        subject = str(params.get("subject") or "").strip()
        body = str(params.get("body") or "").strip()
        if not to or "@" not in to:
            return ExecutorResult(node_id=node.id, status="failed", output={}, error="missing/to_email invalid")
        if not subject:
            return ExecutorResult(node_id=node.id, status="failed", output={}, error="missing_subject")
        if not body:
            return ExecutorResult(node_id=node.id, status="failed", output={}, error="missing_body")
        # 人审闸：外发类默认只入队
        from app.services.acquisition.suppression_list import suppression_store
        allow = suppression_store.check_outreach(
            email=to,
            tenant_id=str(params.get("tenant_id") or context.tenant_id or "demo"),
            channel="email",
            mode="queued_draft",
        )
        if not allow.get("allowed", True):
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={"allowed": False, "code": allow.get("code")},
                error=allow.get("message") or "suppressed",
            )
        try:
            from app.services.ubrain.email_queue_service import EmailQueueService

            svc = EmailQueueService()
            item = await svc.enqueue(
                to_email=to,
                subject=subject,
                body=body,
                to_name=str(params.get("to_name") or ""),
                priority=int(params.get("priority") or 0),
                campaign_id=str(params.get("campaign_id") or ""),
                scheduled_at=str(params.get("scheduled_at") or ""),
                tenant_id=str(params.get("tenant_id") or context.tenant_id or ""),
            )
            status = getattr(item, "status", None)
            status_s = status.value if hasattr(status, "value") else str(status or "queued")
            qid = str(getattr(item, "id", None) or getattr(item, "email_id", "") or "")
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={
                    "queue_id": qid,
                    "status": status_s,
                    "executor": self.get_executor_name(),
                    "capability": "commerce_ops.email_enqueue",
                    "note": "已入队，发送需 worker/人审；非已送达",
                },
            )
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=f"email_enqueue: {exc}")

    async def _followup_sequence(self, node, context, params) -> ExecutorResult:
        lead_id = str(params.get("lead_id") or "").strip()
        if not lead_id:
            return ExecutorResult(node_id=node.id, status="failed", output={}, error="missing_lead_id")
        try:
            from app.services.ubrain.follow_up_engine import FollowUpEngine

            eng = FollowUpEngine()
            seq = eng.build_sequence(
                lead_id=lead_id,
                lead_email=str(params.get("lead_email") or ""),
                lead_name=str(params.get("lead_name") or ""),
                lead_company=str(params.get("lead_company") or ""),
                lead_context=params.get("lead_context") or None,
                max_attempts=int(params.get("max_attempts") or 5),
            )
            stage = getattr(seq, "current_stage", None)
            stage_s = stage.value if hasattr(stage, "value") else str(stage or "")
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={
                    "lead_id": lead_id,
                    "stage": stage_s,
                    "attempts": int(getattr(seq, "current_attempt", 0) or 0),
                    "executor": self.get_executor_name(),
                },
            )
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=f"followup: {exc}")

    async def _outreach_scan(self, node, context, params) -> ExecutorResult:
        if context.db is None:
            return ExecutorResult(node_id=node.id, status="failed", output={}, error="db_unavailable")
        try:
            from app.services.acquisition_outreach_service import enqueue_due_steps

            out = enqueue_due_steps(context.db, limit=int(params.get("limit") or 50))
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={
                    "queued": int(out.get("queued") or 0),
                    "job_ids": list(out.get("job_ids") or []),
                    "executor": self.get_executor_name(),
                },
            )
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=f"outreach_scan: {exc}")

    async def _crm_pipeline(self, node, context, params) -> ExecutorResult:
        if context.db is None:
            return ExecutorResult(node_id=node.id, status="failed", output={}, error="db_unavailable")
        try:
            from sqlalchemy import func
            from app.models.crm_opportunity import Opportunity  # type: ignore

            q = context.db.query(Opportunity)
            try:
                rows = q.with_entities(Opportunity.stage, func.count()).group_by(Opportunity.stage).all()
                stats = {str(s): int(c) for s, c in rows}
            except Exception:
                stats = {}
                try:
                    total = q.count()
                    stats = {"total": total}
                except Exception as exc2:  # noqa: BLE001
                    return ExecutorResult(node_id=node.id, status="failed", output={}, error=f"crm: {exc2}")
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={"stats": stats, "counts": stats, "executor": self.get_executor_name()},
            )
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=f"crm_pipeline: {exc}")

    async def _wallet_token(self, node, context, params) -> ExecutorResult:
        tenant = str(params.get("tenant_id") or context.tenant_id or "demo")
        try:
            from app.services.acquisition.wallet_guard import check_wallet_status

            w = check_wallet_status(tenant, db=context.db)
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={
                    "balance": w.get("token_balance"),
                    "status": w.get("status"),
                    "source": w.get("source"),
                    "hard_block_enabled": w.get("hard_block_enabled"),
                    "message": w.get("message"),
                    "executor": self.get_executor_name(),
                },
            )
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=f"wallet: {exc}")

    async def _acquisition_card(self, node, context, params) -> ExecutorResult:
        iid = str(params.get("inquiry_id") or "").strip()
        if not iid:
            return ExecutorResult(node_id=node.id, status="failed", output={}, error="missing_inquiry_id")
        try:
            from app.services.acquisition import ops_card_store

            tenant = str(params.get("tenant_id") or context.tenant_id or "demo")
            card = ops_card_store.get_by_inquiry(iid)
            if card is None:
                card = ops_card_store.materialize(tenant_id=tenant, inquiry_id=iid)
            summary = card.summary_lines()
            sd = card.score_display()
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={
                    "inquiry_id": iid,
                    "stage": card.stage,
                    "buyer_grade": card.buyer_grade,
                    "score_display": sd,
                    "summary": summary,
                    "executor": self.get_executor_name(),
                },
            )
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=f"acquisition_card: {exc}")


ExecutorRegistry.register(CommerceOpsExecutor())
