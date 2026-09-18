# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Trade Ops Executor — 履约/单证深接（PI 前风控 + 跟单卡节点 + 物流回写）。

契约：
    trade_ops.pi_precheck      PI 前付款风险闸（真 payment_risk + playbook）
    trade_ops.fulfillment_node 跟单卡履约节点回写（真 ops_card_store）
    trade_ops.logistics_write  物流轨迹 + 回写跟单卡
    trade_ops.goodjob_pi       GoodJob PI 桥（未配置诚实 failed）
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

_CAPS = {
    "trade_ops.pi_precheck": {
        "desc": "PI 前付款风险与 Playbook 核验",
        "input": ["country?", "buyer_type?", "inquiry_id?", "auto_pi?", "deposit_ratio?"],
        "output": ["level", "auto_pi_allowed", "reasons"],
        "needs_approval": True,
    },
    "trade_ops.fulfillment_node": {
        "desc": "更新跟单卡报价/PI/定金/尾款节点",
        "input": ["inquiry_id", "key", "status?", "ref?"],
        "output": ["inquiry_id", "nodes", "reminders"],
        "needs_approval": False,
    },
    "trade_ops.logistics_write": {
        "desc": "物流查询并回写跟单卡",
        "input": ["inquiry_id?", "tracking_number", "carrier?"],
        "output": ["tracking", "simulated", "card_logistics"],
        "needs_approval": False,
    },
    "trade_ops.goodjob_pi": {
        "desc": "GoodJob 生成 PI（未接桥诚实失败）",
        "input": ["inquiry_id", "buyer?", "amount?", "currency?"],
        "output": ["pi_no?", "status"],
        "needs_approval": True,
    },
}


class TradeOpsExecutor(BaseExecutor):
    @classmethod
    def get_executor_name(cls) -> str:
        return "trade_ops"

    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return dict(_CAPS)

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        cap = (node.capability or "").strip()
        p = dict(node.input or {})
        try:
            if cap in ("trade_ops.pi_precheck", "default"):
                return self._pi_precheck(node, context, p)
            if cap == "trade_ops.fulfillment_node":
                return self._fulfillment_node(node, context, p)
            if cap == "trade_ops.logistics_write":
                return self._logistics_write(node, context, p)
            if cap == "trade_ops.goodjob_pi":
                return self._goodjob_pi(node, context, p)
            return ExecutorResult(node_id=node.id, status="skipped", output={}, error=f"unsupported {cap}")
        except Exception as exc:  # noqa: BLE001
            logger.exception("trade_ops failed %s", cap)
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=str(exc)[:300])

    def _pi_precheck(self, node, context, p) -> ExecutorResult:
        try:
            from app.services.acquisition import playbook_store, ops_card_store
            from app.services.acquisition.payment_risk import payment_risk_gate

            iid = str(p.get("inquiry_id") or "")
            card = ops_card_store.get_by_inquiry(iid) if iid else None
            country = str(p.get("country") or (card.buyer_display or "").split("@")[-1].strip()[:2] if card else p.get("country") or "")
            # 从买家展示抽国家码（粗）
            if card and not p.get("country"):
                disp = card.buyer_display or ""
                if "@" in disp:
                    tail = disp.split("@")[-1].strip()
                    if len(tail) >= 2:
                        country = tail[-2:].upper()
            buyer_type = str(p.get("buyer_type") or "new")
            risk_flags = list(getattr(card, "risk_flags", []) or []) if card else list(p.get("risk_flags") or [])
            gate = payment_risk_gate(
                country=country,
                buyer_type=buyer_type,
                buyer_grade=card.buyer_grade if card else "",
                risk_flags=risk_flags,
                deposit_ratio=p.get("deposit_ratio"),
                stage=card.stage if card else "",
                auto_pi=bool(p.get("auto_pi", False)),
                ops_store=ops_card_store,
                inquiry_id=iid,
            )
            tips = playbook_store.tips_for(country, buyer_type=buyer_type) if country else []
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={
                    **{k: gate.get(k) for k in ("level", "auto_pi_allowed", "auto_pi_blocked", "reasons", "plain", "next_action")},
                    "playbook_tips": tips[:5],
                    "country": country,
                    "executor": self.get_executor_name(),
                },
            )
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=f"pi_precheck: {exc}")

    def _fulfillment_node(self, node, context, p) -> ExecutorResult:
        iid = str(p.get("inquiry_id") or "").strip()
        key = str(p.get("key") or "").strip()
        if not iid or not key:
            return ExecutorResult(node_id=node.id, status="failed", output={}, error="missing inquiry_id/key")
        try:
            from app.services.acquisition import ops_card_store

            card = ops_card_store.update_fulfillment_node(
                iid,
                key=key,
                status=str(p.get("status") or ""),
                due_at=str(p.get("due_at") or ""),
                done_at=str(p.get("done_at") or ""),
                note=str(p.get("note") or ""),
                ref=str(p.get("ref") or ""),
            )
            fv = card.fulfillment_view()
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={
                    "inquiry_id": iid,
                    "nodes": fv.get("nodes"),
                    "reminders": fv.get("reminders"),
                    "stage": card.stage,
                    "executor": self.get_executor_name(),
                },
            )
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=str(exc))

    def _logistics_write(self, node, context, p) -> ExecutorResult:
        tn = str(p.get("tracking_number") or "").strip()
        if not tn:
            return ExecutorResult(node_id=node.id, status="failed", output={}, error="missing_tracking_number")
        try:
            from app.services.logistics_tracking_service import fetch_tracking_payload

            result = fetch_tracking_payload(tracking_number=tn, carrier=p.get("carrier") or None)
            out = dict(result or {})
            out["simulated"] = bool(out.get("demo") or out.get("simulated"))
            iid = str(p.get("inquiry_id") or "")
            if iid:
                from app.services.acquisition import ops_card_store
                card = ops_card_store.update_logistics(
                    iid,
                    bl_no=tn,
                    carrier=str(p.get("carrier") or out.get("carrier") or ""),
                    milestone=str(out.get("status") or out.get("milestone") or ""),
                )
                out["card_logistics"] = card.summary_lines().get("物流")
            out["executor"] = self.get_executor_name()
            return ExecutorResult(node_id=node.id, status="succeeded", output=out)
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=str(exc))

    def _goodjob_pi(self, node, context, p) -> ExecutorResult:
        iid = str(p.get("inquiry_id") or "").strip()
        try:
            import os
            base = (os.getenv("GOODJOB_BASE_URL") or "").strip()
            if not base:
                return ExecutorResult(
                    node_id=node.id,
                    status="failed",
                    output={"status": "not_configured", "inquiry_id": iid},
                    error="GOODJOB_BASE_URL 未配置 — 拒绝生成假 PI",
                )
            # 真桥路径：优先调用 goodjob 服务（存在则调）
            try:
                from app.services.goodjob.trade_document_bridge import generate_pi  # type: ignore

                out = generate_pi(inquiry_id=iid, **{k: p.get(k) for k in ("buyer", "amount", "currency") if p.get(k) is not None})
                return ExecutorResult(
                    node_id=node.id,
                    status="succeeded",
                    output={"status": "ok", **(out if isinstance(out, dict) else {"result": out}), "executor": self.get_executor_name()},
                )
            except Exception as exc:  # noqa: BLE001
                return ExecutorResult(
                    node_id=node.id,
                    status="failed",
                    output={"status": "bridge_error", "inquiry_id": iid},
                    error=f"goodjob_pi: {exc}",
                )
        except Exception as exc:  # noqa: BLE001
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=str(exc))


ExecutorRegistry.register(TradeOpsExecutor())
