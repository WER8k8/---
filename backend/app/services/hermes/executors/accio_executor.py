# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Accio Executor Plugin for Hermes — 销售飞轮（接真实服务）。

承载实现（已存在，本插件只做契约适配，**不再返回硬编码假数据**）：
    services/ubrain/accio_sales_service.find_buyer_prospects
    services/ubrain/accio_sales_service.outreach_letter_pack
    services/ubrain/accio_sales_service.negotiation_draft

能力映射：
    prospect.enrich / buyer.research  → find_buyer_prospects（采购商候选）
    outreach.letter / outreach.write  → outreach_letter_pack（开发信草稿）
    negotiation.draft                 → negotiation_draft（谈单话术）

诚实纪律（对齐项目"不假交付"铁律）：
    · 真实服务自带 `human_verify_required` / `human_send_required` 标记与 disclaimer，
      本插件**原样透出，不篡改**——候选是「待核实」、开发信是「待确认草稿」，不是既成事实。
    · 不再出现 `{"letter": "Generated ..."}` 这类硬编码占位。
    · 失败即 failed + error，不粉饰。
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

# 能力别名 → 内部动作
_FIND = frozenset({"prospect.enrich", "buyer.research", "prospect.match"})
_LETTER = frozenset({"outreach.letter", "outreach.write"})
_NEGOTIATE = frozenset({"negotiation.draft"})


class AccioExecutor(BaseExecutor):
    """Accio 销售飞轮执行器（采购商候选 / 开发信 / 谈单话术）。"""

    @classmethod
    def get_executor_name(cls) -> str:
        return "accio"

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        capability = (node.capability or "default").strip()
        params: dict[str, Any] = dict(node.input or {})
        # 上游可能把内容塞进来（input_from 解析结果）
        message = str(
            params.get("message")
            or params.get("keyword")
            or params.get("query")
            or params.get("topic")
            or ""
        ).strip()

        try:
            if capability in _FIND:
                out = self._find(context, message, params)
            elif capability in _LETTER:
                out = self._letters(context, message, params)
            elif capability in _NEGOTIATE:
                out = self._negotiate(context, message, params)
            else:
                return ExecutorResult(
                    node_id=node.id,
                    status="skipped",
                    output={},
                    error=f"accio 不支持 capability={capability!r}",
                )
        except Exception as exc:  # noqa: BLE001 — 契约要求失败返回而非抛出
            logger.exception("AccioExecutor 执行失败 node=%s cap=%s", node.id, capability)
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error=f"{type(exc).__name__}: {exc}",
            )

        out["executor"] = self.get_executor_name()
        out["capability"] = capability
        return ExecutorResult(node_id=node.id, status="succeeded", output=out)

    # ── 内部动作 ────────────────────────────────────────────
    def _find(self, ctx: ExecutorContext, message: str, params: dict[str, Any]) -> dict[str, Any]:
        from app.services.ubrain.accio_sales_service import find_buyer_prospects

        if not message:
            message = str(params.get("category") or "建材")
        result = find_buyer_prospects(
            ctx.db, tenant_id=ctx.tenant_id, message=message, memory=None
        )
        prospects = result.get("prospects") or []
        return {
            "leads": prospects,          # 兼容下游 input_from 的 $.node.output.leads
            "prospects": prospects,
            "region": result.get("region"),
            "category": result.get("category"),
            "count": result.get("count", len(prospects)),
            # 原样透出诚实标记，不篡改
            "human_verify_required": result.get("human_verify_required", True),
            "disclaimer": result.get("disclaimer"),
            "write_back": result.get("write_back"),
            "next_step": result.get("next_step"),
            "raw": result,
        }

    def _letters(self, ctx: ExecutorContext, message: str, params: dict[str, Any]) -> dict[str, Any]:
        from app.services.ubrain.accio_sales_service import outreach_letter_pack

        prospect_ids = params.get("prospect_ids")
        if isinstance(prospect_ids, str):
            prospect_ids = [p.strip() for p in prospect_ids.split(",") if p.strip()]
        result = outreach_letter_pack(
            ctx.db,
            tenant_id=ctx.tenant_id,
            message=message or str(params.get("subject") or "开发信"),
            memory=None,
            prospect_ids=prospect_ids if isinstance(prospect_ids, list) else None,
        )
        letters = result.get("letters") or []
        return {
            "letters": letters,
            "letter_count": result.get("letter_count", len(letters)),
            "language": result.get("language"),
            "deliverability_summary": result.get("deliverability_summary"),
            # 草稿性质 + 需人工确认外发——原样透出
            "human_send_required": result.get("human_send_required", True),
            "disclaimer": result.get("disclaimer"),
            "write_back": result.get("write_back"),
            "raw": result,
        }

    def _negotiate(self, ctx: ExecutorContext, message: str, params: dict[str, Any]) -> dict[str, Any]:
        from app.services.ubrain.accio_sales_service import negotiation_draft

        memory = dict(params.get("memory") or {})
        if params.get("category"):
            memory.setdefault("product_category", str(params["category"]))
        result = negotiation_draft(message, dict(params), memory)
        return {"draft": result, "raw": result}


    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "prospect.enrich": {
                "desc": "采购商候选（公开 B2B 画像模板，**待人工核实**）",
                "input": ["message", "category", "region"],
                "output": ["leads", "prospects", "count", "human_verify_required"],
                "cost": {"tokens": 8000, "seconds": 60},
                "needs_approval": False,
            },
            "outreach.letter": {
                "desc": "开发信草稿（**需人工确认后方可外发**）",
                "input": ["message", "prospect_ids"],
                "output": ["letters", "letter_count", "human_send_required"],
                "cost": {"tokens": 12000, "seconds": 90},
                "needs_approval": True,
            },
            "negotiation.draft": {"desc": "多轮谈单话术", "input": ["message"]},
            "prospect.match": {"desc": "同 prospect.enrich（别名）", "input": ["message"]},
        }


ExecutorRegistry.register(AccioExecutor())
