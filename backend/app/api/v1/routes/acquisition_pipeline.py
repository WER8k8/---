# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
获客全链路极智升维 API 路由 (Ultimate Acquisition Pipeline Routes)。

包含：
1. 360° 全球买家画像透视与反查
2. AI 极智千人千面多语种破冰开发信工坊
3. 7 步出海高转化节奏编排器
4. 外贸 8 大经典抗拒智能谈判助攻中枢
5. 线索一键无缝跃迁至 BOQ 工业核价与履约 PI
"""
from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.response import success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.services.acquisition import (
    Buyer360EnrichmentEngine,
    AIPitchStudio,
    OutboundCadenceEngine,
    ObjectionCopilot,
    ops_card_store,
)

ROUTE_PREFIX = ""

router = APIRouter(prefix="/acquisition-pipeline", tags=["外贸获客全链路极智升维"])


# ── 请求与响应 Pydantic 模型 ─────────────────────────────────────
class EnrichBuyerRequest(BaseModel):
    company_name: str = Field(..., min_length=1, description="目标买家公司名称，如 Al Fozan Group")
    domain: Optional[str] = Field("", description="买家官方网址或域名")
    country: Optional[str] = Field("SA", description="国家二字码或名称，如 SA, AE, US, DE")
    industry_hint: Optional[str] = Field("stone", description="品类偏好提示 (stone/ceramic/steel/wood/glass)")


class GeneratePitchRequest(BaseModel):
    company_name: str = Field(..., min_length=1, description="目标公司名称")
    country: Optional[str] = Field("Saudi Arabia", description="目标国家")
    product_category: Optional[str] = Field("Porcelain Tiles & Marble Slabs", description="产品主推品类")
    contact_person: Optional[str] = Field("Procurement Director", description="决策人称呼/职务")
    pain_point: Optional[str] = Field("Lead time delays and container overweight risks", description="买家核心痛点")
    research_level: Optional[str] = Field("basic", description="背调等级 (none/basic/osint/full)")
    language: Optional[str] = Field("en", description="语言 (en/ar/es/ru/pt/fr)")


class CadencePlanRequest(BaseModel):
    company_name: str = Field(..., min_length=1, description="买家公司名称")
    country: Optional[str] = Field("SA", description="目标国家二字码 (SA/AE/DE/US/IN)")
    product_category: Optional[str] = Field("Ceramic & Stone", description="主打建材品类")


class ObjectionAssistRequest(BaseModel):
    objection_key: str = Field("price_high", description="抗拒场景 key，如 price_high, long_oa, quality_cert 等")


class HandoffToQuoteRequest(BaseModel):
    lead_id: Optional[str] = Field("", description="线索编号或询盘编号")
    buyer_name: str = Field(..., description="买家公司名称")
    country: Optional[str] = Field("SA", description="国家")
    product_category: Optional[str] = Field("marble", description="品类 (marble, granite, ceramic, steel)")
    target_port: Optional[str] = Field("Jeddah Islamic Port", description="目的港")
    estimated_sqm: Optional[float] = Field(1200.0, description="预估采购数量 (SQM 或 Unit)")
    unit_price: Optional[float] = Field(0.0, description="单价 USD")
    total_amount: Optional[float] = Field(0.0, description="总金额 USD（优先于 数量×单价）")
    contact_email: Optional[str] = Field("", description="买家邮箱")
    note: Optional[str] = Field("", description="备注")


# ── 端点实现 ──────────────────────────────────────────────────
@router.post("/enrich-buyer", summary="360° 全球买家深度画像透视反查")
async def enrich_buyer(req: EnrichBuyerRequest):
    """根据公司名、域名与国家，秒级反查采购体量、目的港、决策树与合规风险。"""
    intelligence = Buyer360EnrichmentEngine.enrich_buyer(
        company_name=req.company_name,
        domain=req.domain or "",
        country=req.country or "SA",
        industry_hint=req.industry_hint or "stone",
    )
    return success_response(data=intelligence)


@router.post("/generate-pitch", summary="AI 极智千人千面多语种破冰开发信工坊")
async def generate_pitch(req: GeneratePitchRequest):
    """遵循 P1-6 严格背调门禁，生成 Cold Email、WhatsApp 黄金 3 行钩子与 LinkedIn 邀约。"""
    pitch_data = AIPitchStudio.generate_pitch(
        company_name=req.company_name,
        country=req.country or "Saudi Arabia",
        product_category=req.product_category or "Porcelain Tiles & Marble Slabs",
        contact_person=req.contact_person or "Procurement Director",
        pain_point=req.pain_point or "Lead time delays and container overweight risks",
        research_level=req.research_level or "basic",
        language=req.language or "en",
    )
    return success_response(data=pitch_data)


@router.post("/cadence-plan", summary="7 步出海高转化节奏时区编排器")
async def cadence_plan(req: CadencePlanRequest):
    """基于目标国本地工作日与黄金投递时隙，生成 30 天 7 轮多通道跟进节奏。"""
    plan = OutboundCadenceEngine.generate_cadence_plan(
        company_name=req.company_name,
        country=req.country or "SA",
        product_category=req.product_category or "Ceramic & Stone",
    )
    return success_response(data=plan)


@router.get("/objections", summary="获取外贸 8 大经典抗拒场景列表")
async def list_objections():
    """获取外贸销售中最常见的 8 种被拒绝/被压价抗拒场景清单。"""
    items = ObjectionCopilot.list_all_objections()
    return success_response(data={"objections": items})


@router.post("/objection-assist", summary="外贸 8 大异议智能反击与谈判助攻")
async def objection_assist(req: ObjectionAssistRequest):
    """输入抗拒类型，秒级获取资深老外贸反击战术、双语话术与底牌置换条件。"""
    solution = ObjectionCopilot.get_objection_solution(req.objection_key)
    return success_response(data=solution)


@router.post("/handoff-to-quote", summary="线索一键跃迁至 BOQ 核价并落履约订单")
async def handoff_to_quote(
    req: HandoffToQuoteRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """制单/拓客 → 落报价 + 履约订单 + 跟单卡，打通黄金单闭环。"""
    from app.core.response import error_response, success_response

    try:
        from app.models.order import Order
        from app.models.quote import Quote, QuoteItem

        return _handoff_build(req, db, current_user, Order, Quote, QuoteItem, error_response)
    except Exception as exc:
        try:
            db.rollback()
        except Exception:
            pass
        return success_response(data={"ok": False, "error": str(exc), "stage": "handoff"}, message=f"handoff失败: {exc}")


def _handoff_build(req, db, current_user, Order, Quote, QuoteItem, error_response):
    import secrets
    import uuid as _uuid
    from datetime import datetime, timezone

    qty = float(req.estimated_sqm or 0) or 1.0
    unit = float(req.unit_price or 0) or 0.0
    total = float(req.total_amount or 0) or round(qty * unit, 2)
    product = (req.product_category or "").strip() or "Industrial Supplies"
    buyer = (req.buyer_name or "").strip() or "Buyer"
    inquiry_id = (req.lead_id or "").strip()
    try:
        uuid.UUID(inquiry_id)
    except (ValueError, AttributeError, TypeError):
        inquiry_id = ""

    merchant_id = getattr(current_user, "id", None)
    raw_tid = getattr(current_user, "tenant_id", None)
    tenant_id = None
    if raw_tid:
        try:
            tenant_id = uuid.UUID(str(raw_tid))
        except (ValueError, AttributeError, TypeError):
            tenant_id = None

    if not merchant_id:
        from app.core.response import error_response

        return error_response(code=400, message="缺少操作人，无法开单")

    try:
        quote = None
        if inquiry_id:
            quote = Quote(
                inquiry_id=uuid.UUID(inquiry_id),
                tenant_id=tenant_id,
                merchant_id=merchant_id,
                rfq_id=None,
                total_amount=total,
                currency="USD",
                payment_terms="T/T 30/70",
                delivery_terms="CIF" if (req.target_port or "") else "FOB",
                status="converted",
                version=1,
            )
            db.add(quote)
            db.flush()
            db.add(
                QuoteItem(
                    quote_id=quote.id if quote else None,
                    product_name=product,
                    quantity=qty,
                    unit="sqm",
                    unit_price=unit,
                    total_price=total,
                )
            )
    except Exception as exc:
        db.rollback()
        from app.core.response import error_response

        return success_response(data={"ok": False, "error": str(exc), "stage": "quote"}, message=f"建报价失败: {exc}")

    dep_ratio = 30.0
    order_number = f"ORD-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(2).upper()}"
    order = Order(
        order_number=order_number,
        buyer_id=merchant_id,
        merchant_id=merchant_id,
        tenant_id=tenant_id,
        quote_id=quote.id if quote else None,
        total_amount=total,
        currency="USD",
        status="pending",
        payment_status="pending",
        shipping_address=f"{buyer} · {req.country or ''} · {req.target_port or ''}".strip(" ·"),
        access_token=secrets.token_hex(32),
        incoterms="CIF" if (req.target_port or "") else "FOB",
        payment_terms="T/T 30/70",
        deposit_ratio=dep_ratio,
        deposit_amount=round(total * dep_ratio / 100.0, 2) if total else 0.0,
        port_of_discharge=req.target_port or None,
        inquiry_id=inquiry_id or None,
        customer_name=buyer,
        product_summary=product,
    )
    db.add(order)
    try:
        db.commit()
        db.refresh(order)
    except Exception as exc:
        db.rollback()
        from app.core.response import error_response

        return success_response(data={"ok": False, "error": str(exc), "stage": "order"}, message=f"落单失败: {exc}")

    card_inquiry = inquiry_id or str(order.id)
    try:
        card = ops_card_store.materialize(
            tenant_id=str(raw_tid or "demo"),
            inquiry_id=card_inquiry,
            owner_user_id=str(merchant_id or ""),
            stage="quoted",
        )
        card.buyer_display = buyer
        if not card.sku_lines:
            from app.services.acquisition import OpsCardSkuLine

            card.sku_lines = [
                OpsCardSkuLine(
                    name=product,
                    qty=qty,
                    price=unit,
                    currency="USD",
                )
            ]
        ops_card_store.update(card)
    except Exception:
        # 跟单卡失败不回滚订单
        pass

    return success_response(
        data={
            "order_id": str(order.id),
            "order_number": order.order_number,
            "quote_id": str(quote.id) if quote else "",
            "inquiry_id": card_inquiry,
            "buyer_name": buyer,
            "product": product,
            "total_amount": float(total),
            "currency": "USD",
            "status": order.status.value if hasattr(order.status, "value") else str(order.status),
            "recommended_route": "/client/queues/fulfillment",
            "message": "已落报价与履约订单，去履约队列推进定金→发货→尾款→成单。",
        },
        message="已生成报价并进入履约队列",
    )
