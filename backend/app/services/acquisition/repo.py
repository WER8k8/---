# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""获客落库仓储 — 复用既有 Inquiry / ProspectLead，诚实降级。

红线：不新建平行业务账本；DB 不可用时明确 persisted=false，不假装成功。
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _safe_str(v: Any, default: str = "") -> str:
    if v is None:
        return default
    return str(v).strip() or default


def persist_inquiry(
    db: Any,
    *,
    tenant_id: str,
    inquiry_id: str,
    message: str,
    email: str = "",
    contact_name: str = "",
    company_name: str = "",
    product: str = "",
    country: str = "",
    channel: str = "inbound",
    assigned_to: str = "",
    attribution_channel: str = "acquisition_ops",
) -> dict[str, Any]:
    """尽力写入 inquiries 表。返回 {persisted, id, reason}。"""
    if db is None:
        return {"persisted": False, "id": None, "reason": "db_unavailable"}
    try:
        from app.models.inquiry import Inquiry
        row = Inquiry(
            name=_safe_str(contact_name, _safe_str(company_name, "unknown")),
            phone=_safe_str(inquiry_id, "n/a")[:50],
            email=_safe_str(email) or None,
            product=_safe_str(product) or None,
            message=_safe_str(message, "(acquisition reply)")[:4000],
            status="pending",
            source_channel=_safe_str(channel, "inbound")[:50],
            tenant_id=_safe_str(tenant_id) or None,
            assigned_to=_safe_str(assigned_to) or None,
            attribution_channel=_safe_str(attribution_channel)[:50],
            attribution_data=(f'{{"ops_inquiry_id":"{_safe_str(inquiry_id)}","country":"{_safe_str(country)}"}}'
                              if inquiry_id or country else None),
        )
        db.add(row)
        db.commit()
        rid = getattr(row, "id", None) or inquiry_id
        return {"persisted": True, "id": str(rid), "reason": "", "table": "inquiries"}
    except Exception as exc:  # noqa: BLE001
        logger.warning("persist_inquiry 失败: %s", exc)
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass
        return {"persisted": False, "id": None, "reason": str(exc)[:200]}


def persist_prospect_lead(
    db: Any,
    *,
    tenant_id: str = "",
    email: str = "",
    company_name: str = "",
    country: str = "",
    contact_name: str = "",
    contact_title: str = "",
    buyer_type: str = "",
    channel: str = "manual_import",
    inquiry_ref: str = "",
) -> dict[str, Any]:
    """尽力写入 prospect_leads。返回 {persisted, id, reason}。"""
    if db is None:
        return {"persisted": False, "id": None, "reason": "db_unavailable"}
    if not email and not company_name and not contact_name:
        return {"persisted": False, "id": None, "reason": "no_identity_fields"}
    try:
        from app.models.prospect_lead import LeadSource, LeadStatus, ProspectLead

        src_name = (_safe_str(channel) or "manual_import").lower()
        source_map = {
            "inbound": LeadSource.MANUAL_IMPORT,
            "manual": LeadSource.MANUAL_IMPORT,
            "manual_import": LeadSource.MANUAL_IMPORT,
            "email": LeadSource.HUNTER_IO,
            "linkedin": LeadSource.LINKEDIN,
            "whatsapp": LeadSource.WHATSAPP,
            "google": LeadSource.GOOGLE_CSE,
            "website": LeadSource.WEBSITE_SCRAPE,
            "referral": LeadSource.REFERRAL,
            "reply_ingest": LeadSource.MANUAL_IMPORT,
        }
        source = source_map.get(src_name, LeadSource.MANUAL_IMPORT)
        first = contact_name
        last = ""
        if contact_name and " " in contact_name:
            parts = contact_name.split(None, 1)
            first, last = parts[0], parts[1]
        lead = ProspectLead(
            email=_safe_str(email) or None,
            company_name=_safe_str(company_name) or None,
            country=_safe_str(country)[:8] or None,
            first_name=_safe_str(first) or None,
            last_name=_safe_str(last) or None,
            title=_safe_str(contact_title) or None,
            notes=(f"ops_inquiry={_safe_str(inquiry_ref)}; buyer_type={_safe_str(buyer_type)}"
                   if inquiry_ref or buyer_type else None),
        )
        # multi-tenant 归属：有 tenant_id 则写入，避免线索串租户
        if _safe_str(tenant_id) and hasattr(lead, "tenant_id"):
            lead.tenant_id = _safe_str(tenant_id)
        # source 枚举字段若存在则赋值
        if hasattr(lead, "source"):
            try:
                lead.source = source
            except Exception:  # noqa: BLE001
                if hasattr(lead, "source"):
                    lead.source = getattr(source, "value", src_name)
        if hasattr(lead, "status"):
            lead.status = LeadStatus.DISCOVERED
        db.add(lead)
        db.commit()
        rid = getattr(lead, "id", None)
        return {"persisted": True, "id": str(rid) if rid else None, "reason": "", "table": "prospect_leads"}
    except Exception as exc:  # noqa: BLE001
        logger.warning("persist_prospect_lead 失败: %s", exc)
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass
        return {"persisted": False, "id": None, "reason": str(exc)[:200]}
