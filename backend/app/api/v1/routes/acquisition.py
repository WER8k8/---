# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""获客 API：编排图预览 · 跟单卡 · Playbook。

挂在 /api/v1 下；与既有 orchestration 路由互补，不替代。
权限：复用 get_current_user；测试环境允许无依赖构造。
"""
from __future__ import annotations

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.hermes_orchestration import IntentEvent
from app.services.acquisition import (
    BuyerMaster,
    buyer_store,
    ops_card_store,
    playbook_store,
    score_grade,
)
from app.services.acquisition.translate_service import translate_text
from app.services.acquisition.wallet_guard import check_wallet_status

# FIX-30：router 自带 prefix="/acquisition"，auto_discovery 必须用空外挂前缀，
# 否则会变成 /api/v1/acquisition/acquisition/*（前端 404）。
ROUTE_PREFIX = ""
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


# ── 编排图预览（好用：先看懂再执行）─────────────────────────

@router.post("/intent/preview", response_model=IntentPreviewResponse)
async def intent_preview(
    body: IntentPreviewRequest,
    current_user: User = Depends(get_current_user),
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
    return IntentPreviewResponse(
        plan_id=graph.plan_id,
        source=source,
        strategy=graph.strategy,
        approval_required=approval,
        nodes=nodes,
        skill_refs=skill_refs,
        playbook_tips=tips,
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
    )
    return {"card": card.to_dict(), "summary": card.summary_lines()}


@router.get("/ops-card/{inquiry_id}")
def ops_card_get(inquiry_id: str, current_user: User = Depends(get_current_user)):
    card = ops_card_store.get_by_inquiry(inquiry_id)
    if not card:
        raise HTTPException(status_code=404, detail="ops_card_not_found")
    return {"card": card.to_dict(), "summary": card.summary_lines()}


@router.post("/ops-card/{inquiry_id}/touch")
def ops_card_touch(
    inquiry_id: str,
    body: OpsCardTouchRequest,
    current_user: User = Depends(get_current_user),
):
    card = ops_card_store.record_touch(
        inquiry_id,
        channel=body.channel,
        summary=body.summary,
        next_action=body.next_action,
        next_action_at=body.next_action_at,
    )
    return {"card": card.to_dict(), "summary": card.summary_lines()}


@router.post("/ops-card/{inquiry_id}/note")
def ops_card_note(
    inquiry_id: str,
    body: OpsCardNoteRequest,
    current_user: User = Depends(get_current_user),
):
    card = ops_card_store.add_note(inquiry_id, body.author, body.body, body.pinned)
    return {"card": card.to_dict(), "summary": card.summary_lines()}


@router.post("/ops-card/{inquiry_id}/loss")
def ops_card_loss(
    inquiry_id: str,
    body: OpsCardLossRequest,
    current_user: User = Depends(get_current_user),
):
    card = ops_card_store.record_loss(inquiry_id, body.reasons, body.note)
    return {"card": card.to_dict(), "summary": card.summary_lines()}


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
):
    """客户回复 → 身份锁建档（可选）→ 跟单卡 → 记跟进。"""
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
    if body.grade:
        grade_label, grade_reason = score_grade(body.grade)
    tips = playbook_store.tips_for(body.country, buyer_type=effective_type) if body.country else []
    buyer = buyer_store.get(buyer_id) if buyer_id else None
    card = ops_card_store.materialize(
        tenant_id=body.tenant_id,
        inquiry_id=body.inquiry_id,
        buyer_id=buyer_id,
        owner_user_id=body.owner_user_id,
        buyer=buyer,
        grade=grade_label,
        grade_reason=grade_reason,
        playbook_tips=tips,
    )
    summary_line = (body.message or "（客户回复）").strip()[:200]
    card = ops_card_store.record_touch(
        body.inquiry_id,
        channel=body.channel or "inbound",
        summary=summary_line,
        next_action="24h 内回复；先问数量/港口/认证/付款",
    )
    return {
        "card": card.to_dict(),
        "summary": card.summary_lines(),
        "alerts": alerts,
        "buyer_id": buyer_id,
        "playbook_tips": tips,
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
):
    """Token/套餐闸状态；无账本不编造。"""
    return check_wallet_status(tenant_id)
