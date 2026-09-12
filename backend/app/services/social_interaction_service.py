"""Lane I · 社媒评论/私信 → 意向识别 → 谈单草稿 → 可验证发送。"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.no_fake_delivery import NotConfiguredError, assert_not_fake_success
from app.models.social_interaction import SocialInteraction
from app.services.im_channel_webhook_service import ingest_channel_inquiry

# pending → draft_ready → approved → sent | failed | skipped
VALID_STATUSES = frozenset(
    {"pending", "draft_ready", "approved", "sending", "sent", "failed", "skipped"}
)
STATUS_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"draft_ready", "skipped", "failed"},
    "draft_ready": {"approved", "skipped", "failed"},
    "approved": {"sending", "sent", "failed"},
    "sending": {"sent", "failed"},
    "sent": set(),
    "failed": {"draft_ready", "approved"},
    "skipped": set(),
}

_INQUIRY_KEYWORDS = ("多少钱", "报价", "价格", "怎么买", "联系方式", "电话", "微信", "合作", "采购", "询价", "厂家")
_PRICE_KEYWORDS = ("便宜", "优惠", "折扣", "能不能少", "太贵")
_SPAM_KEYWORDS = ("刷单", "代刷", "博彩", "赌博")


def _now_iso() -> str:
    """_now_iso。
    :return: 返回处理结果。
    """
    return datetime.now(timezone.utc).isoformat()


def classify_intent(content: str) -> str:
    """classify_intent。

    参数说明：
    :param content: 参数 content
    :return: 返回处理结果。
    """
    text = (content or "").strip()
    if not text:
        return "general"
    lower = text.lower()
    for kw in _SPAM_KEYWORDS:
        if kw in text:
            return "spam"
    for kw in _INQUIRY_KEYWORDS:
        if kw in text:
            return "inquiry"
    for kw in _PRICE_KEYWORDS:
        if kw in text:
            return "price"
    if re.search(r"\d{7,}", text):
        return "inquiry"
    return "general"


def _extract_phone(content: str) -> Optional[str]:
    """_extract_phone。

    参数说明：
    :param content: 参数 content
    :return: 返回处理结果。
    """
    m = re.search(r"1[3-9]\d{9}", content or "")
    return m.group(0) if m else None


def _extract_product_hint(content: str) -> str:
    """_extract_product_hint。

    参数说明：
    :param content: 参数 content
    :return: 返回处理结果。
    """
    for token in ("岩棉", "混凝土", "砂浆", "保温", "砌块", "板材", "涂料"):
        if token in (content or ""):
            return token
    return "建材产品"


def generate_draft_reply(*, content: str, intent: str, author_name: str) -> str:
    """生成谈单草稿（须人工审批后发送，禁止自动冒充已回复）。"""
    product = _extract_product_hint(content)
    name = (author_name or "客户").strip() or "客户"
    if intent == "spam":
        return ""
    if intent == "price":
        return (
            f"{name}您好，感谢关注。关于{product}的价格，需先确认规格、数量与交货地，"
            "我们才能给出准确报价区间。方便私信留下具体需求吗？"
        )
    if intent == "inquiry":
        return (
            f"{name}您好，已收到您对{product}的咨询。请补充：规格型号、预计数量、"
            "项目城市或目的港，我们 2 小时内安排专员对接报价与样品方案。"
        )
    return (
        f"{name}您好，感谢留言。如需{product}报价或技术参数，请说明使用场景与数量，"
        "我们会尽快回复您。"
    )


def _transition(row: SocialInteraction, new_status: str) -> None:
    """_transition。

    参数说明：
    :param row: 参数 row
    :param new_status: 参数 new_status
    :return: 返回处理结果。
    """
    if new_status not in VALID_STATUSES:
        raise ValueError(f"invalid_status:{new_status}")
    allowed = STATUS_TRANSITIONS.get(row.status or "pending", set())
    if new_status not in allowed and new_status != row.status:
        raise ValueError(f"invalid_transition:{row.status}->{new_status}")
    row.status = new_status


def ingest_douyin_interaction(
    db: Session,
    *,
    tenant_id: str,
    platform_post_id: str,
    platform_comment_id: str,
    content: str,
    author_name: str = "抖音用户",
    author_platform_id: Optional[str] = None,
    interaction_type: str = "comment",
    phone: Optional[str] = None,
) -> dict[str, Any]:
    """Webhook 入库：幂等按 platform+comment_id。"""
    comment_id = (platform_comment_id or "").strip()
    if not comment_id:
        raise ValueError("platform_comment_id_required")

    existing = (
        db.query(SocialInteraction)
        .filter(
            SocialInteraction.platform == "douyin",
            SocialInteraction.platform_comment_id == comment_id,
        )
        .first()
    )
    if existing:
        return serialize_interaction(existing)

    intent = classify_intent(content)
    row = SocialInteraction(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        platform="douyin",
        interaction_type=interaction_type or "comment",
        platform_post_id=platform_post_id,
        platform_comment_id=comment_id,
        author_name=author_name[:120] or "抖音用户",
        author_platform_id=author_platform_id,
        content=content,
        intent=intent,
        status="pending",
    )
    db.add(row)
    db.flush()
    if intent == "spam":
        _transition(row, "skipped")
        row.draft_reply = None
    else:
        draft = generate_draft_reply(content=content, intent=intent, author_name=author_name)
        row.draft_reply = draft or None
        _transition(row, "draft_ready")

    inquiry_id = None
    detected_phone = phone or _extract_phone(content)
    if intent == "inquiry" and detected_phone:
        lead = ingest_channel_inquiry(
            db,
            channel="douyin_comment",
            name=author_name[:120] or "抖音访客",
            phone=detected_phone,
            message=content,
            merchant_id=tenant_id,
            extra={
                "platform_post_id": platform_post_id,
                "platform_comment_id": comment_id,
                "interaction_id": row.id,
            },
        )
        inquiry_id = lead.get("id")
        row.inquiry_id = inquiry_id

    db.commit()
    db.refresh(row)
    try:
        from app.services.onboarding_progress_service import mark_sales_channel_flag
        mark_sales_channel_flag(db, tenant_id, "douyin_worker_configured")
        db.commit()
    except Exception:
        db.rollback()

    if row.status != "skipped":
        try:
            from app.services.sales_push_service import notify_social_interaction
            notify_social_interaction(db, row)
        except Exception:
            pass

    return serialize_interaction(row)


def list_interactions(
    db: Session,
    *,
    tenant_id: Optional[str] = None,
    platform: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
) -> list[dict[str, Any]]:
    """list_interactions。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param platform: 参数 platform
    :param status: 参数 status
    :param limit: 参数 limit
    :param skip: 参数 skip
    :return: 返回处理结果。
    """
    q = db.query(SocialInteraction).order_by(SocialInteraction.updated_at.desc())
    if tenant_id:
        q = q.filter(SocialInteraction.tenant_id == tenant_id)
    if platform:
        q = q.filter(SocialInteraction.platform == platform)
    if status:
        q = q.filter(SocialInteraction.status == status)
    rows = q.offset(skip).limit(limit).all()
    return [serialize_interaction(r) for r in rows]


def get_summary(db: Session, *, tenant_id: Optional[str] = None) -> dict[str, Any]:
    """get_summary。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    q = db.query(SocialInteraction)
    if tenant_id:
        q = q.filter(SocialInteraction.tenant_id == tenant_id)

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    active = q.filter(SocialInteraction.status.in_(("draft_ready", "approved", "sending"))).count()
    pending_approval = q.filter(SocialInteraction.status == "draft_ready").count()
    today = q.filter(SocialInteraction.created_at >= today_start).count()
    monthly_deals = q.filter(
        SocialInteraction.status == "sent",
        SocialInteraction.updated_at >= month_start,
    ).count()
    return {
        "active_negotiations": active,
        "today_inquiries": today,
        "pending_approval": pending_approval,
        "monthly_deals": monthly_deals,
    }


def approve_draft(db: Session, interaction_id: str, *, final_reply: Optional[str] = None) -> dict[str, Any]:
    """approve_draft。

    参数说明：
    :param db: 参数 db
    :param interaction_id: 参数 interaction_id
    :param final_reply: 参数 final_reply
    :return: 返回处理结果。
    """
    row = db.query(SocialInteraction).filter(SocialInteraction.id == interaction_id).first()
    if not row:
        raise KeyError("interaction_not_found")
    if row.status not in ("draft_ready", "failed"):
        raise ValueError(f"cannot_approve_from_{row.status}")
    text = (final_reply or row.draft_reply or "").strip()
    if not text:
        raise ValueError("draft_reply_empty")
    row.final_reply = text
    _transition(row, "approved")
    db.commit()
    db.refresh(row)
    return serialize_interaction(row)


def mark_sent(
    db: Session,
    interaction_id: str,
    *,
    platform_receipt_id: str,
    platform_message_id: Optional[str] = None,
    extra: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """标记已发送 — 必须带平台回执，禁止假成功。"""
    row = db.query(SocialInteraction).filter(SocialInteraction.id == interaction_id).first()
    if not row:
        raise KeyError("interaction_not_found")
    if row.status not in ("approved", "sending"):
        raise ValueError(f"cannot_mark_sent_from_{row.status}")

    receipt_id = (platform_receipt_id or "").strip()
    assert_not_fake_success(
        ok=True,
        evidence=receipt_id,
        code="SOCIAL_REPLY_NO_RECEIPT",
        message="未提供平台发送回执，禁止标记为已发送",
    )
    receipt = {
        "platform_receipt_id": receipt_id,
        "platform_message_id": platform_message_id,
        "recorded_at": _now_iso(),
    }
    if extra:
        receipt.update(extra)

    row.platform_send_receipt = receipt
    _transition(row, "sent")
    db.commit()
    db.refresh(row)
    return serialize_interaction(row)


def mark_failed(
    db: Session,
    interaction_id: str,
    *,
    error_code: str,
    error_message: str,
) -> dict[str, Any]:
    """mark_failed。

    参数说明：
    :param db: 参数 db
    :param interaction_id: 参数 interaction_id
    :param error_code: 参数 error_code
    :param error_message: 参数 error_message
    :return: 返回处理结果。
    """
    row = db.query(SocialInteraction).filter(SocialInteraction.id == interaction_id).first()
    if not row:
        raise KeyError("interaction_not_found")
    row.error_code = error_code[:64]
    row.error_message = error_message[:500]
    _transition(row, "failed")
    db.commit()
    db.refresh(row)
    return serialize_interaction(row)


def regenerate_draft(db: Session, interaction_id: str) -> dict[str, Any]:
    """regenerate_draft。

    参数说明：
    :param db: 参数 db
    :param interaction_id: 参数 interaction_id
    :return: 返回处理结果。
    """
    row = db.query(SocialInteraction).filter(SocialInteraction.id == interaction_id).first()
    if not row:
        raise KeyError("interaction_not_found")
    if row.status in ("sent", "skipped"):
        raise ValueError(f"cannot_regenerate_from_{row.status}")
    draft = generate_draft_reply(content=row.content, intent=row.intent, author_name=row.author_name)
    row.draft_reply = draft
    if row.status == "pending":
        _transition(row, "draft_ready")
    db.commit()
    db.refresh(row)
    return serialize_interaction(row)


def _map_ui_status(status: str) -> str:
    """_map_ui_status。

    参数说明：
    :param status: 参数 status
    :return: 返回处理结果。
    """
    return {
        "pending": "pending",
        "draft_ready": "pending",
        "approved": "in_progress",
        "sending": "in_progress",
        "sent": "completed",
        "failed": "failed",
        "skipped": "completed",
    }.get(status, "pending")


def to_negotiation_view(row: SocialInteraction) -> dict[str, Any]:
    """兼容 AutoNegotiator 前端结构。"""
    messages = [
        {
            "id": f"{row.id}-in",
            "sender": "customer",
            "content": row.content,
            "timestamp": row.created_at.isoformat() if row.created_at else _now_iso(),
        }
    ]
    reply = row.final_reply or row.draft_reply
    if reply:
        messages.append(
            {
                "id": f"{row.id}-draft",
                "sender": "ai",
                "content": reply,
                "timestamp": row.updated_at.isoformat() if row.updated_at else _now_iso(),
            }
        )
    return {
        "id": row.id,
        "session_id": row.id,
        "customerName": row.author_name,
        "customerEmail": "",
        "product": _extract_product_hint(row.content),
        "quantity": 1,
        "unit": "批",
        "destination": "国内",
        "status": _map_ui_status(row.status),
        "round": 1,
        "unread": 1 if row.status in ("draft_ready", "pending") else 0,
        "lastMessage": row.content[:200],
        "updatedAt": row.updated_at.isoformat() if row.updated_at else _now_iso(),
        "messages": messages,
        "platform": row.platform,
        "interaction_type": row.interaction_type,
        "intent": row.intent,
        "backend_status": row.status,
        "draft_reply": row.draft_reply,
        "inquiry_id": row.inquiry_id,
    }


def list_negotiations_view(
    db: Session,
    *,
    tenant_id: Optional[str] = None,
    ui_status: Optional[str] = None,
    limit: int = 50,
) -> dict[str, Any]:
    """list_negotiations_view。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param ui_status: 参数 ui_status
    :param limit: 参数 limit
    :return: 返回处理结果。
    """
    rows = (
        db.query(SocialInteraction)
        .filter(SocialInteraction.status != "skipped")
        .order_by(SocialInteraction.updated_at.desc())
    )
    if tenant_id:
        rows = rows.filter(SocialInteraction.tenant_id == tenant_id)
    items = rows.limit(limit).all()
    negotiations = [to_negotiation_view(r) for r in items]
    if ui_status:
        negotiations = [n for n in negotiations if n["status"] == ui_status]
    return {"negotiations": negotiations, "total": len(negotiations), "limit": limit}


def serialize_interaction(row: SocialInteraction) -> dict[str, Any]:
    """serialize_interaction。

    参数说明：
    :param row: 参数 row
    :return: 返回处理结果。
    """
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "platform": row.platform,
        "interaction_type": row.interaction_type,
        "platform_post_id": row.platform_post_id,
        "platform_comment_id": row.platform_comment_id,
        "author_name": row.author_name,
        "author_platform_id": row.author_platform_id,
        "content": row.content,
        "intent": row.intent,
        "status": row.status,
        "draft_reply": row.draft_reply,
        "final_reply": row.final_reply,
        "platform_send_receipt": row.platform_send_receipt,
        "inquiry_id": row.inquiry_id,
        "error_code": row.error_code,
        "error_message": row.error_message,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }
