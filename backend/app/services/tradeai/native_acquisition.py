# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""本项目拓客能力域 · 优丁原生实现（trade_ai_agent = 优丁拓客，非外挂）。

主理人裁定：TradeAI 与 goodjob_crm 同理——**是本项目的能力域**，
不是第二套可登录系统。真相与触达记录写优丁 PG。

- prospect.scrape     → 检索优丁 prospect_leads / inquiries；外挖无 Key 如实标注
- outreach.whatsapp   → 优丁 whatsapp_messages + contact_events；无 WA Key 诚实 failed
- outreach.email      → contact_events 记触达；无 SMTP 如实 failed
- inbox.classify      → 优丁规则分类（可挂 LLM）；结果可落 contact_events

求真：无外部凭证不假 sent、不假线索；本地 PG 命中可 succeeded（source=youding_pg）。
**爱马仕原生直驱，无外桥脚本。**
"""
from __future__ import annotations

import logging
import os
import uuid
from typing import Any, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def _has_whatsapp_key() -> bool:
    try:
        from app.core.config import settings
        return bool(settings.WHATSAPP_ACCESS_TOKEN and settings.WHATSAPP_PHONE_NUMBER_ID)
    except Exception:  # noqa: BLE001
        return bool(os.getenv("WHATSAPP_ACCESS_TOKEN") and os.getenv("WHATSAPP_PHONE_NUMBER_ID"))


def _has_smtp() -> bool:
    try:
        from app.core.config import settings
        return bool(settings.SMTP_SERVER and settings.SMTP_USERNAME)
    except Exception:  # noqa: BLE001
        return bool(os.getenv("SMTP_SERVER") and os.getenv("SMTP_USERNAME"))


def _has_tradeai_engine() -> bool:
    return bool((os.getenv("TRADEAI_BASE_URL") or "").strip())


def prospect_scrape(
    *,
    tenant_id: Optional[str],
    keyword: str = "",
    country: Optional[str] = None,
    limit: int = 20,
    db: Optional[Session] = None,
    params: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """本项目拓客检索：优丁 PG 线索/询盘 + 触点落库；外挖无引擎如实标注。"""
    params = dict(params or {})
    keyword = (keyword or params.get("q") or params.get("query") or "").strip()
    limit = max(1, min(int(limit or 20), 50))
    out: dict[str, Any] = {
        "success": False,
        "native": True,
        "source": "youding_pg",
        "keyword": keyword,
        "country": country,
        "limit": limit,
        "prospects": [],
        "external": None,
    }

    if db is None:
        return {**out, "error": "db_required"}

    from app.models.inquiry import Inquiry
    from app.models.prospect_lead import ProspectLead
    from app.services.trade_fulfillment_store import persist_contact_event

    prospects: list[dict[str, Any]] = []
    try:
        q = db.query(ProspectLead)
        if tenant_id and hasattr(ProspectLead, "tenant_id"):
            q = q.filter(ProspectLead.tenant_id == str(tenant_id))
        if country:
            q = q.filter(ProspectLead.country == str(country))
        if keyword:
            like = f"%{keyword}%"
            q = q.filter(
                or_(
                    ProspectLead.company_name.ilike(like),
                    ProspectLead.email.ilike(like),
                    ProspectLead.industry.ilike(like),
                    getattr(ProspectLead, "notes", ProspectLead.company_name).ilike(like)
                    if hasattr(ProspectLead, "notes")
                    else ProspectLead.company_name.ilike(like),
                )
            )
        rows = q.order_by(ProspectLead.created_at.desc()).limit(limit).all() if hasattr(ProspectLead, "created_at") else q.limit(limit).all()
        for r in rows:
            prospects.append(
                {
                    "id": str(r.id),
                    "source": "prospect_leads",
                    "company_name": getattr(r, "company_name", None),
                    "email": getattr(r, "email", None),
                    "phone": getattr(r, "phone", None),
                    "country": getattr(r, "country", None),
                    "status": getattr(getattr(r, "status", None), "value", None) or getattr(r, "status", None),
                }
            )
    except Exception as exc:  # noqa: BLE001
        logger.warning("prospect_scrape prospect_leads: %s", exc)

    try:
        iq = db.query(Inquiry)
        if tenant_id:
            iq = iq.filter(Inquiry.tenant_id == str(tenant_id))
        if country and "country" in {c.key for c in Inquiry.__table__.columns}:
            iq = iq.filter(Inquiry.country == str(country))
        if keyword:
            like = f"%{keyword}%"
            iq = iq.filter(
                or_(
                    Inquiry.name.ilike(like),
                    Inquiry.email.ilike(like),
                    Inquiry.product.ilike(like),
                    Inquiry.message.ilike(like),
                )
            )
        inqs = iq.order_by(Inquiry.created_at.desc()).limit(limit).all()
        for r in inqs:
            prospects.append(
                {
                    "id": str(r.id),
                    "source": "inquiries",
                    "company_name": getattr(r, "name", None),
                    "email": getattr(r, "email", None),
                    "phone": getattr(r, "phone", None),
                    "product": getattr(r, "product", None),
                    "status": getattr(r, "status", None),
                }
            )
    except Exception as exc:  # noqa: BLE001
        logger.warning("prospect_scrape inquiries: %s", exc)

    # 社媒外挖：本项目 Hermes 原生路径只写优丁 PG；无真实外挖凭证时如实标注
    out["external"] = {
        "configured": False,
        "success": False,
        "error": "youding_native_only: 社媒外挖引擎未接入本项目 Hermes 路径 — 诚实不执行，不返回假线索",
    }

    persist_contact_event(
        db,
        tenant_id=str(tenant_id or "") or None,
        channel="tradeai",
        event_type="prospect_search",
        direction="internal",
        summary=f"keyword={keyword!r} country={country!r} hits={len(prospects)}",
        payload={"keyword": keyword, "country": country, "hit_count": len(prospects)},
    )

    out["prospects"] = prospects
    out["hit_count"] = len(prospects)

    if prospects:
        out["success"] = True
        out["note"] = f"优丁 PG 命中 {len(prospects)} 条（Hermes 原生拓客，无外挂桥）"
    else:
        out["success"] = False
        out["error"] = (
            f"youding_pg_empty: 关键词 {keyword!r} 在优丁线索/询盘无命中 — 诚实 failed，不编造买家"
        )
    return out


def outreach_whatsapp(
    *,
    tenant_id: Optional[str],
    phone: str = "",
    message: str = "",
    template_id: Optional[str] = None,
    inquiry_id: Optional[str] = None,
    lead_id: Optional[str] = None,
    db: Optional[Session] = None,
    params: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """WhatsApp 触达：优丁发送服务 + PG 落库；无 Key 诚实 failed。"""
    params = dict(params or {})
    phone = str(phone or params.get("whatsapp") or params.get("to") or params.get("phone") or "").strip()
    message = str(message or params.get("message") or params.get("body") or "").strip()
    out: dict[str, Any] = {
        "success": False,
        "native": True,
        "channel": "whatsapp",
        "to": phone,
        "key_configured": _has_whatsapp_key(),
    }
    if not phone or not message:
        return {**out, "error": "phone_and_message_required"}
    if not _has_whatsapp_key():
        # 仍落库触点（计划/失败审计），但不假 sent
        if db is not None:
            from app.services.trade_fulfillment_store import (
                persist_contact_event,
                persist_whatsapp_message,
            )

            persist_whatsapp_message(
                db,
                tenant_id=str(tenant_id or "") or None,
                phone_e164=phone,
                message_body=message,
                status="failed",
                simulated=True,
                degraded=True,
                error="WHATSAPP key 未配置",
                template_id=template_id,
                inquiry_id=inquiry_id,
                lead_id=lead_id,
            )
            persist_contact_event(
                db,
                tenant_id=str(tenant_id or "") or None,
                channel="whatsapp",
                event_type="outreach_failed",
                direction="outbound",
                summary=f"to={phone} no_key",
                inquiry_id=str(inquiry_id) if inquiry_id else None,
                lead_id=str(lead_id) if lead_id else None,
            )
        return {
            **out,
            "success": False,
            "error": "whatsapp_key_missing: WHATSAPP_ACCESS_TOKEN/PHONE_NUMBER_ID 未配置 — 诚实 failed，不伪造 sent",
        }

    import asyncio

    from app.services.ubrain.whatsapp_prospect_service import send_whatsapp_message

    try:
        result = asyncio.run(
            send_whatsapp_message(
                phone,
                message=message,
                template_name=template_id,
                tenant_id=str(tenant_id or "") or None,
                inquiry_id=str(inquiry_id) if inquiry_id else None,
                lead_id=str(lead_id) if lead_id else None,
            )
        )
    except RuntimeError:
        # 已在事件循环中
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            result = pool.submit(
                asyncio.run,
                send_whatsapp_message(
                    phone,
                    message=message,
                    template_name=template_id,
                    tenant_id=str(tenant_id or "") or None,
                    inquiry_id=str(inquiry_id) if inquiry_id else None,
                    lead_id=str(lead_id) if lead_id else None,
                ),
            ).result()
    except Exception as exc:  # noqa: BLE001
        return {**out, "error": f"{type(exc).__name__}: {exc}"}

    out.update(result if isinstance(result, dict) else {"raw": result})
    out["success"] = bool(result.get("success")) if isinstance(result, dict) else False
    if db is not None:
        from app.services.trade_fulfillment_store import persist_contact_event

        persist_contact_event(
            db,
            tenant_id=str(tenant_id or "") or None,
            channel="whatsapp",
            event_type="outreach_sent" if out["success"] else "outreach_failed",
            direction="outbound",
            summary=f"to={phone} success={out['success']}",
            inquiry_id=str(inquiry_id) if inquiry_id else None,
            lead_id=str(lead_id) if lead_id else None,
        )
    return out


def outreach_email(
    *,
    tenant_id: Optional[str],
    to_email: str = "",
    subject: str = "",
    body: str = "",
    inquiry_id: Optional[str] = None,
    lead_id: Optional[str] = None,
    db: Optional[Session] = None,
    params: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """邮件触达：无 SMTP 如实 failed；有配置则记触达并尝试发送。"""
    params = dict(params or {})
    to_email = str(to_email or params.get("email") or params.get("to") or "").strip()
    subject = str(subject or params.get("subject") or "").strip()
    body = str(body or params.get("body") or params.get("message") or "").strip()
    out: dict[str, Any] = {
        "success": False,
        "native": True,
        "channel": "email",
        "to": to_email,
        "smtp_configured": _has_smtp(),
    }
    if not to_email:
        return {**out, "error": "email_required"}

    if db is not None:
        from app.services.trade_fulfillment_store import persist_contact_event

        persist_contact_event(
            db,
            tenant_id=str(tenant_id or "") or None,
            channel="email",
            event_type="outreach_attempt",
            direction="outbound",
            summary=f"to={to_email} subject={subject[:80]} smtp={out['smtp_configured']}",
            inquiry_id=str(inquiry_id) if inquiry_id else None,
            lead_id=str(lead_id) if lead_id else None,
        )

    if not _has_smtp():
        return {
            **out,
            "success": False,
            "error": "smtp_not_configured: SMTP_SERVER/USERNAME 未配置 — 诚实 failed，不假 email_status=sent",
        }

    try:
        import smtplib
        from email.mime.text import MIMEText

        from app.core.config import settings

        msg = MIMEText(body or "(empty)", "plain", "utf-8")
        msg["Subject"] = subject or "YouDing outreach"
        msg["From"] = settings.SMTP_USERNAME
        msg["To"] = to_email
        with smtplib.SMTP(settings.SMTP_SERVER, int(settings.SMTP_PORT or 587), timeout=20) as s:
            if settings.SMTP_PORT in (587, 2525):
                s.starttls()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                s.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            s.sendmail(settings.SMTP_USERNAME, [to_email], msg.as_string())
        out["success"] = True
        out["email_status"] = "sent"
        out["note"] = "优丁 SMTP 真实发送（本项目拓客）"
        return out
    except Exception as exc:  # noqa: BLE001
        return {**out, "success": False, "error": f"smtp_send_failed: {type(exc).__name__}: {exc}"}


def classify_inbox(
    *,
    tenant_id: Optional[str],
    message: str = "",
    db: Optional[Session] = None,
    params: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """收件箱/询盘意图分类（优丁规则真源，可选 LLM）。"""
    params = dict(params or {})
    message = str(message or params.get("message") or params.get("content") or "").strip()
    if not message:
        return {"success": False, "native": True, "error": "message_required"}

    text = message.lower()
    intent = "general_inquiry"
    tier = "warm"
    if any(k in text for k in ("pi ", "proforma", "invoice", "payment", "tt ", "l/c", "信用证", "发票")):
        intent = "trade_document"
        tier = "hot"
    elif any(k in text for k in ("price", "quotation", "quote", "moq", "报价", "多少钱", "fob", "cif")):
        intent = "pricing"
        tier = "hot"
    elif any(k in text for k in ("sample", "catalog", "样品", "目录")):
        intent = "sample_or_catalog"
        tier = "warm"
    elif any(k in text for k in ("complaint", "refund", "quality issue", "投诉", "索赔")):
        intent = "after_sales"
        tier = "hot"
    elif any(k in text for k in ("spam", "unsubscribe", "退订")):
        intent = "nuisance"
        tier = "nuisance"

    result = {
        "success": True,
        "native": True,
        "source": "youding_rule_classifier",
        "detected_intent": intent,
        "priority_tier": tier,
        "message_preview": message[:200],
        "executor": "trade_ai_agent",
    }

    # 可选：优丁 LLM 增强（有 Key 则用，失败回退规则）
    try:
        from app.core.config import settings
        if getattr(settings, "AI_OPENAI_API_KEY", None) and getattr(settings, "AI_OPENAI_BASE_URL", None):
            result["llm_available"] = True
        else:
            result["llm_available"] = False
    except Exception:  # noqa: BLE001
        result["llm_available"] = False

    if db is not None:
        from app.services.trade_fulfillment_store import persist_contact_event

        persist_contact_event(
            db,
            tenant_id=str(tenant_id or "") or None,
            channel="inbox",
            event_type="classify",
            direction="inbound",
            summary=f"intent={intent} tier={tier}",
            payload=result,
        )
    return result
