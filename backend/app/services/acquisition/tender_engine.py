# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P3-7 经销商 / 招投标流程引擎（大单深耕 v1）。

状态机（跟单卡 + 独立 tender 记录）：
    lead → qualify → bid_prep → tender_submit → evaluation → won/lost

规则：
    · 资质包未齐禁止 tender_submit
    · 账期/风险未过人审禁止标「可自动 PI」
    · 每步写 ops 卡备注，可调度（commerce_ops / trade_ops 调用）
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


STAGES = (
    "lead",
    "qualify",
    "bid_prep",
    "tender_submit",
    "evaluation",
    "won",
    "lost",
)

STAGE_LABELS = {
    "lead": "大单线索",
    "qualify": "资质核验",
    "bid_prep": "标书准备",
    "tender_submit": "投标提交",
    "evaluation": "评标中",
    "won": "中标",
    "lost": "未中标",
}

QUAL_DOCS = (
    "business_license",
    "iso_cert",
    "product_test_report",
    "project_cases",
    "bank_account",
    "factory_video",
)


@dataclass
class TenderProject:
    tender_id: str
    inquiry_id: str = ""
    tenant_id: str = "demo"
    buyer_name: str = ""
    project_name: str = ""
    stage: str = "lead"
    docs_ready: dict[str, bool] = field(default_factory=dict)
    payment_terms: str = ""
    credit_ok: Optional[bool] = None
    auto_pi_allowed: bool = False
    amount: float = 0.0
    currency: str = "USD"
    note: str = ""
    updated_at: str = field(default_factory=_now)
    history: list[dict[str, Any]] = field(default_factory=list)


class TenderEngine:
    def __init__(self) -> None:
        self._by_id: dict[str, TenderProject] = {}

    def get(self, tender_id: str) -> Optional[TenderProject]:
        return self._by_id.get(tender_id)

    def upsert(
        self,
        *,
        tender_id: str = "",
        inquiry_id: str = "",
        tenant_id: str = "demo",
        buyer_name: str = "",
        project_name: str = "",
        amount: float = 0,
        currency: str = "USD",
    ) -> TenderProject:
        tid = tender_id or f"TDR-{inquiry_id or 'NEW'}"
        proj = self._by_id.get(tid)
        if proj is None:
            proj = TenderProject(
                tender_id=tid,
                inquiry_id=inquiry_id,
                tenant_id=tenant_id,
                buyer_name=buyer_name,
                project_name=project_name or f"{buyer_name or inquiry_id} 项目",
                amount=float(amount or 0),
                currency=currency or "USD",
                docs_ready={d: False for d in QUAL_DOCS},
            )
            self._by_id[tid] = proj
        else:
            if inquiry_id:
                proj.inquiry_id = inquiry_id
            if buyer_name:
                proj.buyer_name = buyer_name
            if project_name:
                proj.project_name = project_name
            if amount:
                proj.amount = float(amount)
        proj.updated_at = _now()
        return proj

    def checklist(self, tender_id: str) -> dict[str, Any]:
        proj = self.upsert(tender_id=tender_id)
        docs = dict(proj.docs_ready or {})
        missing = [k for k in QUAL_DOCS if not docs.get(k)]
        ready = not missing
        return {
            "tender_id": proj.tender_id,
            "stage": proj.stage,
            "stage_label": STAGE_LABELS.get(proj.stage, proj.stage),
            "docs_ready": docs,
            "missing_docs": missing,
            "qualify_ready": ready,
            "payment_terms": proj.payment_terms,
            "credit_ok": proj.credit_ok,
            "auto_pi_allowed": proj.auto_pi_allowed,
            "plain": (
                f"资质包齐全（{len(QUAL_DOCS)-len(missing)}/{len(QUAL_DOCS)}）"
                if ready
                else f"还缺资质：{'、'.join(missing)}"
            ),
            "next_action": (
                "进入标书准备：交期/质保/账期写进投标文件"
                if ready
                else "先补齐缺失资质文件，禁止投标提交"
            ),
        }

    def mark_doc(self, tender_id: str, doc_key: str, ready: bool = True) -> dict[str, Any]:
        proj = self.upsert(tender_id=tender_id)
        if doc_key not in QUAL_DOCS:
            return {"ok": False, "message": f"未知资质项 {doc_key}", "allowed_docs": list(QUAL_DOCS)}
        proj.docs_ready[doc_key] = bool(ready)
        proj.updated_at = _now()
        proj.history.append({"at": _now(), "type": "doc", "doc": doc_key, "ready": bool(ready)})
        return self.checklist(tender_id)

    def set_payment(self, tender_id: str, terms: str, credit_ok: bool = False) -> dict[str, Any]:
        proj = self.upsert(tender_id=tender_id)
        proj.payment_terms = terms or ""
        proj.credit_ok = bool(credit_ok)
        # 长账期 + 未信用确认 → 禁自动 PI
        risky_terms = any(x in (terms or "").lower() for x in ("账期", "credit", "oa", "lc", "90", "120", "180"))
        proj.auto_pi_allowed = bool(credit_ok) and not risky_terms
        proj.updated_at = _now()
        proj.history.append({"at": _now(), "type": "payment", "terms": terms, "credit_ok": credit_ok})
        return {
            "ok": True,
            "tender_id": proj.tender_id,
            "payment_terms": proj.payment_terms,
            "credit_ok": proj.credit_ok,
            "auto_pi_allowed": proj.auto_pi_allowed,
            "plain": (
                "付款条款已登记，可考虑自动 PI（仍建议人审）"
                if proj.auto_pi_allowed
                else "账期/信用未过闸 — 禁止自动 PI，须人审"
            ),
            "next_action": "财务/合规确认后再推进 PI",
        }

    def advance(self, tender_id: str, to_stage: str, note: str = "") -> dict[str, Any]:
        proj = self.upsert(tender_id=tender_id)
        to_stage = (to_stage or "").strip().lower()
        if to_stage not in STAGES:
            return {"ok": False, "message": f"非法阶段 {to_stage}", "stages": list(STAGES)}
        checklist = self.checklist(tender_id)
        # 提交投标必须资质齐
        if to_stage == "tender_submit" and not checklist["qualify_ready"]:
            return {
                "ok": False,
                "code": "docs_incomplete",
                "message": checklist["plain"],
                "checklist": checklist,
            }
        if to_stage in ("won", "lost") and proj.stage not in ("evaluation", "tender_submit", "bid_prep"):
            # 允许从任意阶段结果登记，但提示
            pass
        proj.stage = to_stage
        proj.updated_at = _now()
        proj.history.append({"at": _now(), "type": "stage", "from": proj.stage, "to": to_stage, "note": note})
        if note:
            proj.note = note
        return {
            "ok": True,
            "tender_id": proj.tender_id,
            "stage": proj.stage,
            "stage_label": STAGE_LABELS.get(proj.stage, proj.stage),
            "checklist": self.checklist(tender_id),
            "plain": f"已进入阶段：{STAGE_LABELS.get(proj.stage, proj.stage)}",
        }

    def playbook(self, *, buyer_type: str = "distributor") -> list[str]:
        if buyer_type == "tender":
            return [
                "投标：资质包先齐，再写交期/质保/账期",
                "无信用确认不承诺长账期",
                "评标期间保持周更，勿失联",
            ]
        return [
            "经销商：要年采购量与渠道布局",
            "区域独家条款必须法务/人审",
            "账期与铺货风险进付款闸",
        ]

    def view(self, tender_id: str) -> dict[str, Any]:
        proj = self.upsert(tender_id=tender_id)
        return {
            **self.checklist(tender_id),
            "tender_id": proj.tender_id,
            "inquiry_id": proj.inquiry_id,
            "tenant_id": proj.tenant_id,
            "project_name": proj.project_name,
            "buyer_name": proj.buyer_name,
            "amount": proj.amount,
            "currency": proj.currency,
            "history": proj.history[-20:],
            "playbook": self.playbook(),
        }


tender_engine = TenderEngine()
