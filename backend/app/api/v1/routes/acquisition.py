# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""获客 API：编排图预览 · 跟单卡 · Playbook。

挂在 /api/v1 下；与既有 orchestration 路由互补，不替代。
权限：复用 get_current_user；测试环境允许无依赖构造。
"""
from __future__ import annotations

from typing import Any, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.hermes_orchestration import IntentEvent
from app.services.acquisition import (
    BuyerMaster,
    buyer_store,
    ops_card_store,
    playbook_store,
    score_grade,
    sample_view,
    evaluate_research_gate,
    list_dictionary,
    dictionary_plain_summary,
)
from app.services.acquisition.dispatch_service import dispatch_acquisition
from app.services.acquisition.experience_feed import (
    record_acquisition_event,
    record_ops_loss,
    record_ops_win,
)
from app.services.acquisition.onboarding import build_onboarding
from app.services.acquisition.intent_classifier import classify_reply
from app.services.acquisition.repo import persist_inquiry, persist_prospect_lead
from app.services.acquisition.sla import card_sla, default_next_action_at
from app.services.acquisition.translate_service import translate_text
from app.services.acquisition.wallet_guard import check_wallet_status
from app.services.acquisition.growth_ops import content_attr_store, ip_slot_catalog
from app.services.acquisition.billing_explain import billing_explain
from app.services.acquisition.sales_collision import claim_inquiry, collision_report
from app.services.acquisition.wangcai_line_b import rescue_plan
from app.services.acquisition.nps_rescue import nps_and_rescue_brief
from app.services.acquisition.sanctions_source import list_source_status, screen_subject
from app.services.acquisition.tender_engine import tender_engine
from app.core.db_sessions import get_read_session
from app.services.acquisition.quote_guard import leadtime_gate, quote_validity_view
from app.services.acquisition.suppression_list import suppression_store
from app.services.acquisition.payment_risk import payment_risk_gate
from app.services.acquisition.knowledge_queue import knowledge_queue_store
from app.services.acquisition.risk_rescan import risk_rescan_store
from app.services.acquisition.ops_observability import acq_rate_limiter, billing_reconcile
from app.services.acquisition.queue_monitor import queue_monitor_report
from app.services.acquisition.baseline_bench import run_dispatch_baseline, run_claim_collision_baseline
from app.services.acquisition.sales_collision import claim_inquiry as _claim_fn
from app.core.db_sessions import db_topology, get_read_session
from app.services.acquisition.template_weights import (
    approve_weight,
    approved_weights,
    build_template_weight_suggestions,
)
from app.services.evolution.unified_experience import experience_source_report

# FIX-30：router 自带 prefix="/acquisition"，auto_discovery 必须用空外挂前缀，
# 否则会变成 /api/v1/acquisition/acquisition/*（前端 404）。
ROUTE_PREFIX = ""


def _resolve_db(db: Any = None) -> Any:
    """单测直调时 db 可能是 Depends 占位；无真实 Session 一律当 None。"""
    if db is None:
        return None
    if type(db).__name__ in ("Depends", "DependsObject"):
        return None
    if not hasattr(db, "add"):
        return None
    return db


def _ops_card_payload(card: Any) -> dict[str, Any]:
    """跟单卡统一视图：六格 + 评分大字 + 履约节点 + 样品 + 背调闸 + SLA + P3。"""
    from app.services.acquisition.sla import card_sla
    from app.services.acquisition.sample_flow import sample_view as _sv

    return {
        "card": card.to_dict(),
        "summary": card.summary_lines(),
        "score_display": card.score_display(),
        "fulfillment": card.fulfillment_view(),
        "sample": _sv(card.sample),
        "research_gate": card.research_gate_view(),
        "quote_validity": card.quote_validity_view(),
        "leadtime_gate": card.leadtime_gate_view(),
        "payment_risk": card.payment_risk_view(),
        "sla": card_sla(card),
    }


def _rate_limit_or_raise(tenant_id: str, action: str = "acq_api") -> dict[str, Any]:
    """E-3：超限诚实 429。"""
    verdict = acq_rate_limiter.check(tenant_id=tenant_id, action=action)
    if not verdict.get("allowed"):
        raise HTTPException(status_code=429, detail=verdict.get("plain") or "rate limited")
    return verdict


ROUTE_TAGS = ["获客"]

router = APIRouter(prefix="/acquisition", tags=["获客"])


# ── Schemas ────────────────────────────────────────────────

class IntentPreviewRequest(BaseModel):
    intent: str = Field(..., description="如 find_leads / fulfillment / whatsapp")
    tenant_id: str = "demo"
    payload: dict[str, Any] = Field(default_factory=dict)
    channel: str = "api"


class NodePreview(BaseModel):
    id: str
    executor: str
    capability: str
    depends_on: List[str] = []
    approval_required: bool = False


class IntentPreviewResponse(BaseModel):
    plan_id: str
    source: str
    strategy: str
    approval_required: List[str]
    nodes: List[NodePreview]
    skill_refs: List[dict[str, Any]]
    playbook_tips: List[str]
    experience: Optional[dict[str, Any]] = None


class BuyerUpsertRequest(BaseModel):
    tenant_id: str
    email: str = ""
    contact_name: str = ""
    contact_gender: str = "unknown"
    contact_title: str = ""
    company_name: str = ""
    company_domain: str = ""
    company_country: str = ""
    buyer_type: str = "unknown"
    industry: str = ""
    source: str = ""


class OpsCardMaterializeRequest(BaseModel):
    tenant_id: str
    inquiry_id: str
    buyer_id: str = ""
    owner_user_id: str = ""
    grade: int = 0
    grade_reason: str = ""


class OpsCardTouchRequest(BaseModel):
    channel: str = "whatsapp"
    summary: str = ""
    next_action: str = ""
    next_action_at: str = ""
    direction: str = "outbound"


class OpsCardNoteRequest(BaseModel):
    author: str = "sales"
    body: str
    pinned: bool = False


class OpsCardLossRequest(BaseModel):
    reasons: List[str]
    note: str = ""


class OpsCardWinRequest(BaseModel):
    amount: float = 0
    currency: str = "USD"
    note: str = ""
    reasons: List[str] = Field(default_factory=list)


class OpsCardPaymentRequest(BaseModel):
    pi_no: str = ""
    deposit_amount: float = 0
    deposit_due: str = ""
    deposit_paid_at: str = ""
    balance_amount: float = 0
    balance_status: str = ""  # pending/paid/overdue
    voucher_url: str = ""
    overdue_days: int = 0


class OpsCardLogisticsRequest(BaseModel):
    forwarder: str = ""
    carrier: str = ""
    bl_no: str = ""
    container_no: str = ""
    etd: str = ""
    eta: str = ""
    milestone: str = ""


class OpsCardSkuLineRequest(BaseModel):
    name: str = ""
    spec: str = ""
    qty: float = 0
    unit: str = ""
    price: float = 0
    currency: str = "USD"


class OpsCardGoodsRequest(BaseModel):
    sku_lines: List[OpsCardSkuLineRequest] = Field(default_factory=list)
    container_hint: str = ""


class OpsCardSampleRequest(BaseModel):
    status: str = ""  # none/requested/confirmed/preparing/shipped/delivered/fee_collected/waived/rejected
    product: str = ""
    spec: str = ""
    qty: float = 0
    unit: str = ""
    fee_amount: float = 0
    fee_currency: str = "USD"
    fee_status: str = ""  # unbilled/billed/paid/waived
    courier: str = ""
    tracking_no: str = ""
    shipped_at: str = ""
    note: str = ""


class OpsCardFulfillmentRequest(BaseModel):
    key: str  # quote/pi/deposit/balance
    status: str = ""
    due_at: str = ""
    done_at: str = ""
    note: str = ""
    ref: str = ""


class OpsCardResearchRequest(BaseModel):
    research_level: str = "none"  # none/basic/osint/full
    note: str = ""


class ContentAttrRegisterRequest(BaseModel):
    content_id: str = ""
    content_title: str = ""
    content_type: str = "article"
    channel: str = ""
    tenant_id: str = "demo"
    published_at: str = ""


class ContentAttrLinkRequest(BaseModel):
    content_id: str
    inquiry_id: str
    tenant_id: str = "demo"


class ReplyIngestRequest(BaseModel):
    tenant_id: str = "demo"
    inquiry_id: str
    buyer_id: str = ""
    channel: str = "inbound"
    message: str = ""
    country: str = ""
    grade: int = 0
    owner_user_id: str = ""
    contact_name: str = ""
    contact_gender: str = "unknown"
    contact_title: str = ""
    company_name: str = ""
    email: str = ""
    buyer_type: str = "unknown"


class TranslateRequest(BaseModel):
    text: str
    from_lang: str = "auto"
    to_lang: str = "zh"


class DispatchRequest(BaseModel):
    intent: str
    tenant_id: str = "demo"
    channel: str = "acquisition_ops"
    payload: dict[str, Any] = Field(default_factory=dict)
    inquiry_id: str = ""
    auto_dispatch: bool = False


class DispatchResponse(BaseModel):
    plan_id: str
    graph_source: str
    node_count: int
    nodes: List[dict[str, Any]]
    approval_required: List[str]
    dispatched: bool
    task_ids: List[str]
    plan_task_id: str
    dispatch_error: str
    persistence_note: str
    experience: Optional[dict[str, Any]] = None
    card: Optional[dict[str, Any]] = None


# ── 编排图预览（好用：先看懂再执行）─────────────────────────

@router.post("/intent/preview", response_model=IntentPreviewResponse)
async def intent_preview(
    body: IntentPreviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """意图 → 任务图预览（不真正派发）。傻子都行：先看节点与是否人审。"""
    from app.services.hermes import planner_service as ps

    ev = IntentEvent(
        event_id=f"preview-{id(body)}",
        tenant_id=body.tenant_id,
        channel=body.channel,
        intent=body.intent,
        payload=dict(body.payload or {}),
    )
    # preview 用假 db，experience 可能失败 — best-effort
    try:
        import asyncio
        graph, source = await ps.decompose(ev, db=None)  # type: ignore[arg-type]
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"拆解失败: {exc}") from exc

    approval = list(graph.policies.approval_required or [])
    nodes = []
    for n in graph.nodes:
        need_appr = any(n.capability.startswith(a) or a == n.capability for a in approval)
        nodes.append(NodePreview(
            id=n.id,
            executor=n.executor,
            capability=n.capability,
            depends_on=list(n.depends_on or []),
            approval_required=need_appr,
        ))
    tips = []
    country = str((body.payload or {}).get("country") or "").upper()
    if country:
        tips = playbook_store.tips_for(country, buyer_type="new")
    skill_refs = list((ev.payload or {}).get("_skill_refs") or [])
    exp = record_acquisition_event(
        _resolve_db(db),
        tenant_id=body.tenant_id,
        event="intent_preview",
        inquiry_id="",
        success=True,
        detail=f"intent={body.intent}; source={source}; nodes={len(nodes)}",
        executor_id="planner_preview",
    )
    return IntentPreviewResponse(
        plan_id=graph.plan_id,
        source=source,
        strategy=graph.strategy,
        approval_required=approval,
        nodes=nodes,
        skill_refs=skill_refs,
        playbook_tips=tips,
        experience=exp,
    )


# ── Buyer Master ───────────────────────────────────────────

@router.post("/buyers/upsert")
def buyers_upsert(
    body: BuyerUpsertRequest,
    current_user: User = Depends(get_current_user),
):
    b = BuyerMaster(**body.model_dump())
    out, is_new, alerts = buyer_store.upsert(b)
    return {"buyer": out.to_dict(), "is_new": is_new, "alerts": alerts}


@router.get("/buyers/{buyer_id}")
def buyers_get(buyer_id: str, current_user: User = Depends(get_current_user)):
    b = buyer_store.get(buyer_id)
    if not b:
        raise HTTPException(status_code=404, detail="buyer_not_found")
    return b.to_dict()


@router.get("/buyers/by-email/{tenant_id}/{email}")
def buyers_by_email(
    tenant_id: str,
    email: str,
    current_user: User = Depends(get_current_user),
):
    b = buyer_store.get_by_email(tenant_id, email)
    if not b:
        raise HTTPException(status_code=404, detail="buyer_not_found")
    return b.to_dict()


# ── Ops Card 跟单卡 ────────────────────────────────────────

@router.post("/ops-card/materialize")
def ops_card_materialize(
    body: OpsCardMaterializeRequest,
    current_user: User = Depends(get_current_user),
):
    buyer = buyer_store.get(body.buyer_id) if body.buyer_id else None
    grade, reason = "", ""
    score = int(body.grade or 0)
    if body.grade:
        g, r = score_grade(body.grade)
        grade, reason = g, (r or body.grade_reason)
    elif body.grade_reason:
        grade, reason = "", body.grade_reason
    country = buyer.company_country if buyer else ""
    tips = playbook_store.tips_for(country, buyer_type=buyer.buyer_type if buyer else "new") if country else []
    card = ops_card_store.materialize(
        tenant_id=body.tenant_id,
        inquiry_id=body.inquiry_id,
        buyer_id=body.buyer_id,
        owner_user_id=body.owner_user_id,
        buyer=buyer,
        grade=grade,
        grade_reason=reason,
        playbook_tips=tips,
        score=score,
    )
    return _ops_card_payload(card)


@router.get("/ops-card/{inquiry_id}")
def ops_card_get(inquiry_id: str, current_user: User = Depends(get_current_user)):
    card = ops_card_store.get_by_inquiry(inquiry_id)
    if not card:
        raise HTTPException(status_code=404, detail="ops_card_not_found")
    return _ops_card_payload(card)


@router.post("/ops-card/{inquiry_id}/touch")
def ops_card_touch(
    inquiry_id: str,
    body: OpsCardTouchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    card = ops_card_store.record_touch(
        inquiry_id,
        channel=body.channel,
        summary=body.summary,
        next_action=body.next_action,
        next_action_at=body.next_action_at,
    )
    exp = record_acquisition_event(
        _resolve_db(db),
        tenant_id=card.tenant_id,
        event="ops_touch",
        inquiry_id=inquiry_id,
        success=True,
        detail=body.summary[:200],
        executor_id="ops_card",
    )
    out = _ops_card_payload(card)
    out["experience"] = exp
    return out


@router.post("/ops-card/{inquiry_id}/note")
def ops_card_note(
    inquiry_id: str,
    body: OpsCardNoteRequest,
    current_user: User = Depends(get_current_user),
):
    card = ops_card_store.add_note(inquiry_id, body.author, body.body, body.pinned)
    return _ops_card_payload(card)


@router.post("/ops-card/{inquiry_id}/loss")
def ops_card_loss(
    inquiry_id: str,
    body: OpsCardLossRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    card = ops_card_store.record_loss(inquiry_id, body.reasons, body.note)
    exp = record_ops_loss(
        _resolve_db(db),
        tenant_id=card.tenant_id,
        inquiry_id=inquiry_id,
        reasons=list(body.reasons or []),
        note=body.note or "",
    )
    out = _ops_card_payload(card)
    out["experience"] = exp
    out["loss_report"] = ops_card_store.loss_stats(tenant_id=card.tenant_id)
    return out


@router.post("/ops-card/{inquiry_id}/payment")
def ops_card_payment(
    inquiry_id: str,
    body: OpsCardPaymentRequest,
    current_user: User = Depends(get_current_user),
):
    """更新收款（定金/尾款/PI）——傻子都行大白话字段。"""
    card = ops_card_store.update_payment(
        inquiry_id,
        pi_no=body.pi_no,
        deposit_amount=body.deposit_amount,
        deposit_due=body.deposit_due,
        deposit_paid_at=body.deposit_paid_at,
        balance_amount=body.balance_amount,
        balance_status=body.balance_status,
        voucher_url=body.voucher_url,
        overdue_days=body.overdue_days,
    )
    # P1-2：收款联动履约节点
    if body.pi_no:
        card = ops_card_store.update_fulfillment_node(
            inquiry_id, key="pi", status="done", ref=body.pi_no
        )
    if body.deposit_paid_at:
        card = ops_card_store.update_fulfillment_node(inquiry_id, key="deposit", status="done")
    if body.balance_status == "paid":
        card = ops_card_store.update_fulfillment_node(inquiry_id, key="balance", status="done")
    elif body.balance_status == "overdue":
        card = ops_card_store.update_fulfillment_node(inquiry_id, key="balance", status="overdue")
    return _ops_card_payload(card)


@router.post("/ops-card/{inquiry_id}/logistics")
def ops_card_logistics(
    inquiry_id: str,
    body: OpsCardLogisticsRequest,
    current_user: User = Depends(get_current_user),
):
    """更新物流（货代/柜号/ETD/ETA/里程碑）。"""
    card = ops_card_store.update_logistics(
        inquiry_id,
        forwarder=body.forwarder,
        carrier=body.carrier,
        bl_no=body.bl_no,
        container_no=body.container_no,
        etd=body.etd,
        eta=body.eta,
        milestone=body.milestone,
    )
    return _ops_card_payload(card)


@router.post("/ops-card/{inquiry_id}/goods")
def ops_card_goods(
    inquiry_id: str,
    body: OpsCardGoodsRequest,
    current_user: User = Depends(get_current_user),
):
    """更新货物（发什么货）。"""
    from app.services.acquisition import OpsCardSkuLine

    card = ops_card_store.get_by_inquiry(inquiry_id)
    if card is None:
        from app.services.acquisition import OpsCard as _OC
        card = _OC(inquiry_id=inquiry_id)
    card.sku_lines = [
        OpsCardSkuLine(
            name=s.name, spec=s.spec, qty=s.qty, unit=s.unit,
            price=s.price, currency=s.currency or "USD",
        )
        for s in body.sku_lines
    ]
    if body.container_hint is not None:
        card.container_hint = body.container_hint
    card = ops_card_store.update(card)
    return _ops_card_payload(card)


@router.post("/ops-card/{inquiry_id}/sample")
def ops_card_sample(
    inquiry_id: str,
    body: OpsCardSampleRequest,
    current_user: User = Depends(get_current_user),
):
    """P1-5 样品流程：寄样状态机 + 费用备注。"""
    from app.services.acquisition.sample_flow import can_transition, sample_view

    card = ops_card_store.get_by_inquiry(inquiry_id)
    current_status = (card.sample.status if card and card.sample else "none") or "none"
    if body.status and body.status != current_status:
        if not can_transition(current_status, body.status):
            raise HTTPException(
                status_code=422,
                detail=f"样品状态不能从「{current_status}」直接到「{body.status}」",
            )
    kwargs: dict[str, Any] = {}
    for field_name in (
        "status", "product", "spec", "qty", "unit",
        "fee_amount", "fee_currency", "fee_status",
        "courier", "tracking_no", "shipped_at", "note",
    ):
        val = getattr(body, field_name, None)
        if val is not None and val != "":
            kwargs[field_name] = val
    if body.qty:
        kwargs["qty"] = body.qty
    if body.fee_amount:
        kwargs["fee_amount"] = body.fee_amount
    card = ops_card_store.update_sample(inquiry_id, **kwargs)
    out = _ops_card_payload(card)
    out["sample"] = sample_view(card.sample)
    return out


@router.post("/ops-card/{inquiry_id}/fulfillment")
def ops_card_fulfillment(
    inquiry_id: str,
    body: OpsCardFulfillmentRequest,
    current_user: User = Depends(get_current_user),
):
    """P1-2 报价/PI/定金/尾款节点状态进跟单卡。"""
    if not (body.key or "").strip():
        raise HTTPException(status_code=400, detail="key required (quote/pi/deposit/balance)")
    card = ops_card_store.update_fulfillment_node(
        inquiry_id,
        key=body.key.strip(),
        status=body.status,
        due_at=body.due_at,
        done_at=body.done_at,
        note=body.note,
        ref=body.ref,
    )
    return _ops_card_payload(card)


@router.post("/ops-card/{inquiry_id}/research")
def ops_card_research(
    inquiry_id: str,
    body: OpsCardResearchRequest,
    current_user: User = Depends(get_current_user),
):
    """P1-6 千人千面背调深度登记；无背调禁止个性化开发信。"""
    card = ops_card_store.set_research_level(
        inquiry_id, body.research_level, note=body.note
    )
    return _ops_card_payload(card)


@router.get("/loss-report")
def acquisition_loss_report(
    tenant_id: str = "demo",
    current_user: User = Depends(get_current_user),
):
    """P1-3 流失原因报表：分布 + 大白话解读。"""
    return ops_card_store.loss_stats(tenant_id=tenant_id)


@router.post("/ops-card/{inquiry_id}/win")
def ops_card_win(
    inquiry_id: str,
    body: OpsCardWinRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """P2-2 成交登记：won + 金额/原因 → 经验环。"""
    card = ops_card_store.record_win(
        inquiry_id,
        amount=body.amount,
        currency=body.currency,
        note=body.note,
        reasons=list(body.reasons or []),
    )
    exp = record_ops_win(
        _resolve_db(db),
        tenant_id=card.tenant_id,
        inquiry_id=inquiry_id,
        amount=body.amount,
        currency=body.currency,
        note=body.note,
        won_reasons=list(body.reasons or []),
    )
    out = _ops_card_payload(card)
    out["experience"] = exp
    out["win_loss"] = ops_card_store.win_loss_stats(tenant_id=card.tenant_id)
    return out


@router.get("/win-loss")
def acquisition_win_loss(
    tenant_id: str = "demo",
    current_user: User = Depends(get_current_user),
):
    """P2-2 Win/Loss 汇总（傻子能看懂）。"""
    return ops_card_store.win_loss_stats(tenant_id=tenant_id)


@router.get("/onboarding")
def acquisition_onboarding(
    tenant_id: str = "demo",
    has_dispatch: bool = False,
    current_user: User = Depends(get_current_user),
):
    """P2-4 租户开通 5 步引导清单。"""
    return build_onboarding(
        tenant_id,
        ops_store=ops_card_store,
        has_dispatch=has_dispatch,
    )


class TemplateWeightApproveRequest(BaseModel):
    intent: str
    weight: float
    approved_by: str = "operator"
    tenant_id: str = "demo"


@router.get("/template-weights")
def acquisition_template_weights(
    tenant_id: str = "demo",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """P2-3 L1 模板权重建议（只读；需人审才生效）。"""
    session = _resolve_db(db)
    out = build_template_weight_suggestions(
        ops_store=ops_card_store,
        tenant_id=tenant_id,
        db=session,
    )
    out["approved"] = approved_weights(tenant_id)
    return out


@router.post("/template-weights/approve")
def acquisition_template_weights_approve(
    body: TemplateWeightApproveRequest,
    current_user: User = Depends(get_current_user),
):
    """P2-3 人审通过某航道权重（记录，不自动改调度源码）。"""
    if not (body.intent or "").strip():
        raise HTTPException(status_code=400, detail="intent required")
    rec = approve_weight(body.tenant_id, body.intent.strip(), body.weight, approved_by=body.approved_by)
    return {
        "approved": rec,
        "plain_summary": f"已记录人审权重 {body.intent}={rec['weight']}（调度可读取该批准值）。",
        "hint": "批准≠自动改库；后续调度接入 approved_weights 读取。",
    }


@router.get("/experience-source")
def acquisition_experience_source(
    tenant_id: str = "demo",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """P2-1 经验真源体检：PG 是否为唯一主源。"""
    return experience_source_report(_resolve_db(db), tenant_id=tenant_id)


@router.get("/billing-explain")
def acquisition_billing_explain(
    tenant_id: str = "demo",
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """P2-6 账单明细可解释：Token/动作大白话。"""
    return billing_explain(_resolve_db(db), tenant_id=tenant_id, limit=max(1, min(50, limit)))


class InquiryClaimRequest(BaseModel):
    tenant_id: str = "demo"
    user_id: str
    confirm_force: bool = False
    note: str = ""


@router.post("/ops-card/{inquiry_id}/claim")
def ops_card_claim(
    inquiry_id: str,
    body: InquiryClaimRequest,
    current_user: User = Depends(get_current_user),
):
    """P2-7 撞单规则：认领/交接审计。"""
    return claim_inquiry(
        ops_card_store,
        inquiry_id=inquiry_id,
        user_id=body.user_id,
        tenant_id=body.tenant_id,
        confirm_force=body.confirm_force,
        note=body.note,
    )


@router.get("/collision-report")
def acquisition_collision_report(
    tenant_id: str = "demo",
    current_user: User = Depends(get_current_user),
):
    """P2-7 团队交接/撞单汇总。"""
    return collision_report(ops_card_store, tenant_id=tenant_id)


@router.get("/wangcai-rescue")
def acquisition_wangcai_rescue(
    tenant_id: str = "demo",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """P1-10 旺财线B：建站卡壳 → 小图补救建议（禁复读）。"""
    return rescue_plan(tenant_id=tenant_id, db=_resolve_db(db))


@router.get("/nps-rescue")
def acquisition_nps_rescue(
    tenant_id: str = "demo",
    nps_score: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """P2-5 NPS / 低使用挽回（只出建议，不自动骚扰）。"""
    session = _resolve_db(db)
    onb = build_onboarding(tenant_id, ops_store=ops_card_store, has_dispatch=False)
    wl = ops_card_store.win_loss_stats(tenant_id=tenant_id)
    bill = None
    try:
        bill = billing_explain(session, tenant_id=tenant_id, limit=1)
    except Exception:
        bill = None
    return nps_and_rescue_brief(
        tenant_id=tenant_id,
        ops_store=ops_card_store,
        onboarding_view=onb,
        win_loss_view=wl,
        billing_view=bill,
        nps_score=nps_score,
    )


class QuoteValidityRequest(BaseModel):
    quote_at: str = ""
    valid_days: int = 14
    fx_locked: bool = False
    fx_note: str = ""


class LeadtimeRequest(BaseModel):
    promised_days: Optional[int] = None
    has_inventory_evidence: bool = False
    has_capacity_evidence: bool = False
    note: str = ""


class SuppressionRequest(BaseModel):
    email: str
    tenant_id: str = "demo"
    reason: str = "unsubscribe"
    source: str = ""
    created_by: str = "operator"


class SuppressionRemoveRequest(BaseModel):
    email: str
    tenant_id: str = "demo"
    confirm: bool = False
    note: str = ""


class OutreachAllowRequest(BaseModel):
    email: str
    tenant_id: str = "demo"
    channel: str = "email"
    mode: str = "personalized"


class PaymentRiskRequest(BaseModel):
    country: str = ""
    buyer_type: str = "new"
    inquiry_id: str = ""
    auto_pi: bool = False
    deposit_ratio: Optional[float] = None
    risk_flags: List[str] = Field(default_factory=list)


@router.post("/ops-card/{inquiry_id}/quote-validity")
def ops_card_quote_validity(
    inquiry_id: str,
    body: QuoteValidityRequest,
    current_user: User = Depends(get_current_user),
):
    """P3-2 登记报价有效期。"""
    card = ops_card_store.get_by_inquiry(inquiry_id)
    if card is None:
        from app.services.acquisition import OpsCard as _OC
        card = _OC(inquiry_id=inquiry_id)
    card.quote_at = body.quote_at or card.quote_at
    card.quote_valid_days = int(body.valid_days or 14)
    card.quote_fx_locked = bool(body.fx_locked)
    card.quote_fx_note = body.fx_note or card.quote_fx_note
    card = ops_card_store.update(card)
    out = _ops_card_payload(card)
    out["quote_validity"] = card.quote_validity_view()
    return out


@router.post("/ops-card/{inquiry_id}/leadtime")
def ops_card_leadtime(
    inquiry_id: str,
    body: LeadtimeRequest,
    current_user: User = Depends(get_current_user),
):
    """P3-3 交期门禁：无证据禁止保证交期。"""
    card = ops_card_store.get_by_inquiry(inquiry_id)
    if card is None:
        from app.services.acquisition import OpsCard as _OC
        card = _OC(inquiry_id=inquiry_id)
    card.leadtime_days = body.promised_days
    card.leadtime_inventory_evidence = bool(body.has_inventory_evidence)
    card.leadtime_capacity_evidence = bool(body.has_capacity_evidence)
    card = ops_card_store.update(card)
    out = _ops_card_payload(card)
    out["leadtime_gate"] = card.leadtime_gate_view()
    return out


@router.get("/suppression")
def acquisition_suppression_list(
    tenant_id: str = "demo",
    current_user: User = Depends(get_current_user),
):
    """P3-5 退订/抑制名单。"""
    return suppression_store.report(tenant_id=tenant_id)


@router.post("/suppression/add")
def acquisition_suppression_add(
    body: SuppressionRequest,
    current_user: User = Depends(get_current_user),
):
    """P3-5 加入抑制（退订/投诉）。"""
    return suppression_store.add(
        email=body.email,
        tenant_id=body.tenant_id,
        reason=body.reason,
        source=body.source,
        created_by=body.created_by,
    )


@router.post("/suppression/remove")
def acquisition_suppression_remove(
    body: SuppressionRemoveRequest,
    current_user: User = Depends(get_current_user),
):
    """P3-5 解除抑制（必须 confirm）。"""
    return suppression_store.remove(
        email=body.email,
        tenant_id=body.tenant_id,
        confirm=body.confirm,
        note=body.note,
    )


@router.post("/outreach/allow-check")
def acquisition_outreach_allow(
    body: OutreachAllowRequest,
    current_user: User = Depends(get_current_user),
):
    """P3-5 外发前抑制闸门检查。"""
    return suppression_store.check_outreach(
        email=body.email,
        tenant_id=body.tenant_id,
        channel=body.channel,
        mode=body.mode,
    )


@router.post("/payment-risk")
def acquisition_payment_risk(
    body: PaymentRiskRequest,
    current_user: User = Depends(get_current_user),
):
    """P3-6 付款风险闸：高风险阻断自动 PI。"""
    card = ops_card_store.get_by_inquiry(body.inquiry_id) if body.inquiry_id else None
    return payment_risk_gate(
        country=body.country,
        buyer_type=body.buyer_type,
        buyer_grade=card.buyer_grade if card else "",
        risk_flags=list(body.risk_flags or []),
        deposit_ratio=body.deposit_ratio,
        stage=card.stage if card else "",
        auto_pi=bool(body.auto_pi),
        ops_store=ops_card_store,
        inquiry_id=body.inquiry_id,
    )


class KnowledgeMarkRequest(BaseModel):
    item_id: str
    action: str = "done"  # done / reset
    by: str = "sales"
    tenant_id: str = "demo"


class RiskScanRequest(BaseModel):
    inquiry_id: str
    result: str = "unknown"  # clear/watch/blocked/unknown
    source: str = "manual"
    note: str = ""
    country: str = ""
    risk_flags: List[str] = Field(default_factory=list)
    tenant_id: str = "demo"


@router.get("/knowledge-queue")
def acquisition_knowledge_queue(
    tenant_id: str = "demo",
    category: str = "",
    only_pending: bool = False,
    current_user: User = Depends(get_current_user),
):
    """P3-8 阅读知识队列（认证/诈骗/合规）。"""
    return knowledge_queue_store.report(tenant_id=tenant_id) if not (category or only_pending) else {
        **knowledge_queue_store.report(tenant_id=tenant_id),
        "items": knowledge_queue_store.list(tenant_id=tenant_id, category=category, only_pending=only_pending),
    }


@router.post("/knowledge-queue/mark")
def acquisition_knowledge_mark(
    body: KnowledgeMarkRequest,
    current_user: User = Depends(get_current_user),
):
    """P3-8 标记知识已读/重置。"""
    if not (body.item_id or "").strip():
        raise HTTPException(status_code=400, detail="item_id required")
    if body.action == "reset":
        return knowledge_queue_store.mark_pending(body.item_id.strip())
    return knowledge_queue_store.mark_done(body.item_id.strip(), by=body.by)


@router.get("/risk-rescan")
def acquisition_risk_rescan(
    tenant_id: str = "demo",
    rescan_days: int = 90,
    current_user: User = Depends(get_current_user),
):
    """P3-4 制裁/风险名单重扫 + 真名单源筛查。"""
    return risk_rescan_store.report(
        ops_store=ops_card_store,
        tenant_id=tenant_id,
        rescan_days=max(1, min(365, rescan_days)),
        external_list_configured=None,
        auto_screen=True,
    )


class SanctionsScreenRequest(BaseModel):
    name: str = ""
    email: str = ""
    company: str = ""
    domain: str = ""
    inquiry_id: str = ""


@router.get("/sanctions/source")
def acquisition_sanctions_source(current_user: User = Depends(get_current_user)):
    """P3-4 名单源状态（是否已配置真源）。"""
    return list_source_status()


@router.post("/sanctions/screen")
def acquisition_sanctions_screen(
    body: SanctionsScreenRequest,
    current_user: User = Depends(get_current_user),
):
    """P3-4 对公司/邮箱做名单筛查。"""
    out = screen_subject(
        name=body.name,
        email=body.email,
        company=body.company,
        domain=body.domain,
    )
    if body.inquiry_id:
        result = str(out.get("result") or "unknown")
        if result in ("blocked", "watch"):
            risk_rescan_store.mark_scanned(
                body.inquiry_id,
                result=result,
                source=str(out.get("source") or "sanctions_list"),
                note=str(out.get("plain") or "")[:200],
            )
            card = ops_card_store.get_by_inquiry(body.inquiry_id)
            if card is not None:
                card.risk_flags = list(set(card.risk_flags + [f"sanctions_{result}"]))
                ops_card_store.update(card)
    out["inquiry_id"] = body.inquiry_id
    return out


class TenderUpsertRequest(BaseModel):
    tender_id: str = ""
    inquiry_id: str = ""
    tenant_id: str = "demo"
    buyer_name: str = ""
    project_name: str = ""
    amount: float = 0
    currency: str = "USD"


class TenderDocRequest(BaseModel):
    tender_id: str
    doc_key: str
    ready: bool = True


class TenderAdvanceRequest(BaseModel):
    tender_id: str
    to_stage: str
    note: str = ""
    payment_terms: str = ""
    credit_ok: bool = False


@router.get("/tender/{tender_id}")
def acquisition_tender_view(
    tender_id: str,
    current_user: User = Depends(get_current_user),
):
    """P3-7 招投标/经销商项目视图。"""
    return tender_engine.view(tender_id)


@router.post("/tender/upsert")
def acquisition_tender_upsert(
    body: TenderUpsertRequest,
    current_user: User = Depends(get_current_user),
):
    """P3-7 创建/更新大单项目。"""
    proj = tender_engine.upsert(
        tender_id=body.tender_id,
        inquiry_id=body.inquiry_id,
        tenant_id=body.tenant_id,
        buyer_name=body.buyer_name,
        project_name=body.project_name,
        amount=body.amount,
        currency=body.currency,
    )
    return tender_engine.view(proj.tender_id)


@router.post("/tender/doc")
def acquisition_tender_doc(
    body: TenderDocRequest,
    current_user: User = Depends(get_current_user),
):
    """P3-7 资质包勾选。"""
    return tender_engine.mark_doc(body.tender_id, body.doc_key, body.ready)


@router.post("/tender/advance")
def acquisition_tender_advance(
    body: TenderAdvanceRequest,
    current_user: User = Depends(get_current_user),
):
    """P3-7 阶段推进（资质不齐禁止投标提交）。"""
    if body.payment_terms or body.credit_ok:
        tender_engine.set_payment(body.tender_id, body.payment_terms, body.credit_ok)
    out = tender_engine.advance(body.tender_id, body.to_stage, note=body.note)
    # 同步跟单卡备注
    if out.get("ok") and body.inquiry_id if hasattr(body, "inquiry_id") else False:
        pass
    return out


@router.post("/ops-card/{inquiry_id}/tender")
def ops_card_tender_bind(
    inquiry_id: str,
    body: TenderUpsertRequest,
    current_user: User = Depends(get_current_user),
):
    """P3-7 跟单卡绑定大单项目 + 备注。"""
    proj = tender_engine.upsert(
        tender_id=body.tender_id or f"TDR-{inquiry_id}",
        inquiry_id=inquiry_id,
        tenant_id=body.tenant_id or "demo",
        buyer_name=body.buyer_name,
        project_name=body.project_name,
        amount=body.amount,
        currency=body.currency,
    )
    card = ops_card_store.get_by_inquiry(inquiry_id)
    if card is None:
        card = ops_card_store.materialize(tenant_id=proj.tenant_id, inquiry_id=inquiry_id)
    card = ops_card_store.add_note(
        inquiry_id,
        author="tender_engine",
        body=f"绑定大单 {proj.tender_id}：{proj.project_name}；阶段={proj.stage}",
        pinned=True,
    )
    out = _ops_card_payload(card)
    out["tender"] = tender_engine.view(proj.tender_id)
    return out


@router.get("/ops/reconcile")
def acquisition_billing_reconcile(
    tenant_id: str = "demo",
    window_hours: int = 24,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """E-5 meter vs ledger 对账（只读）。优先只读会话。"""
    session = _resolve_db(db)
    if session is None:
        try:
            with get_read_session() as rs:
                return billing_reconcile(rs, tenant_id=tenant_id, window_hours=window_hours)
        except Exception:
            pass
    return billing_reconcile(session, tenant_id=tenant_id, window_hours=window_hours)


@router.post("/risk-rescan/mark")
def acquisition_risk_rescan_mark(
    body: RiskScanRequest,
    current_user: User = Depends(get_current_user),
):
    """P3-4 登记一次名单重扫结果。"""
    if not (body.inquiry_id or "").strip():
        raise HTTPException(status_code=400, detail="inquiry_id required")
    out = risk_rescan_store.mark_scanned(
        body.inquiry_id.strip(),
        result=body.result,
        source=body.source,
        note=body.note,
        country=body.country,
        risk_flags=list(body.risk_flags or []),
    )
    card = ops_card_store.get_by_inquiry(body.inquiry_id.strip())
    if card is not None:
        card.risk_flags = list(body.risk_flags or [])
        card = ops_card_store.update(card)
        out["card_payment_risk"] = card.payment_risk_view()
    else:
        out["card_payment_risk"] = None
    return out


class RateLimitProbeRequest(BaseModel):
    tenant_id: str = "demo"
    action: str = "acq_api"
    times: int = 1


@router.post("/rate-limit/probe")
def acquisition_rate_limit_probe(
    body: RateLimitProbeRequest,
    current_user: User = Depends(get_current_user),
):
    """E-3 限流探测（开发/联调）。超限返回 429 语义结构。"""
    last = None
    for _ in range(max(1, min(20, int(body.times)))):
        last = acq_rate_limiter.check(tenant_id=body.tenant_id, action=body.action)
    return last or {"allowed": True, "code": "ok"}


@router.get("/rate-limit/stats")
def acquisition_rate_limit_stats(current_user: User = Depends(get_current_user)):
    """E-3 当前限流窗口占用。"""
    return acq_rate_limiter.stats()


@router.get("/ops/reconcile")
def acquisition_billing_reconcile(
    tenant_id: str = "demo",
    window_hours: int = 24,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """E-5 meter vs ledger 对账（只读）。"""
    return billing_reconcile(_resolve_db(db), tenant_id=tenant_id, window_hours=window_hours)


@router.get("/ops/queues")
def acquisition_queue_monitor(
    tenant_id: str = "demo",
    limit: int = 200,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """E-1 队列拆分监控（outreach/content/ops）。"""
    return queue_monitor_report(_resolve_db(db), tenant_id=tenant_id, limit=max(1, min(500, limit)))


@router.get("/ops/db-topology")
def acquisition_db_topology(current_user: User = Depends(get_current_user)):
    """E-2 读写分离拓扑体检（未配置读库诚实说明）。"""
    return db_topology()


@router.get("/ops/read-session-probe")
def acquisition_read_session_probe(
    current_user: User = Depends(get_current_user),
):
    """E-2 只读会话探活：证明读库/回落主库可用。"""
    try:
        with get_read_session() as session:
            from sqlalchemy import text
            db_name = session.execute(text("select current_database()")).scalar()
        topo = db_topology()
        return {
            "ok": True,
            "database": str(db_name or ""),
            "topology": topo,
            "plain_summary": f"只读会话可用，连接库 {db_name}。{topo.get('plain_summary', '')}",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": str(exc)[:200],
            "plain_summary": f"只读会话探活失败：{str(exc)[:120]}",
        }


@router.post("/ops/baseline")
def acquisition_baseline(
    n: int = 20,
    current_user: User = Depends(get_current_user),
):
    """E-6 混沌/压测基线（跟单卡写路径 + 撞单红线）。"""
    card_base = run_dispatch_baseline(ops_store=ops_card_store, n=n)
    probe_id = f"INQ-BASE-CLAIM-{uuid.uuid4().hex[:8]}"
    ops_card_store.materialize(tenant_id="demo", inquiry_id=probe_id, owner_user_id="alice")
    claim_base = run_claim_collision_baseline(
        claim_fn=lambda **kw: _claim_fn(ops_card_store, **kw),
        inquiry_id=probe_id,
    )
    return {
        "dispatch_card": card_base,
        "claim_collision": claim_base,
        "ok": bool(card_base.get("ok") and claim_base.get("ok")),
        "plain_summary": card_base.get("plain_summary", "") + " ｜ " + claim_base.get("plain_summary", ""),
    }


@router.get("/orchestration-dictionary")
def acquisition_orchestration_dictionary(
    current_user: User = Depends(get_current_user),
):
    """P1-9 编排词典 v1：≥8 条已验证航道。"""
    return {
        "version": "v1",
        "count": len(list_dictionary()),
        "routes": list_dictionary(),
        "plain_summary": dictionary_plain_summary(),
        "hint": "词典航道与智能拆解 L1 模板对齐；外发节点仍须人审。",
    }


@router.get("/outreach-gate")
def acquisition_outreach_gate(
    research_level: str = "none",
    current_user: User = Depends(get_current_user),
):
    """P1-6 开发信个性化闸：无背调禁止个性化。"""
    return evaluate_research_gate(research_level)


@router.get("/attribution/content")
def acquisition_content_attribution(
    tenant_id: str = "demo",
    current_user: User = Depends(get_current_user),
):
    """P1-7 内容获客归因报表（文章/视频 → 询盘）。"""
    return content_attr_store.report(tenant_id=tenant_id)


@router.post("/attribution/content/register")
def acquisition_content_attr_register(
    body: ContentAttrRegisterRequest,
    current_user: User = Depends(get_current_user),
):
    """登记一条内容（文章/视频/落地页）。"""
    item = content_attr_store.upsert_content(
        content_id=body.content_id,
        content_title=body.content_title,
        content_type=body.content_type,
        channel=body.channel,
        tenant_id=body.tenant_id,
        published_at=body.published_at,
    )
    return {
        "content_id": item.content_id,
        "content_title": item.content_title,
        "content_type": item.content_type,
        "channel": item.channel,
        "linked": True,
    }


@router.post("/attribution/content/link")
def acquisition_content_attr_link(
    body: ContentAttrLinkRequest,
    current_user: User = Depends(get_current_user),
):
    """询盘挂内容来源（归因可查）。"""
    return content_attr_store.link_inquiry(
        content_id=body.content_id,
        inquiry_id=body.inquiry_id,
        tenant_id=body.tenant_id,
    )


@router.get("/ip-slots")
def acquisition_ip_slots(
    tenant_id: str = "demo",
    current_user: User = Depends(get_current_user),
):
    """P1-8 IP/指纹槽位只读状态；无账本诚实 unknown。"""
    return ip_slot_catalog.list_view(tenant_id=tenant_id)


# ── Playbook ───────────────────────────────────────────────

@router.get("/playbooks")
def playbooks_list(
    country: str = "",
    buyer_type: str = "",
    current_user: User = Depends(get_current_user),
):
    items = playbook_store.match(country=country, buyer_type=buyer_type)
    return {
        "playbooks": [
            {
                "playbook_id": p.playbook_id,
                "country": p.country,
                "buyer_type": p.buyer_type,
                "payment_bias": p.payment_bias,
                "tips": p.tips,
                "warnings": p.warnings,
                "talk_tracks": p.talk_tracks,
            }
            for p in items
        ]
    }


@router.get("/playbooks/tips")
def playbooks_tips(
    country: str,
    buyer_type: str = "new",
    current_user: User = Depends(get_current_user),
):
    return {"country": country, "buyer_type": buyer_type, "tips": playbook_store.tips_for(country, buyer_type)}


# ── 回复进线一步建卡（傻子都行）────────────────────────────

@router.post("/reply-ingest")
def reply_ingest(
    body: ReplyIngestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """客户回复进线（E-3：限流）。"""
    _rate_limit_or_raise(body.tenant_id or "demo", action="reply_ingest")
    if not body.inquiry_id:
        raise HTTPException(status_code=400, detail="inquiry_id required")
    alerts: list[str] = []
    buyer_id = body.buyer_id or ""
    if body.email or body.contact_name or body.company_name:
        b = BuyerMaster(
            tenant_id=body.tenant_id,
            email=body.email,
            contact_name=body.contact_name,
            contact_gender=body.contact_gender,
            contact_title=body.contact_title,
            company_name=body.company_name,
            company_country=body.country,
            buyer_type=body.buyer_type,
            source="reply_ingest",
        )
        out, _is_new, a = buyer_store.upsert(b)
        buyer_id = out.buyer_id
        alerts.extend(a)
    grade_label, grade_reason = "", ""
    effective_type = body.buyer_type or "new"
    score = int(body.grade or 0)
    if body.grade:
        grade_label, grade_reason = score_grade(body.grade)
    tips = playbook_store.tips_for(body.country, buyer_type=effective_type) if body.country else []
    buyer = buyer_store.get(buyer_id) if buyer_id else None
    intent_analysis = classify_reply(body.message, country=body.country)
    stage = intent_analysis.get("stage_suggestion") or "engaged"
    # Spec S2.2：现卡 stage 已是 lost 则不覆盖；lost 仅由 loss API 设置
    card = ops_card_store.get_by_inquiry(body.inquiry_id)
    if card and card.stage == "lost":
        stage = "lost"
    tips = list(tips)
    if intent_analysis.get("talk_track"):
        tips.insert(0, str(intent_analysis["talk_track"]))
    # P1-2：样品意图自动点亮样品节点提示
    if intent_analysis.get("intent") == "request_sample":
        tips.insert(0, "客户要样品：确认规格/费用/运费后再寄，防样品黑洞")
    card = ops_card_store.materialize(
        tenant_id=body.tenant_id,
        inquiry_id=body.inquiry_id,
        buyer_id=buyer_id,
        owner_user_id=body.owner_user_id,
        buyer=buyer,
        grade=grade_label,
        grade_reason=grade_reason,
        playbook_tips=tips,
        stage=stage,
        score=score,
    )
    if intent_analysis.get("intent") == "request_sample":
        card = ops_card_store.update_sample(
            body.inquiry_id,
            status="requested" if (card.sample.status in ("none", "", None)) else card.sample.status,
        )
    if intent_analysis.get("intent") == "request_quote":
        card = ops_card_store.update_fulfillment_node(
            body.inquiry_id, key="quote", status="active",
            note=str(intent_analysis.get("next_action") or "补齐资格四问后报价"),
        )
    if intent_analysis.get("intent") == "payment_discuss":
        card = ops_card_store.update_fulfillment_node(
            body.inquiry_id, key="pi", status="active",
            note="确认付款方式与定金比例；写入 PI",
        )
    summary_line = (body.message or "（客户回复）").strip()[:200]
    next_at = default_next_action_at(hours=24)
    card = ops_card_store.record_touch(
        body.inquiry_id,
        channel=body.channel or "inbound",
        summary=summary_line,
        next_action=str(intent_analysis.get("next_action") or "24h 内回复；先问数量/港口/认证/付款"),
        next_action_at=next_at,
    )
    session = _resolve_db(db)
    persistence = {
        "inquiry": persist_inquiry(
            session,
            tenant_id=body.tenant_id,
            inquiry_id=body.inquiry_id,
            message=body.message,
            email=body.email,
            contact_name=body.contact_name,
            company_name=body.company_name,
            product="",
            country=body.country,
            channel=body.channel or "inbound",
            assigned_to=body.owner_user_id,
        ),
        "lead": persist_prospect_lead(
            session,
            tenant_id=body.tenant_id,
            email=body.email,
            company_name=body.company_name,
            country=body.country,
            contact_name=body.contact_name,
            contact_title=body.contact_title,
            buyer_type=body.buyer_type,
            channel=body.channel or "reply_ingest",
            inquiry_ref=body.inquiry_id,
        ),
    }
    experience = record_acquisition_event(
        session,
        tenant_id=body.tenant_id,
        event="reply_ingest",
        inquiry_id=body.inquiry_id,
        success=True,
        detail=summary_line,
        executor_id="acquisition_ops",
    )
    out = _ops_card_payload(card)
    out.update({
        "alerts": alerts,
        "buyer_id": buyer_id,
        "playbook_tips": tips,
        "persistence": persistence,
        "experience": experience,
        "intent_analysis": intent_analysis,
    })
    return out


@router.get("/followups")
def acquisition_followups(
    tenant_id: str = "demo",
    include_lost: bool = False,
    current_user: User = Depends(get_current_user),
):
    """今日待办：按逾期/到期排序的跟单卡。"""
    cards = ops_card_store.list_followups(tenant_id=tenant_id, include_lost=include_lost)
    items = []
    for c in cards:
        sla = card_sla(c)
        items.append({
            "inquiry_id": c.inquiry_id,
            "stage": c.stage,
            "owner_user_id": c.owner_user_id,
            "buyer_display": c.buyer_display,
            "buyer_grade": c.buyer_grade,
            "next_action": c.next_action,
            "next_action_at": c.next_action_at,
            "last_summary": c.last_summary,
            "summary": c.summary_lines(),
            "sla": sla,
        })
    # 紧急优先
    rank = {"overdue": 0, "due": 1, "none": 2, "closed": 3}
    items.sort(key=lambda x: rank.get(x["sla"]["sla"], 9))
    overdue = sum(1 for i in items if i["sla"].get("overdue"))
    return {
        "tenant_id": tenant_id,
        "total": len(items),
        "overdue_count": overdue,
        "items": items,
        "hint": "先处理逾期，再处理将到期；流失单不进列表。",
    }


@router.post("/translate")
def acquisition_translate(
    body: TranslateRequest,
    current_user: User = Depends(get_current_user),
):
    """获客窗口双向翻译；无引擎诚实降级。"""
    return translate_text(body.text, from_lang=body.from_lang, to_lang=body.to_lang)


@router.get("/wallet-status")
def acquisition_wallet_status(
    tenant_id: str = "demo",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Token/套餐闸状态；有账本读真余额，无账本不编造。"""
    return check_wallet_status(tenant_id, db=_resolve_db(db))


@router.get("/channels")
def acquisition_channels(current_user: User = Depends(get_current_user)):
    """获客渠道健康：real / mock / coming_soon（前端红标）。"""
    try:
        from app.services.ubrain.channel_status import get_all_channel_statuses
        items = get_all_channel_statuses()
        channels = [
            {
                "id": c.id,
                "name": c.name,
                "status": c.status,
                "reason": c.reason,
                "is_mock": c.status != "real",
            }
            for c in items
        ]
    except Exception as exc:  # noqa: BLE001
        channels = []
        return {"channels": [], "error": str(exc)[:200], "hint": "渠道状态服务不可用"}
    mock_n = sum(1 for c in channels if c.get("is_mock"))
    return {
        "channels": channels,
        "mock_count": mock_n,
        "real_count": len(channels) - mock_n,
        "hint": "标记为「演示/未配置」的渠道结果不可当作真实线索。",
    }


@router.post("/dispatch", response_model=DispatchResponse)
async def acquisition_dispatch(
    body: DispatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """作战台一键派发：拆解任务图，可选真派发（复用爱马仕 supervisor）。E-3 限流。"""
    _rate_limit_or_raise(body.tenant_id or "demo", action="dispatch")
    if not (body.intent or "").strip():
        raise HTTPException(status_code=400, detail="intent required")
    session = _resolve_db(db)
    payload = dict(body.payload or {})
    # 傻子都行：作战台派发时给履约/询盘节点补齐最小字段，避免诚实 failed=missing_name
    if body.inquiry_id:
        payload.setdefault("name", body.inquiry_id)
        payload.setdefault("inquiry_id", body.inquiry_id)
        payload.setdefault("contact_name", str(payload.get("contact_name") or body.inquiry_id))
        payload.setdefault("buyer_display", str(payload.get("buyer_display") or body.inquiry_id))
    try:
        result = await dispatch_acquisition(
            session,
            tenant_id=body.tenant_id,
            intent=body.intent,
            payload=payload,
            channel=body.channel,
            auto_dispatch=bool(body.auto_dispatch),
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422, detail=f"拆解/派发失败: {exc}") from exc

    card = None
    if body.inquiry_id:
        tips = []
        country = str((body.payload or {}).get("country") or "").upper()
        if country:
            tips = playbook_store.tips_for(country, buyer_type="new")
        card = ops_card_store.materialize(
            tenant_id=body.tenant_id,
            inquiry_id=body.inquiry_id,
            stage="orchestrated",
            playbook_tips=tips,
        )
        card = ops_card_store.add_note(
            body.inquiry_id,
            author="system",
            body=f"已智能拆派 plan={result.get('plan_id')} source={result.get('graph_source')} dispatched={result.get('dispatched')}",
            pinned=True,
        )

    exp = record_acquisition_event(
        session,
        tenant_id=body.tenant_id,
        event="ops_dispatch",
        inquiry_id=body.inquiry_id,
        success=bool(result.get("dispatched")) or not body.auto_dispatch,
        detail=f"intent={body.intent}; plan={result.get('plan_id')}; dispatched={result.get('dispatched')}",
        executor_id="acquisition_dispatch",
    )
    return DispatchResponse(
        plan_id=str(result.get("plan_id") or ""),
        graph_source=str(result.get("graph_source") or ""),
        node_count=int(result.get("node_count") or 0),
        nodes=list(result.get("nodes") or []),
        approval_required=list(result.get("approval_required") or []),
        dispatched=bool(result.get("dispatched")),
        task_ids=list(result.get("task_ids") or []),
        plan_task_id=str(result.get("plan_task_id") or ""),
        dispatch_error=str(result.get("dispatch_error") or ""),
        persistence_note=str(result.get("persistence_note") or ""),
        experience=exp,
        card=card.to_dict() if card else None,
    )
