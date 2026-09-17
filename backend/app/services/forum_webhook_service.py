# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""论坛 Webhook — 新问题 → SEO 候选；含联系方式 → 询盘草稿；采纳答案 → Wiki 草稿。"""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import Session

from app.models.inquiry import Inquiry
from app.models.region import IndustryKeyword
from app.models.tenant import Tenant
from app.services.forum_sidecar_service import _safe_settings

_EMAIL = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_PHONE = re.compile(r"(?:\+?\d[\d\s\-()]{6,}\d|1[3-9]\d{9})")


def _extract_title(body: dict[str, Any]) -> str:
    """_extract_title。

    参数说明：
    :param body: 参数 body
    :return: 返回处理结果。
    """
    for key in ("title", "question_title", "subject", "name"):
        val = body.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()[:200]
    data = body.get("data")
    if isinstance(data, dict):
        for key in ("title", "question_title"):
            val = data.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()[:200]
    return ""


def _extract_body_text(body: dict[str, Any]) -> str:
    """_extract_body_text。

    参数说明：
    :param body: 参数 body
    :return: 返回处理结果。
    """
    for key in ("body", "content", "description", "question", "html"):
        val = body.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()[:2000]
    data = body.get("data")
    if isinstance(data, dict):
        for key in ("body", "content", "description"):
            val = data.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()[:2000]
    return ""


def _extract_answer_text(body: dict[str, Any]) -> str:
    """_extract_answer_text。

    参数说明：
    :param body: 参数 body
    :return: 返回处理结果。
    """
    for key in ("answer", "answer_body", "accepted_answer", "reply"):
        val = body.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()[:4000]
    data = body.get("data")
    if isinstance(data, dict):
        for key in ("answer", "answer_body", "content", "body"):
            val = data.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()[:4000]
    return ""


def _event_name(body: dict[str, Any]) -> str:
    """_event_name。

    参数说明：
    :param body: 参数 body
    :return: 返回处理结果。
    """
    return str(body.get("event") or body.get("type") or body.get("action") or "unknown").lower()


def _first_email(text: str) -> str | None:
    """_first_email。

    参数说明：
    :param text: 参数 text
    :return: 返回处理结果。
    """
    match = _EMAIL.search(text or "")
    return match.group(0) if match else None


def _first_phone(text: str) -> str | None:
    """_first_phone。

    参数说明：
    :param text: 参数 text
    :return: 返回处理结果。
    """
    match = _PHONE.search(text or "")
    if not match:
        return None
    raw = match.group(0).strip()
    digits = re.sub(r"\D", "", raw)
    if len(digits) >= 7:
        return raw[:50]
    return None


def _maybe_create_inquiry_from_forum(
    db: Session,
    *,
    tenant: Tenant | None,
    title: str,
    content: str,
) -> dict[str, Any] | None:
    """_maybe_create_inquiry_from_forum。

    参数说明：
    :param db: 参数 db
    :param tenant: 参数 tenant
    :param title: 参数 title
    :param content: 参数 content
    :return: 返回处理结果。
    """
    email = _first_email(content)
    phone = _first_phone(content)
    if not email and not phone:
        return None
    if not tenant:
        return {"skipped": True, "reason": "no_tenant_for_inquiry"}

    combined = f"{title}\n{content}".strip()
    existing = (
        db.query(Inquiry)
        .filter(
            Inquiry.tenant_id == str(tenant.id),
            Inquiry.source_channel == "forum_qa",
            Inquiry.message == combined[:2000],
        )
        .first()
    )
    if existing:
        return {"skipped": True, "reason": "duplicate", "inquiry_id": existing.id}

    email_val = email or ""
    name = email_val.split("@")[0][:100] if email_val else "Forum Buyer"
    inquiry = Inquiry(
        name=name or "Forum Buyer",
        phone=phone or "pending-contact",
        email=email,
        product=title[:100] if title else None,
        message=combined[:2000],
        status="pending",
        source_channel="forum_qa",
        tenant_id=str(tenant.id),
        last_click_label="forum_webhook_auto",
    )
    db.add(inquiry)
    db.flush()
    return {
        "created": True,
        "inquiry_id": inquiry.id,
        "human_review_required": True,
    }


def _maybe_create_wiki_draft(title: str, answer: str) -> dict[str, Any] | None:
    """_maybe_create_wiki_draft。

    参数说明：
    :param title: 参数 title
    :param answer: 参数 answer
    :return: 返回处理结果。
    """
    if len((answer or "").strip()) < 20:
        return None
    from app.api.v1.routes.building_wiki import create_forum_qa_draft
    article = create_forum_qa_draft(title or answer[:120], answer)
    if not article:
        return None
    if article.get("skipped"):
        return {"wiki_skipped": True, **article}
    return {
        "wiki_draft_created": True,
        "wiki_article_id": article.get("id"),
        "human_review_required": True,
    }


def ingest_forum_webhook(
    db: Session,
    *,
    tenant: Tenant | None,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """ingest_forum_webhook。

    参数说明：
    :param db: 参数 db
    :param tenant: 参数 tenant
    :param payload: 参数 payload
    :return: 返回处理结果。
    """
    event = _event_name(payload)
    title = _extract_title(payload)
    content = _extract_body_text(payload)
    answer = _extract_answer_text(payload)
    keyword_text = title or content[:120]
    if not keyword_text and not answer:
        return {"ok": False, "error": "缺少问题标题、正文或回答", "event": event}

    seo_imported = False
    seo_skipped = False
    question_events = ("question.created", "question.create", "post.created", "unknown")
    if event in question_events or (event == "answer.created" and title):
        text = (keyword_text or title).strip()
        if len(text) >= 4:
            existing = db.query(IndustryKeyword).filter(IndustryKeyword.keyword == text).first()
            if existing:
                seo_skipped = True
            else:
                db.add(
                    IndustryKeyword(
                        keyword=text[:200],
                        keyword_type="forum_qa",
                        category="论坛问答候选",
                        is_active=False,
                    )
                )
                seo_imported = True

    inquiry_result = None
    if event in question_events and (content or title):
        inquiry_result = _maybe_create_inquiry_from_forum(
            db, tenant=tenant, title=title, content=content or title
        )

    wiki_result = None
    accept_events = ("answer.accepted", "answer.accept", "question.accepted")
    if event in accept_events or (event == "answer.created" and payload.get("accepted")):
        wiki_result = _maybe_create_wiki_draft(title or keyword_text, answer or content)

    db.commit()
    inquiry_hint = bool(_EMAIL.search(content))
    tenant_label = tenant.name if tenant else "unknown"
    parts = ["已记入 SEO 候选（未激活）"]
    if inquiry_result and inquiry_result.get("created"):
        parts.append("已生成询盘草稿（待人工跟进）")
    elif inquiry_hint:
        parts.append("含邮箱/电话，请人工转询盘")
    if wiki_result and wiki_result.get("wiki_draft_created"):
        parts.append("已生成 Wiki 草稿（未发布）")

    return {
        "ok": True,
        "event": event,
        "tenant": tenant_label,
        "title": title[:200] if title else None,
        "seo_keyword_candidate": keyword_text[:200] if keyword_text else None,
        "seo_imported": seo_imported,
        "seo_skipped_duplicate": seo_skipped,
        "inquiry_hint": inquiry_hint,
        "inquiry": inquiry_result,
        "wiki": wiki_result,
        "human_review_required": True,
        "message": "；".join(parts) + "。",
    }


def resolve_tenant_for_webhook(db: Session, tenant_id: str | None, domain: str | None) -> Tenant | None:
    """resolve_tenant_for_webhook。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param domain: 参数 domain
    :return: 返回处理结果。
    """
    if tenant_id:
        row = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if row:
            return row
    if domain:
        row = db.query(Tenant).filter(Tenant.domain == domain.strip().lower()).first()
        if row:
            return row
    return None


def verify_webhook_secret(tenant: Tenant | None, header_secret: str | None) -> bool:
    """verify_webhook_secret。

    参数说明：
    :param tenant: 参数 tenant
    :param header_secret: 参数 header_secret
    :return: 返回处理结果。
    """
    from app.services.forum_sidecar_service import webhook_secret
    expected_global = webhook_secret()
    if expected_global and (header_secret or "").strip() == expected_global:
        return True
    if not tenant:
        return not expected_global
    settings = _safe_settings(tenant.settings)
    forum = settings.get("forum") if isinstance(settings.get("forum"), dict) else {}
    tenant_secret = str(forum.get("webhook_secret") or "").strip()
    if tenant_secret and (header_secret or "").strip() == tenant_secret:
        return True
    if not expected_global and not tenant_secret:
        return True
    return False
