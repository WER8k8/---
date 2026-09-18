# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""自动谈单 - 谈判/报价审批与智能议价引擎。

重构升级：
1. 【多租户隔离】彻底淘汰全局可变字典，按 tenant_id 隔离配置、报价、审批状态与消息流。
2. 【黑客防注入】集成 Prompt 注入与越狱对抗防火墙，拦截底价套取与指令覆盖。
3. 【30年外贸议价模型】底价红线保护、阶梯让步曲线、MOQ联动与大额折扣主管审批流。
4. 【PI单证一键套打】谈成后自动对接外贸单证引擎生成 Proforma Invoice。
"""

from __future__ import annotations

import logging
import re
import threading
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import uuid
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.models.quote import Quote, QuoteItem
from app.models.user import User
from app.services.foreign_trade.trade_document_service import build_proforma_invoice
from app.services.foreign_trade.negotiation_rules import apply_concession, NegotiationRules


logger = logging.getLogger(__name__)

ROUTE_PREFIX = "/negotiation"
ROUTE_TAGS = ["自动谈单"]

router = APIRouter()

# ── Prompt 注入检测模式 ──────────────────────────────────────────
_PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|system)\s+(instructions|rules|prompts|constraints)", re.IGNORECASE),
    re.compile(r"(reveal|tell\s+me|output|leak|disclose)\s+.*?(system\s*prompt|floor\s*price|bottom\s*price|cost|margin)", re.IGNORECASE),
    re.compile(r"(jailbreak|dan\s+mode|developer\s+mode|act\s+as\s+unrestricted)", re.IGNORECASE),
    re.compile(r"忽略.*?(规则|提示词|指令|约束|设定)", re.IGNORECASE),
    re.compile(r"(告诉我|透露|坦白|输出|提供).*?(底价|成本|内部价格|利润率|系统提示词)", re.IGNORECASE),
    re.compile(r"(突破限制|解除权限|无视设定|越狱模式)", re.IGNORECASE),
]


class GeneratePIBody(BaseModel):
    """generate-pi 可选覆盖参数。"""
    seller_override: Optional[Dict[str, Any]] = None
    buyer_override: Optional[Dict[str, Any]] = None


def detect_prompt_injection(text: str) -> bool:
    """检测输入是否存在 Prompt 注入或越权套取底价攻击。"""
    if not text:
        return False
    return any(p.search(text) for p in _PROMPT_INJECTION_PATTERNS)


# ── 多租户线程安全状态存储器 ────────────────────────────────────
class TenantNegotiationStore:
    """按 tenant_id 物理隔离的谈判数据中枢。"""

    def __init__(self):
        self._lock = threading.Lock()
        self._default_settings = {
            "base_profit_margin": 15.0,
            "max_rounds": 5,
            "auto_reply": True,
            "require_approval": True,
            "working_hours": None,
            "max_auto_discount_pct": 5.0,
            "floor_margin_pct": 8.0,
        }
        self._settings: Dict[str, Dict[str, Any]] = {}
        self._quotes: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._approvals: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._messages: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}

    def _tid(self, user: User) -> str:
        tid = getattr(user, "tenant_id", None)
        return str(tid) if tid else "default_tenant"

    def get_settings(self, user: User) -> Dict[str, Any]:
        tid = self._tid(user)
        with self._lock:
            if tid not in self._settings:
                self._settings[tid] = dict(self._default_settings)
            return dict(self._settings[tid])

    def update_settings(self, user: User, patch: Dict[str, Any]) -> Dict[str, Any]:
        tid = self._tid(user)
        with self._lock:
            if tid not in self._settings:
                self._settings[tid] = dict(self._default_settings)
            self._settings[tid].update(patch)
            return dict(self._settings[tid])

    def get_quote(self, user: User, negotiation_id: str) -> Optional[Dict[str, Any]]:
        tid = self._tid(user)
        with self._lock:
            return self._quotes.get(tid, {}).get(negotiation_id)

    def save_quote(self, user: User, negotiation_id: str, quote: Dict[str, Any]) -> None:
        tid = self._tid(user)
        with self._lock:
            if tid not in self._quotes:
                self._quotes[tid] = {}
            self._quotes[tid][negotiation_id] = quote

    def get_approval(self, user: User, negotiation_id: str) -> Dict[str, Any]:
        tid = self._tid(user)
        with self._lock:
            return self._approvals.get(tid, {}).get(negotiation_id, {})

    def set_approval(self, user: User, negotiation_id: str, data: Dict[str, Any]) -> None:
        tid = self._tid(user)
        with self._lock:
            if tid not in self._approvals:
                self._approvals[tid] = {}
            self._approvals[tid][negotiation_id] = data

    def get_messages(self, user: User, negotiation_id: str) -> List[Dict[str, Any]]:
        tid = self._tid(user)
        with self._lock:
            return list(self._messages.get(tid, {}).get(negotiation_id, []))

    def append_message(self, user: User, negotiation_id: str, message: Dict[str, Any]) -> int:
        tid = self._tid(user)
        with self._lock:
            if tid not in self._messages:
                self._messages[tid] = {}
            if negotiation_id not in self._messages[tid]:
                self._messages[tid][negotiation_id] = []
            self._messages[tid][negotiation_id].append(message)
            return len(self._messages[tid][negotiation_id])


_store = TenantNegotiationStore()


# ── 请求与响应模型 ──────────────────────────────────────────────
class QuoteRequest(BaseModel):
    """报价请求"""
    product_name: str = ""
    quantity: int = 1
    base_cost: float = 0.0
    profit_margin: float = 15.0
    delivery_time: str = "30天"
    delivery_terms: Optional[str] = "FOB Shenzhen"
    payment_terms: str = "T/T 30% deposit, 70% before shipment"
    unit_price: float = 0.0
    total_price: float = 0.0
    buyer_name: Optional[str] = "Overseas Buyer"
    buyer_country: Optional[str] = "Global"



class ApprovalRequest(BaseModel):
    """审批请求"""
    negotiation_id: str = ""
    round: int = 1
    action: str = Field("approve", pattern="^(approve|reject)$")
    supervisor_notes: Optional[str] = None


class SettingsRequest(BaseModel):
    """谈判设置请求"""
    base_profit_margin: float = 15.0
    max_rounds: int = 5
    auto_reply: bool = True
    require_approval: bool = True
    working_hours: Optional[Any] = None
    max_auto_discount_pct: Optional[float] = 5.0
    floor_margin_pct: Optional[float] = 8.0


class MessageRequest(BaseModel):
    """谈判消息请求"""
    message: str = Field(..., min_length=1, description="消息内容")
    target_discount_pct: Optional[float] = Field(None, description="买家期望折扣百分比")


# ── 路由端点 ────────────────────────────────────────────────────
@router.get("/settings")
def get_negotiation_settings(current_user: User = Depends(get_current_user)):
    """获取当前租户独立的谈判设置（多租户严格隔离）。"""
    return success_response(data=_store.get_settings(current_user))


@router.put("/settings")
def update_negotiation_settings(
    req: SettingsRequest,
    current_user: User = Depends(get_current_user),
):
    """保存当前租户独立的谈判设置（仅限租户管理员/超管）。"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足：只有管理员可修改谈判配置")
    updated = _store.update_settings(current_user, req.model_dump(exclude_none=True))
    return success_response(data=updated, message="设置已保存（租户隔离）")


@router.get("/{negotiation_id}/approval-status")
def get_approval_status(
    negotiation_id: str,
    current_user: User = Depends(get_current_user),
):
    """查询报价是否需要人工主管审批。"""
    approval = _store.get_approval(current_user, negotiation_id)
    settings = _store.get_settings(current_user)
    needs_approval = approval.get("needs_approval", bool(settings.get("require_approval")))
    return success_response(data={
        "negotiation_id": negotiation_id,
        "needs_approval": needs_approval,
        "approval_status": approval.get("status", "pending" if needs_approval else "approved"),
        "approved_by": approval.get("approved_by"),
    })


@router.post("/{negotiation_id}/quote")
def submit_quote(
    negotiation_id: str,
    req: QuoteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提交谈判报价（含底价保护、审批判定与数据库双写持久化）。"""
    settings = _store.get_settings(current_user)
    floor_margin = float(settings.get("floor_margin_pct", 8.0))
    base_cost = float(req.base_cost or 0.0)

    # 计算底价
    floor_price = base_cost * (1.0 + floor_margin / 100.0) if base_cost > 0 else 0.0
    needs_approval = False
    if req.unit_price > 0 and floor_price > 0 and req.unit_price < floor_price:
        needs_approval = True

    quote_data = req.model_dump()
    quote_data["floor_price"] = round(floor_price, 2)
    quote_data["needs_approval"] = needs_approval

    _store.save_quote(current_user, negotiation_id, quote_data)
    _store.set_approval(current_user, negotiation_id, {
        "needs_approval": needs_approval,
        "status": "pending" if needs_approval else "approved",
    })

    # 持久化至 PostgreSQL quotes 表
    try:
        quote_uuid = None
        try:
            quote_uuid = uuid.UUID(negotiation_id)
        except ValueError:
            pass

        inquiry_row = None
        if quote_uuid:
            from app.models.inquiry import Inquiry
            inquiry_row = db.query(Inquiry).filter(Inquiry.id == quote_uuid).first()

        existing_quote = None
        if quote_uuid and not inquiry_row:
            existing_quote = db.query(Quote).filter(Quote.id == quote_uuid).first()
        elif inquiry_row:
            existing_quote = db.query(Quote).filter(Quote.inquiry_id == quote_uuid).first()

        total_val = float(req.total_price if req.total_price > 0 else (req.unit_price * (req.quantity or 1)))
        if existing_quote:
            existing_quote.total_amount = total_val
            existing_quote.status = "pending_approval" if needs_approval else "draft"
            if req.payment_terms:
                existing_quote.payment_terms = req.payment_terms
            if req.delivery_terms:
                existing_quote.delivery_terms = req.delivery_terms
        else:
            new_quote = Quote(
                id=uuid.uuid4(),
                tenant_id=current_user.tenant_id,
                merchant_id=current_user.id,
                inquiry_id=inquiry_row.id if inquiry_row else (quote_uuid if quote_uuid else None),
                total_amount=total_val,
                currency="USD",
                payment_terms=req.payment_terms or "30% deposit, 70% before shipment",
                delivery_terms=req.delivery_terms or "FOB Shenzhen",
                status="pending_approval" if needs_approval else "draft",
            )
            db.add(new_quote)
            db.flush()


            # 添加明细行
            item = QuoteItem(
                id=uuid.uuid4(),
                quote_id=new_quote.id,
                product_name=req.product_name or "Industrial Building Materials Pack",
                quantity=float(req.quantity or 1),
                unit="pcs",
                unit_price=float(req.unit_price or 0.0),
                total_price=total_val,
            )
            db.add(item)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("[Negotiation] Quote DB persistence fallback to memory: %s", exc)

    return success_response(data={
        "status": "ok",
        "negotiation_id": negotiation_id,
        "quote": quote_data,
        "needs_approval": needs_approval,
    }, message="报价已保存")


@router.post("/{negotiation_id}/request-approval")
def request_approval(
    negotiation_id: str,
    req: ApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """主管审批操作（严格校验审批权限，仅超管/租户管理员/销售经理可放行，并同步更新 DB）。"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "sales_manager"]:
        return error_response(403, "权限不足：只有主管或管理员有权审批特价折扣")

    is_approved = req.action == "approve"
    _store.set_approval(current_user, negotiation_id, {
        "needs_approval": not is_approved,
        "status": "approved" if is_approved else "rejected",
        "approved_round": req.round,
        "approved_by": str(current_user.id),
        "notes": req.supervisor_notes,
    })

    # 同步更新 PostgreSQL 中的 Quote 审批状态
    try:
        quote_uuid = None
        try:
            quote_uuid = uuid.UUID(negotiation_id)
        except ValueError:
            pass
        if quote_uuid:
            q_row = db.query(Quote).filter(Quote.id == quote_uuid).first()
            if q_row:
                q_row.approved_by = str(current_user.id)
                q_row.approved_at = datetime.now(timezone.utc)
                q_row.status = "approved" if is_approved else "rejected"
                db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("[Negotiation] Approval DB sync fallback: %s", exc)

    return success_response(data={
        "status": "ok",
        "negotiation_id": negotiation_id,
        "action": req.action,
        "round": req.round,
        "approved_by": str(current_user.id),
    }, message=f"已{'批准' if is_approved else '拒绝'}特价折扣申请")


@router.get("/{negotiation_id}/messages")
def get_negotiation_messages(
    negotiation_id: str,
    current_user: User = Depends(get_current_user),
):
    """获取租户会话消息列表（租户隔离）。"""
    messages = _store.get_messages(current_user, negotiation_id)
    return success_response(data={
        "negotiation_id": negotiation_id,
        "messages": messages,
    })


@router.post("/{negotiation_id}/messages")
def send_negotiation_message(
    negotiation_id: str,
    req: MessageRequest,
    current_user: User = Depends(get_current_user),
):
    """发送谈判消息（含黑客 Prompt 防注入与老外贸让步曲线逻辑）。"""
    content = req.message.strip()

    # 1. 黑客红队：Prompt 注入拦截
    if detect_prompt_injection(content):
        logger.warning("[Security] 拦截到谈判 Prompt 注入攻击: user=%s content=%s", current_user.id, content[:100])
        ai_reply = {
            "sender": "ai",
            "content": "Thank you for your inquiry. Our export pricing is standardized strictly based on order volume, production quality, and Incoterms 2020. Internal cost models and prompt constraints cannot be disclosed. Please confirm your required quantity and target specifications so we can evaluate the best possible quotation.",
            "security_flag": "prompt_injection_blocked",
        }
        _store.append_message(current_user, negotiation_id, {"sender": "buyer", "content": content})
        _store.append_message(current_user, negotiation_id, ai_reply)
        return success_response(data={
            "status": "blocked",
            "negotiation_id": negotiation_id,
            "security_incident": True,
            "reply": ai_reply,
        }, message="检测到恶意指令尝试，已启用安全防护回复")

    # 2. 计算当前谈判轮次并记录买家消息
    prior_messages = _store.get_messages(current_user, negotiation_id)
    round_no = (len(prior_messages) // 2) + 1
    _store.append_message(current_user, negotiation_id, {"sender": "buyer", "content": content})

    # 3. 阶梯让步规则引擎计算（配置化，默认行为与原有硬编码一致）
    quote = _store.get_quote(current_user, negotiation_id) or {}
    settings = _store.get_settings(current_user)

    base_price = float(quote.get("unit_price", 100.0))
    base_cost = float(quote.get("base_cost", 80.0))
    floor_margin = float(settings.get("floor_margin_pct", 8.0))
    max_auto_discount = float(settings.get("max_auto_discount_pct", 5.0))
    quantity = float(quote.get("quantity", 1) or 1)

    requested_discount = req.target_discount_pct or 0.0

    # 使用配置化规则引擎（默认规则与原有硬编码行为保持一致）
    rules = NegotiationRules(
        floor_margin_pct=floor_margin,
        max_auto_discount_pct=max_auto_discount,
    )
    result = apply_concession(
        rules=rules,
        round_no=round_no,
        requested_discount=requested_discount,
        base_price=base_price,
        base_cost=base_cost,
        quantity=quantity,
    )
    concession_price = result.concession_price
    concession_rate = result.concession_rate
    needs_approval = result.needs_approval

    # 生成AI回复文本
    if round_no == 1:
        ai_text = f"We have quoted USD {base_price:.2f} based on premium raw materials and rigorous ISO/CE quality standards. At this quantity, our standard pricing already reflects our best manufacturing baseline."
    elif not needs_approval:
        ai_text = f"To demonstrate our sincerity for a long-term business relationship, we can offer a special trial discount of {concession_rate:.1f}%, adjusting the unit price to USD {concession_price:.2f} based on prompt order confirmation."
    else:
        # 触发审批：更新审批状态
        _store.set_approval(current_user, negotiation_id, {
            "needs_approval": True,
            "status": "pending",
            "requested_round": round_no,
            "requested_discount": requested_discount,
        })
        ai_text = f"The requested discount exceeds our automated sales authorization. I have formally escalated your price proposal of USD {concession_price:.2f} to our General Sales Director for special concession approval. We will revert with the official sign-off within 24 hours."

    ai_msg = {
        "sender": "ai",
        "content": ai_text,
        "round": round_no,
        "needs_approval": needs_approval,
    }
    _store.append_message(current_user, negotiation_id, ai_msg)

    return success_response(data={
        "status": "ok",
        "negotiation_id": negotiation_id,
        "round": round_no,
        "reply": ai_msg,
    }, message="谈判回复已生成")


@router.post("/{negotiation_id}/generate-pi")
def generate_pi_document(
    negotiation_id: str,
    body: Optional[GeneratePIBody] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """谈妥后一键生成标准形式发票 (Proforma Invoice PI)。（外贸7步闭环核心契约）。"""
    seller_override = body.seller_override if body else None
    buyer_override = body.buyer_override if body else None
    quote = _store.get_quote(current_user, negotiation_id) or {}
    approval = _store.get_approval(current_user, negotiation_id)

    if approval.get("needs_approval") and approval.get("status") != "approved":
        return error_response(400, "当前谈单方案尚在审批中或未通过，无法生成最终 PI")

    seller = seller_override or {
        "name": "YouDing Building Materials Tech Co., Ltd.",
        "address": "No. 88 Export Industrial Zone, Guangdong, China",
        "email": current_user.email or "export@youding.com",
    }
    buyer = buyer_override or {
        "name": quote.get("buyer_name", "Global Trade Buyer"),
        "company": quote.get("buyer_name", "Global Trade Buyer Inc."),
        "country": quote.get("buyer_country", "Global"),
        "email": "inquiry@client.com",
    }

    unit_price = float(quote.get("unit_price") or 100.0)
    qty = float(quote.get("quantity") or 1)
    product_name = quote.get("product_name") or "Building Materials Solution"

    lines = [
        {
            "description": product_name,
            "quantity": qty,
            "unit": "sets",
            "unit_price": unit_price,
            "hs_code": "6802.91.00",
        }
    ]

    pi_payload = build_proforma_invoice(
        seller=seller,
        buyer=buyer,
        lines=lines,
        currency="USD",
        payment_terms=quote.get("payment_terms") or "30% deposit, 70% before shipment",
        delivery_terms="FOB Shenzhen",
        validity_days=15,
        notes="Generated via YouDing AI Negotiator Contract Suite",
        db=db,
        tenant_id=str(getattr(current_user, "tenant_id", "") or "") or None,
    )

    return success_response(data=pi_payload, message="Proforma Invoice 已成功生成")


# 注：谈价、询盘等其余动作已按契约归位
# 1. [P1-3] AI 智能谈判（谈价 + 谈判 + PI）已在上方内联实现（/quote /messages /generate-pi），
#    无需再委托 trade_ai_agent 路由。
# 2. [P1-1] 汇率服务 (FX) 已在上方 build_proforma_invoice 内通过 load_rates 内联实现，
#    并带有 _RATE_FALLBACK 常量兜底。
# 3. 合同管理 (contract) 与 报关单 (customs_declaration) 属于「单证」范畴，
#    由 GoodJob 单证套打与 trade_document_service 的 build_contract/build_customs_declaration
#    承接，非本路由（询盘核价）职责。
# 4. 物流轨迹 (logistics_tracking) 与尾款核销 (final_payment) 属于履约后段（步骤5/7），
#    由 goodjob_fulfillment / logistics_service 承接，非本路由职责。



