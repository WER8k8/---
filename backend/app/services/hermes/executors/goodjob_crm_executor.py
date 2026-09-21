# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""goodjob_crm 执行器 —— **本项目的 CRM**（爱马仕原生直驱，无外桥）。

  · goodjob_crm = 优丁 CRM（单证 / 履约 / 线索 / 商机）
  · TradeAI     = 优丁拓客（同理）
  · 调度主权 Hermes；数据真相优丁 PG；**进程内直驱，无 HTTP 桥**
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

_CAPS = frozenset({
    "trade.docs",
    "document.generate_pi", "generate_pi", "pi_generator",
    "document.generate_trade_docs", "trade_document.generate",
    "crm.sync_stage", "sync_stage",
    "crm.sync_lead", "sync_lead",
    "crm.update_opportunity", "update_opportunity",
})

_CAP_DEFAULT_DOCTYPE = {
    "trade.docs": "PI",
    "document.generate_pi": "PI",
    "generate_pi": "PI",
    "pi_generator": "PI",
    "document.generate_trade_docs": "CI",
    "trade_document.generate": "CI",
}


class GoodJobCrmExecutor(BaseExecutor):
    """优丁 CRM 执行器：单证 + 履约 + 线索/商机（native_fulfillment → PG）。"""

    @classmethod
    def get_executor_name(cls) -> str:
        return "goodjob_crm"

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        capability = (node.capability or "").lower().strip()
        if capability.startswith("goodjob."):
            capability = capability.split(".", 1)[1]
        params: dict[str, Any] = dict(node.input or {})

        if capability not in _CAPS:
            return ExecutorResult(
                node_id=node.id,
                status="skipped",
                output={"capability": capability},
                error=f"goodjob_crm 不支持 capability={capability!r}；能力集={sorted(_CAPS)}",
            )

        from app.services.goodjob import native_fulfillment as native
        db = context.db

        if capability in ("crm.sync_stage", "sync_stage"):
            order_id = str(
                params.get("order_id") or params.get("order") or params.get("inquiry_id") or ""
            ).strip()
            stage = str(params.get("stage") or "deposit_received").strip()
            step_number = int(params.get("step_number") or 1)
            out = native.sync_fulfillment_stage(
                tenant_id=context.tenant_id,
                order_id=order_id or None,
                stage=stage,
                step_number=step_number,
                params=params,
                db=db,
            )
            return ExecutorResult(
                node_id=node.id,
                status="succeeded" if out.get("success") else "failed",
                output={**out, "executor": self.get_executor_name(), "capability": capability},
                error=None if out.get("success") else str(out.get("error") or "native_stage_failed"),
            )

        if capability in ("crm.sync_lead", "sync_lead"):
            lead = {
                "company_name": params.get("company_name") or params.get("company"),
                "contact_name": params.get("contact_name") or params.get("name"),
                "email": params.get("email"),
                "phone": params.get("phone"),
                "country": params.get("country"),
                "source": params.get("source") or "hermes_goodjob_crm",
                "inquiry_id": params.get("inquiry_id"),
                "product": params.get("product"),
                "message": params.get("message"),
            }
            out = native.sync_lead(tenant_id=context.tenant_id, lead_data=lead, db=db)
            return ExecutorResult(
                node_id=node.id,
                status="succeeded" if out.get("success") else "failed",
                output={**out, "executor": self.get_executor_name(), "capability": capability},
                error=None if out.get("success") else str(out.get("error") or "native_lead_failed"),
            )

        if capability in ("crm.update_opportunity", "update_opportunity"):
            out = native.update_opportunity(
                opportunity_id=str(params.get("opportunity_id") or params.get("lead_id") or "").strip(),
                status=str(params.get("status") or "").strip(),
                tenant_id=context.tenant_id,
                db=db,
            )
            return ExecutorResult(
                node_id=node.id,
                status="succeeded" if out.get("success") else "failed",
                output={**out, "executor": self.get_executor_name(), "capability": capability},
                error=None if out.get("success") else str(out.get("error") or "native_opp_failed"),
            )

        doc_type = str(params.get("doc_type") or _CAP_DEFAULT_DOCTYPE.get(capability, "PI")).upper()
        out = native.generate_trade_document(
            doc_type=doc_type,
            tenant_id=context.tenant_id,
            params=params,
            db=db,
            order_id=str(params.get("order_id") or params.get("order") or "").strip() or None,
            inquiry_id=str(params.get("inquiry_id") or params.get("inquiry") or "").strip() or None,
        )
        status = "succeeded" if out.get("success") else "failed"
        if out.get("success") and out.get("bank_configured") is False:
            status = "degraded"
        return ExecutorResult(
            node_id=node.id,
            status=status,
            output={**out, "executor": self.get_executor_name(), "capability": capability},
            error=None if out.get("success") else str(out.get("error") or "native_document_failed"),
        )

    async def sync_lead_to_crm(self, lead_data: dict[str, Any], db: Any = None) -> dict[str, Any]:
        from app.services.goodjob import native_fulfillment as native
        session = db
        close_after = False
        if session is None:
            from app.core.database import SessionLocal
            session = SessionLocal()
            close_after = True
        try:
            return native.sync_lead(tenant_id=lead_data.get("tenant_id"), lead_data=lead_data, db=session)
        finally:
            if close_after:
                session.close()

    async def update_opportunity_status(self, opportunity_id: str, status: str, db: Any = None) -> dict[str, Any]:
        from app.services.goodjob import native_fulfillment as native
        session = db
        close_after = False
        if session is None:
            from app.core.database import SessionLocal
            session = SessionLocal()
            close_after = True
        try:
            return native.update_opportunity(opportunity_id=opportunity_id, status=status, db=session)
        finally:
            if close_after:
                session.close()

    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "trade.docs": {
                "desc": "外贸单证（本项目 CRM 原生：PI/CI/PL → 优丁 PG）",
                "input": ["doc_type", "items", "inquiry_id", "order_id"],
                "output": ["doc_type", "doc_no", "document", "invoice_persisted"],
                "cost": {"tokens": 0, "seconds": 3},
                "needs_approval": True,
            },
            "document.generate_pi": {
                "desc": "形式发票 PI（爱马仕直驱原生套打；账户未配置不编造银行号）",
                "input": ["product_name", "quantity", "unit_price", "buyer_name", "order_id"],
                "output": ["pi_number", "doc_no", "document", "bank_configured"],
                "cost": {"tokens": 0, "seconds": 3},
                "needs_approval": True,
            },
            "document.generate_trade_docs": {
                "desc": "发运单证 CI/PL（原生；写 invoices）",
                "input": ["doc_type", "items", "order_id", "bl_number"],
                "output": ["doc_type", "doc_no", "document"],
                "cost": {"tokens": 0, "seconds": 3},
                "needs_approval": True,
            },
            "crm.sync_stage": {
                "desc": "7 步履约阶段推进（orders 状态机 + 管线/触点，无外桥）",
                "input": ["order_id", "stage", "step_number"],
                "output": ["success", "status", "order_number", "pipeline"],
                "cost": {"tokens": 0, "seconds": 2},
                "needs_approval": False,
            },
            "crm.sync_lead": {
                "desc": "线索建档（inquiries + opportunities，本项目 CRM）",
                "input": ["company_name", "contact_name", "email"],
                "output": ["lead_id", "inquiry_id", "success"],
                "cost": {"tokens": 0, "seconds": 2},
                "needs_approval": False,
            },
            "crm.update_opportunity": {
                "desc": "更新商机阶段（opportunities）",
                "input": ["opportunity_id", "status"],
                "output": ["success", "stage"],
                "cost": {"tokens": 0, "seconds": 1},
                "needs_approval": False,
            },
        }


ExecutorRegistry.register(GoodJobCrmExecutor())
