# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""归因服务 — 连接各模块的自动化桥接层。

Connection ②: GEO Low Score → 自动重试内容生成
Connection ③: Customer Finder → Inquiry 自动创建
Connection ④: Email Reply → Auto-Create Negotiation
Connection ⑥: Full Funnel Attribution Report
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.inquiry import Inquiry
from app.models.social_interaction import SocialInteraction

logger = logging.getLogger("uj-admin.attribution")


# ═══════════════════════════════════════════════
# Connection ③: Customer Finder → Inquiry 自动创建
# ═══════════════════════════════════════════════

def create_inquiry_from_customer_finder(
    db: Session,
    customer: dict[str, Any],
    *,
    tenant_id: Optional[str] = None,
) -> Optional[Inquiry]:
    """从 Customer Finder 结果自动创建 Inquiry 记录（带事务保护）。

    Args:
        db: 数据库会话
        customer: Customer Finder 返回的客户字典，需包含 name/email/phone 等
        tenant_id: 租户 ID（可选）

    Returns:
        创建的 Inquiry 实例，或 None（如缺少必要字段或事务失败）
    """
    from sqlalchemy.exc import SQLAlchemyError
    name = (customer.get("name") or customer.get("company_name") or "").strip()
    email = (customer.get("email") or "").strip()
    phone = (customer.get("phone") or customer.get("contact_phone") or "").strip()
    if not name or not (email or phone):
        logger.warning("Customer Finder result missing name or contact info, skip: %s", customer.get("id"))
        return None

    company = customer.get("company_name") or customer.get("company") or name
    industry = customer.get("industry") or customer.get("category") or ""
    evidence_url = customer.get("evidence_url") or customer.get("source_url") or customer.get("url") or ""
    customer_finder_id = customer.get("id") or customer.get("customer_finder_id") or ""
    inquiry = Inquiry(
        name=name[:100],
        phone=phone[:50] if phone else "",
        email=email[:200] if email else None,
        message=f"Customer Finder 自动导入: {company} - {industry}",
        source_channel="customer_finder",
        attribution_channel="customer_finder",
        source_url=evidence_url[:1000] if evidence_url else None,
        customer_finder_id=str(customer_finder_id)[:36] if customer_finder_id else None,
        status="pending",
        tenant_id=tenant_id,
    )
    db.add(inquiry)
    try:
        db.commit()
        logger.info(
            "Auto-created Inquiry from Customer Finder: id=%s name=%s company=%s",
            inquiry.id, name, company,
        )
        return inquiry
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Failed to create Inquiry from Customer Finder (transaction rolled back): %s", exc)
        return None


# ═══════════════════════════════════════════════
# Connection ②: GEO Low Score → 自动重试内容生成
# ═══════════════════════════════════════════════

# 每个 reason 对应的人类化反馈指令
_REASON_FEEDBACK: dict[str, str] = {
    "ai_taste_high": "AI味过高，减少套话，用一线销售/工程经理口吻重写",
    "low_stat_density": "增加可验证数据（密度、价格、货期、国标编号、MOQ）",
    "low_human_signal": "增加行业真人信号（工地现场、报价比对、客户反馈、发货/到货）",
    "low_faq_format": "添加FAQ格式（问：/答：短句，答案50-120字），提升LLM引用吸收率",
    "weak_brand_anchor": "首段锚定：品牌名+产品品类+地域，三要素缺一不可",
}

MAX_RETRIES = 3


async def _run_quality_retry_loop(
    generate_fn,
    score_fn,
    prompt_builder,
    max_retries,
    initial_score_obj,
    best_content,
    best_score_obj,
    best_quality_dict,
    best_attempt,
    attempts,
    retry_feedbacks,
):
    """执行质量重试循环，返回更新后的 (attempts, best_content, best_score_obj, best_quality_dict, best_attempt, retry_feedbacks)。"""
    from app.services.geo.geo_writing_policy import content_quality_to_dict
    score_obj = initial_score_obj
    for retry_idx in range(max_retries):
        # 根据不通过原因构建反馈
        reasons = score_obj.reasons or []
        feedbacks = [_REASON_FEEDBACK.get(r, f"改进: {r}") for r in reasons]
        feedback_text = "；".join(feedbacks) if feedbacks else "AI味过高，减少套话；增加可验证数据"
        # 构建重试 prompt
        retry_prompt = prompt_builder(feedback_text)
        retry_feedbacks.append(feedback_text)
        logger.info(
            "Content quality retry %d/%d — reasons: %s, feedback: %s",
            retry_idx + 1, max_retries, reasons, feedback_text,
        )
        try:
            content = await generate_fn(retry_prompt)
        except Exception as exc:
            logger.warning("Content generation retry %d failed: %s", retry_idx + 1, exc)
            continue

        attempts += 1
        score_obj = score_fn(content)
        quality_dict = content_quality_to_dict(score_obj)
        # 用综合分数选出最佳（passed 优先，然后看 geo_citation_score - ai_taste_score）
        current_metric = (
            (1.0 if score_obj.passed else 0.0) * 10
            + score_obj.geo_citation_score
            - score_obj.ai_taste_score
        )
        best_metric = (
            (1.0 if best_score_obj.passed else 0.0) * 10
            + best_score_obj.geo_citation_score
            - best_score_obj.ai_taste_score
        )
        if current_metric > best_metric:
            best_content = content
            best_score_obj = score_obj
            best_quality_dict = quality_dict
            best_attempt = attempts

        if score_obj.passed:
            logger.info("Content quality passed on attempt %d", attempts)
            break

    return attempts, best_content, best_score_obj, best_quality_dict, best_attempt, retry_feedbacks


async def generate_with_quality_retry(
    *,
    generate_fn: Callable[..., Any],
    score_fn: Callable[[str], Any],
    prompt_builder: Callable[[str], str],
    initial_prompt: str,
    domain: str = "",
    keywords: str = "",
    max_retries: int = MAX_RETRIES,
) -> dict[str, Any]:
    """带质量重试的内容生成包装器。

    流程：生成 → 评分 → 不通过则附反馈重试 → 返回最优结果。

    Args:
        generate_fn: 异步内容生成函数，签名 async (prompt: str) -> str
        score_fn: 质量评分函数，签名 (content: str) -> ContentQualityScore
        prompt_builder: 根据反馈构建重写 prompt 的函数，签名 (feedback: str) -> str
        initial_prompt: 初始生成 prompt
        domain: 业务领域
        keywords: 目标关键词
        max_retries: 最大重试次数（默认 3）

    Returns:
        {
            "content": str,          # 最终内容
            "quality": dict,         # 最终质量分数
            "attempts": int,         # 总尝试次数
            "best_attempt": int,     # 最佳结果是第几次
            "retry_feedbacks": list, # 每次重试使用的反馈
        }
    """
    from app.services.geo.geo_writing_policy import content_quality_to_dict
    best_content = ""
    best_score_obj = None
    best_quality_dict: dict[str, Any] = {}
    retry_feedbacks: list[str] = []
    attempts = 0
    # 第一次生成
    try:
        content = await generate_fn(initial_prompt)
    except Exception as exc:
        logger.error("Initial content generation failed: %s", exc)
        return {
            "content": "",
            "quality": {},
            "attempts": 1,
            "best_attempt": 0,
            "retry_feedbacks": [],
            "error": str(exc),
        }

    attempts = 1
    score_obj = score_fn(content)
    best_content = content
    best_score_obj = score_obj
    best_quality_dict = content_quality_to_dict(score_obj)
    best_attempt = 1
    # 如果已通过，直接返回
    if score_obj.passed:
        logger.info("Content quality passed on attempt 1 (score=%s)", best_quality_dict)
        return {
            "content": best_content,
            "quality": best_quality_dict,
            "attempts": 1,
            "best_attempt": 1,
            "retry_feedbacks": [],
        }

    attempts, best_content, best_score_obj, best_quality_dict, best_attempt, retry_feedbacks = await _run_quality_retry_loop(
        generate_fn, score_fn, prompt_builder, max_retries, score_obj,
        best_content, best_score_obj, best_quality_dict, best_attempt, attempts, retry_feedbacks,
    )
    logger.info(
        "Content generation finished: attempts=%d best_attempt=%d passed=%s",
        attempts, best_attempt, best_quality_dict.get("passed"),
    )
    return {
        "content": best_content,
        "quality": best_quality_dict,
        "attempts": attempts,
        "best_attempt": best_attempt,
        "retry_feedbacks": retry_feedbacks,
    }


# ═══════════════════════════════════════════════
# Connection ④: Email Reply → Auto-Create Negotiation
# ═══════════════════════════════════════════════

_INQUIRY_KEYWORDS = (
    "interested", "quote", "price", "order", "sample", "trial",
    "报价", "价格", "下单", "样品", "感兴趣", "合作", "采购", "询价",
)
_PRICE_KEYWORDS = (
    "discount", "negotiate", "cheaper", "budget",
    "优惠", "折扣", "便宜", "能不能少",
)


def _classify_email_intent(subject: str, body: str) -> str:
    """Classify email reply intent (same taxonomy as social_interaction_service)."""
    text = f"{subject or ''} {body or ''}".lower()
    for kw in _INQUIRY_KEYWORDS:
        if kw in text:
            return "inquiry"
    for kw in _PRICE_KEYWORDS:
        if kw in text:
            return "price"
    return "general"


def _extract_product_from_subject(subject: str) -> str:
    """Best-effort product extraction from email subject."""
    if not subject:
        return ""
    clean = subject
    for prefix in ("re:", "fw:", "fwd:", "回复:", "转发:"):
        while clean.lower().startswith(prefix):
            clean = clean[len(prefix):].strip()
    return clean[:200]


def _find_campaign_inquiry(
    db: Session,
    sender_email: str,
    subject: str,
    tenant_id: Optional[str] = None,
) -> Optional[Inquiry]:
    """
    Match an incoming email reply to the original outreach inquiry.

    Strategy (best-effort):
    1. Match by email + source_channel containing "email".
    2. Fallback: match by email only (most recent).
    """
    base = db.query(Inquiry).filter(Inquiry.is_active)
    if tenant_id:
        base = base.filter(Inquiry.tenant_id == tenant_id)

    email_channel_match = (
        base.filter(Inquiry.email == sender_email)
        .filter(Inquiry.source_channel.ilike("%email%"))
        .order_by(Inquiry.created_at.desc())
        .first()
    )
    if email_channel_match:
        return email_channel_match

    fallback = (
        base.filter(Inquiry.email == sender_email)
        .order_by(Inquiry.created_at.desc())
        .first()
    )
    return fallback


def _create_email_reply_interaction(
    db: Session,
    sender_email: str,
    body: str,
    intent: str,
    matched_tenant_id: Optional[str],
    campaign_inquiry,
) -> "SocialInteraction":
    """创建 email_reply 类型的 SocialInteraction 记录并更新关联 campaign inquiry 归因。"""
    interaction = SocialInteraction(
        id=str(uuid.uuid4()),
        tenant_id=matched_tenant_id or "",
        platform="email",
        interaction_type="email_reply",
        platform_post_id=None,
        platform_comment_id=None,
        author_name=sender_email.split("@")[0] if "@" in sender_email else sender_email,
        author_platform_id=sender_email,
        content=body[:5000] if body else "",
        intent=intent,
        status="pending",  # pending → draft_ready → approved → sent
        draft_reply=None,
        final_reply=None,
        inquiry_id=str(campaign_inquiry.id) if campaign_inquiry else None,
    )
    db.add(interaction)
    # If we matched a campaign inquiry, update its attribution
    if campaign_inquiry:
        if not campaign_inquiry.attribution_channel:
            campaign_inquiry.attribution_channel = "email"
        if not campaign_inquiry.source_channel:
            campaign_inquiry.source_channel = "email_reply"
    return interaction


def _build_email_reply_negotiation(interaction, sender_email: str, subject: str, intent: str, campaign_inquiry) -> dict[str, Any]:
    """构建与 to_negotiation_view 同结构的 negotiation 视图。"""
    now_iso = datetime.now(timezone.utc).isoformat()
    messages = [
        {
            "id": f"{interaction.id}-in",
            "sender": "customer",
            "content": interaction.content,
            "timestamp": interaction.created_at.isoformat() if interaction.created_at else now_iso,
        }
    ]
    return {
        "id": interaction.id,
        "session_id": interaction.id,
        "customerName": interaction.author_name,
        "customerEmail": sender_email,
        "product": _extract_product_from_subject(subject),
        "quantity": 1,
        "unit": "批",
        "destination": "",
        "status": "in_progress",
        "round": 1,
        "unread": 1,
        "lastMessage": interaction.content[:200],
        "updatedAt": now_iso,
        "messages": messages,
        "platform": "email",
        "interaction_type": "email_reply",
        "intent": intent,
        "backend_status": interaction.status,
        "draft_reply": None,
        "inquiry_id": interaction.inquiry_id,
        "source_channel": "email_reply",
        "matched_inquiry_id": str(campaign_inquiry.id) if campaign_inquiry else None,
    }


def create_negotiation_from_email_reply(
    db: Session,
    *,
    sender_email: str,
    subject: str,
    body: str,
    tenant_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    When an email reply is detected from a cold outreach campaign, automatically
    create a negotiation session in the Auto Negotiator.

    Bridges Connection ④ (email reply) with the existing SocialInteraction-based
    negotiation UI that powers AutoNegotiator.

    SECURITY: 事务保护 — 确保 SocialInteraction 创建和 Inquiry 更新原子性。

    Parameters
    ----------
    sender_email : str
        The email address of the reply sender.
    subject : str
        The email subject line.
    body : str
        The email body text.
    tenant_id : str, optional
        Scope to a specific tenant.

    Returns
    -------
    dict
        ``{"created": True, "negotiation": {...}}`` on success,
        ``{"created": False, "error": "..."}`` on failure.
    """
    from sqlalchemy.exc import SQLAlchemyError
    if not sender_email:
        return {"created": False, "error": "sender_email is required"}

    # Step 1: Classify intent
    intent = _classify_email_intent(subject, body)
    # Step 2: Try to match original outreach campaign
    campaign_inquiry = _find_campaign_inquiry(db, sender_email, subject, tenant_id)
    matched_tenant_id = tenant_id or (str(campaign_inquiry.tenant_id) if campaign_inquiry else None)
    # Step 3 & 4: Create a SocialInteraction record and update its attribution
    interaction = _create_email_reply_interaction(db, sender_email, body, intent, matched_tenant_id, campaign_inquiry)
    try:
        db.commit()
        db.refresh(interaction)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Failed to create negotiation from email reply (transaction rolled back): %s", exc)
        return {"created": False, "error": str(exc)}

    # Build the negotiation view (same shape as to_negotiation_view)
    negotiation = _build_email_reply_negotiation(interaction, sender_email, subject, intent, campaign_inquiry)
    logger.info(
        "Email reply negotiation created: interaction=%s sender=%s tenant=%s matched_inquiry=%s",
        interaction.id, sender_email, matched_tenant_id,
        campaign_inquiry.id if campaign_inquiry else None,
    )
    return {"created": True, "negotiation": negotiation}


# ═══════════════════════════════════════════════
# Connection ⑥: Full Funnel Attribution Report
# ═══════════════════════════════════════════════

CHANNELS = ("seo", "customer_finder", "email", "social", "ai_search", "referral", "direct")


def _compute_channel_conversion(db, all_inquiries) -> dict[str, dict[str, Any]]:
    """计算各渠道的询盘/报价/成交转化。"""
    from app.models.quote import Quote
    from app.models.order import Order
    channel_conversion: dict[str, dict[str, Any]] = {}
    for ch in CHANNELS:
        ch_inquiries = [i for i in all_inquiries if (i.attribution_channel or "direct") == ch]
        ch_total = len(ch_inquiries)
        if ch_total == 0:
            channel_conversion[ch] = {
                "inquiries": 0, "quoted": 0, "closed": 0,
                "quote_rate": 0.0, "close_rate": 0.0,
            }
            continue

        inquiry_ids = [str(i.id) for i in ch_inquiries]
        quoted_count = (
            db.query(func.count(func.distinct(Quote.inquiry_id)))
            .filter(Quote.inquiry_id.in_(inquiry_ids))
            .scalar() or 0
        )
        closed_count = (
            db.query(func.count(func.distinct(Order.id)))
            .join(Quote, Order.quote_id == Quote.id)
            .filter(Quote.inquiry_id.in_(inquiry_ids))
            .filter(Order.status.in_(["completed", "shipped"]))
            .scalar() or 0
        )
        channel_conversion[ch] = {
            "inquiries": ch_total,
            "quoted": quoted_count,
            "closed": closed_count,
            "quote_rate": round(quoted_count / ch_total * 100, 1),
            "close_rate": round(closed_count / ch_total * 100, 1),
        }
    return channel_conversion


def _compute_top_keywords(all_inquiries) -> list[dict[str, Any]]:
    """统计 Top 来源关键词。"""
    keyword_counts: dict[str, int] = {}
    for inq in all_inquiries:
        kw = (inq.source_keyword or "").strip()
        if kw:
            keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
    top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:20]
    return [{"keyword": k, "inquiries": c} for k, c in top_keywords]


def _compute_top_engines(all_inquiries) -> list[dict[str, Any]]:
    """统计 Top AI 搜索引擎来源。"""
    engine_counts: dict[str, int] = {}
    for inq in all_inquiries:
        eng = (inq.ai_search_engine or "").strip()
        if eng:
            engine_counts[eng] = engine_counts.get(eng, 0) + 1
    top_engines = sorted(engine_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    return [{"engine": e, "inquiries": c} for e, c in top_engines]


def _compute_channel_revenue(db, tenant_id, channels) -> dict[str, float]:
    """计算各渠道营收。"""
    from app.models.quote import Quote
    from app.models.order import Order
    channel_revenue: dict[str, float] = {ch: 0.0 for ch in channels}
    revenue_rows = (
        db.query(
            Inquiry.attribution_channel,
            func.sum(Order.total_amount).label("revenue"),
        )
        .join(Quote, Quote.inquiry_id == Inquiry.id)
        .join(Order, Order.quote_id == Quote.id)
        .filter(Order.status.in_(["completed", "shipped", "paid"]))
        .filter(Inquiry.is_active)
    )
    if tenant_id:
        revenue_rows = revenue_rows.filter(Inquiry.tenant_id == tenant_id)
    revenue_rows = revenue_rows.group_by(Inquiry.attribution_channel).all()
    for ch, rev in revenue_rows:
        key = ch or "direct"
        if key not in channel_revenue:
            key = "direct"
        channel_revenue[key] = float(rev or 0)
    return channel_revenue


def build_attribution_report(
    db: Session,
    *,
    tenant_id: Optional[str] = None,
    period: str = "30d",
) -> dict[str, Any]:
    """
    Build a full-funnel attribution report.

    Returns channel-level inquiry counts, conversion rates, top keywords,
    AI search engine sources, and revenue data.
    """
    days = 30
    if period.endswith("d"):
        try:
            days = int(period[:-1])
        except ValueError:
            days = 30

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    base = db.query(Inquiry).filter(Inquiry.is_active, Inquiry.created_at >= cutoff)
    if tenant_id:
        base = base.filter(Inquiry.tenant_id == tenant_id)

    all_inquiries = base.all()
    # --- Channel distribution ---
    channel_counts: dict[str, int] = {ch: 0 for ch in CHANNELS}
    for inq in all_inquiries:
        ch = inq.attribution_channel or "direct"
        if ch not in channel_counts:
            ch = "direct"
        channel_counts[ch] += 1

    total_inquiries = len(all_inquiries)
    channel_conversion = _compute_channel_conversion(db, all_inquiries)
    top_keywords_list = _compute_top_keywords(all_inquiries)
    top_engines_list = _compute_top_engines(all_inquiries)
    channel_revenue = _compute_channel_revenue(db, tenant_id, CHANNELS)
    # --- Overall conversion ---
    total_quoted = sum(v["quoted"] for v in channel_conversion.values())
    total_closed = sum(v["closed"] for v in channel_conversion.values())
    return {
        "period": period,
        "total_inquiries": total_inquiries,
        "total_quoted": total_quoted,
        "total_closed": total_closed,
        "overall_quote_rate": round(total_quoted / total_inquiries * 100, 1) if total_inquiries else 0.0,
        "overall_close_rate": round(total_closed / total_inquiries * 100, 1) if total_inquiries else 0.0,
        "channels": {
            ch: {
                "inquiries": channel_counts[ch],
                "conversion": channel_conversion[ch],
                "revenue": channel_revenue[ch],
            }
            for ch in CHANNELS
        },
        "top_keywords": top_keywords_list,
        "top_ai_engines": top_engines_list,
        "total_revenue": sum(channel_revenue.values()),
    }


def parse_and_bind_utm_to_inquiry(inquiry: Any, utm_data: dict[str, Any]) -> None:
    """提取 URL 中的 UTM 标记与来源参数，直接绑定至询盘实体。"""
    if not inquiry or not utm_data:
        return
    for field in ("utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"):
        val = utm_data.get(field)
        if val and hasattr(inquiry, field):
            setattr(inquiry, field, str(val)[:200])

    # 自动识别主要归因渠道
    src = str(utm_data.get("utm_source") or "").lower()
    med = str(utm_data.get("utm_medium") or "").lower()
    if hasattr(inquiry, "attribution_channel"):
        if "seo" in med or "google" in src or "baidu" in src:
            inquiry.attribution_channel = "seo"
        elif "email" in med or "newsletter" in src:
            inquiry.attribution_channel = "email"
        elif "social" in med or any(s in src for s in ("linkedin", "facebook", "twitter", "tiktok")):
            inquiry.attribution_channel = "social"
        elif "ai" in med or any(a in src for a in ("deepseek", "chatgpt", "perplexity", "gemini")):
            inquiry.attribution_channel = "ai_search"
        elif src:
            inquiry.attribution_channel = "referral"

