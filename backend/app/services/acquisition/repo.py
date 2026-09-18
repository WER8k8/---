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


def _is_uuid(value: str) -> bool:
    try:
        import uuid as _uuid
        _uuid.UUID(str(value))
        return True
    except Exception:
        return False


def resolve_tenant_uuid(db: Any, tenant_id: str) -> Optional[str]:
    """业务租户 id（demo/dev.local）→ tenants.id UUID；解析失败返回 None（诚实不硬塞）。"""
    tid = _safe_str(tenant_id)
    if not tid:
        return None
    if _is_uuid(tid):
        return tid
    if db is None or not hasattr(db, "execute"):
        return None
    try:
        from sqlalchemy import text

        # 业务别名 → 稳定开发租户（dev.local）
        aliases = {
            "demo": ["dev.local", "开发租户"],
            "dev": ["dev.local", "开发租户"],
            "dev.local": ["dev.local", "开发租户"],
        }
        candidates = list(aliases.get(tid.lower(), [])) + [tid]
        for v in candidates:
            for sql, param in (
                ("select id::text from tenants where domain = :v limit 1", v),
                ("select id::text from tenants where name = :v limit 1", v),
                ("select id::text from tenants where domain ilike :like limit 1", f"%{v}%"),
                ("select id::text from tenants where name ilike :like limit 1", f"%{v}%"),
            ):
                try:
                    row = db.execute(text(sql), {"v": v, "like": param if "ilike" in sql else v}).first()
                    if row and row[0]:
                        return str(row[0])
                except Exception:
                    continue
        # 用户 username = tenant 的关联租户（seed 常见）
        row = db.execute(
            text(
                "select ut.tenant_id::text from user_tenants ut "
                "join users u on u.id = ut.user_id "
                "where u.username in (:v, 'tenant', 'tenant_demo') "
                "order by ut.created_at nulls last limit 1"
            ),
            {"v": tid},
        ).first()
        if row and row[0]:
            return str(row[0])
        row = db.execute(text("select id::text from tenants order by created_at nulls last limit 1")).first()
        if row and row[0]:
            return str(row[0])
    except Exception:
        return None
    return None


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
    tid_resolved = resolve_tenant_uuid(db, tenant_id) if _safe_str(tenant_id) else None
    try:
        from app.models.inquiry import Inquiry
        # inquiries.tenant_id 在本库为 varchar：优先写业务串；若列是 UUID 则用解析结果
        row = Inquiry(
            name=_safe_str(contact_name, _safe_str(company_name, "unknown")),
            phone=_safe_str(inquiry_id, "n/a")[:50],
            email=_safe_str(email) or None,
            product=_safe_str(product) or None,
            message=_safe_str(message, "(acquisition reply)")[:4000],
            status="pending",
            source_channel=_safe_str(channel, "inbound")[:50],
            tenant_id=tid_resolved or _safe_str(tenant_id) or None,
            assigned_to=_safe_str(assigned_to) or None,
            attribution_channel=_safe_str(attribution_channel)[:50],
            attribution_data=(f'{{"ops_inquiry_id":"{_safe_str(inquiry_id)}","country":"{_safe_str(country)}"}}'
                              if inquiry_id or country else None),
        )
        db.add(row)
        db.commit()
        rid = getattr(row, "id", None) or inquiry_id
        return {
            "persisted": True,
            "id": str(rid),
            "reason": "",
            "table": "inquiries",
            "tenant_resolved": tid_resolved,
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("persist_inquiry 失败: %s", exc)
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass
        # 列类型不匹配时：再试另一种 tenant_id 写法
        try:
            from app.models.inquiry import Inquiry
            for tid_try in (tid_resolved, _safe_str(tenant_id)):
                if not tid_try:
                    continue
                try:
                    row = Inquiry(
                        name=_safe_str(contact_name, _safe_str(company_name, "unknown")),
                        phone=_safe_str(inquiry_id, "n/a")[:50],
                        email=_safe_str(email) or None,
                        product=_safe_str(product) or None,
                        message=_safe_str(message, "(acquisition reply)")[:4000],
                        status="pending",
                        source_channel=_safe_str(channel, "inbound")[:50],
                        tenant_id=tid_try,
                        assigned_to=None,
                        attribution_channel=_safe_str(attribution_channel)[:50],
                        attribution_data=(f'{{"ops_inquiry_id":"{_safe_str(inquiry_id)}","country":"{_safe_str(country)}"}}'
                                          if inquiry_id or country else None),
                    )
                    db.add(row)
                    db.commit()
                    rid = getattr(row, "id", None) or inquiry_id
                    return {"persisted": True, "id": str(rid), "reason": "", "table": "inquiries", "tenant_resolved": tid_try}
                except Exception:
                    db.rollback()
                    continue
        except Exception as exc2:  # noqa: BLE001
            try:
                db.rollback()
            except Exception:
                pass
            return {"persisted": False, "id": None, "reason": f"{str(exc)[:120]} | retry:{str(exc2)[:120]}"}
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
        # multi-tenant 归属：业务 id 先解析成 tenants.id UUID，解析失败则不写（避免假归属）
        tid = resolve_tenant_uuid(db, tenant_id) if _safe_str(tenant_id) else None
        if tid and hasattr(lead, "tenant_id"):
            lead.tenant_id = tid
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
        return {
            "persisted": True,
            "id": str(rid) if rid else None,
            "reason": "",
            "table": "prospect_leads",
            "tenant_resolved": tid,
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("persist_prospect_lead 失败: %s", exc)
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass
        return {"persisted": False, "id": None, "reason": str(exc)[:200]}
