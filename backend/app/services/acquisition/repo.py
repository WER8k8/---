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
    # ── W3 扩展（入站总线收口用）：全部可选，向后兼容 ──
    phone: str = "",
    name: str = "",
    status: str = "",
    session_id: str = "",
    source_channel: str = "",
    priority_score: Optional[int] = None,
    provenance_metadata: Optional[dict] = None,
) -> dict[str, Any]:
    """尽力写入 inquiries 表。返回 {persisted, id, reason}。

    W3 扩展：入站渠道（WhatsApp / 邮件 / 表单）可显式传 ``phone``/``name``/
    ``status``/``session_id``/``source_channel``/``priority_score``/``provenance_metadata``；
    缺省时保持既有行为不变（``phone`` 回落 ``inquiry_id``、``status='pending'``）。
    """
    if db is None:
        return {"persisted": False, "id": None, "reason": "db_unavailable"}
    tid_resolved = resolve_tenant_uuid(db, tenant_id) if _safe_str(tenant_id) else None

    def _common_kwargs(tid_try: Any) -> dict[str, Any]:
        kw: dict[str, Any] = {
            "name": _safe_str(name) or _safe_str(contact_name, _safe_str(company_name, "unknown")),
            "phone": (_safe_str(phone)[:50] or _safe_str(inquiry_id, "n/a")[:50]),
            "email": _safe_str(email) or None,
            "product": _safe_str(product) or None,
            "message": _safe_str(message, "(acquisition reply)")[:4000],
            "status": _safe_str(status) or "pending",
            "source_channel": (_safe_str(source_channel) or _safe_str(channel, "inbound"))[:50],
            "tenant_id": tid_try,
            "assigned_to": _safe_str(assigned_to) or None,
            "attribution_channel": _safe_str(attribution_channel)[:50],
            "attribution_data": (f'{{"ops_inquiry_id":"{_safe_str(inquiry_id)}","country":"{_safe_str(country)}"}}'
                                 if inquiry_id or country else None),
        }
        if session_id:
            kw["session_id"] = _safe_str(session_id)[:64]
        if priority_score is not None:
            kw["priority_score"] = max(0, min(100, int(priority_score)))
        if provenance_metadata:
            kw["provenance_metadata"] = provenance_metadata
        return kw

    try:
        from app.models.inquiry import Inquiry
        # inquiries.tenant_id 在本库为 varchar：优先写业务串；若列是 UUID 则用解析结果
        row = Inquiry(**_common_kwargs(tid_resolved or _safe_str(tenant_id) or None))
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
                    row = Inquiry(**_common_kwargs(tid_try))
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


def _clamp_score(value: Any, default: int = 0) -> int:
    """把任意分数夹取到 0-100 整数（满足 prospect_leads 的 CHECK 约束）。"""
    try:
        return max(0, min(100, int(round(float(value)))))
    except (TypeError, ValueError):
        return default


def _split_score_breakdown(breakdown: Optional[dict]) -> dict[str, int]:
    """把评分引擎的多维 breakdown 拆入 ProspectLead 的 4 个子分字段。

    映射（缺失维度取 0）：
      - score_email    ← email_quality
      - score_match    ← company_completeness
      - score_evidence ← source_quality
      - score_contact  ← title_match
    其余维度（activity_signals / geo_match 等）不落子分，由调用方写入 lead_metadata。
    """
    def _dim(key: str) -> int:
        v = (breakdown or {}).get(key)
        if isinstance(v, dict):
            v = v.get("score")
        return _clamp_score(v, 0)

    return {
        "score_email": _dim("email_quality"),
        "score_match": _dim("company_completeness"),
        "score_evidence": _dim("source_quality"),
        "score_contact": _dim("title_match"),
    }


def _coerce_lead_source(value: Any, channel: str) -> Any:
    """把任意来源串归一为 LeadSource 枚举（非法值兜底 manual_import）。"""
    from app.models.prospect_lead import LeadSource

    if isinstance(value, LeadSource):
        return value
    raw = (_safe_str(value) or _safe_str(channel) or "manual_import").lower()
    aliases = {
        "inbound": LeadSource.MANUAL_IMPORT,
        "manual": LeadSource.MANUAL_IMPORT,
        "manual_import": LeadSource.MANUAL_IMPORT,
        "csv": LeadSource.MANUAL_IMPORT,
        "csv_import": LeadSource.MANUAL_IMPORT,
        "reply_ingest": LeadSource.MANUAL_IMPORT,
        "email": LeadSource.HUNTER_IO,
        "linkedin": LeadSource.LINKEDIN,
        "whatsapp": LeadSource.WHATSAPP,
        "google": LeadSource.GOOGLE_CSE,
        "google_cse": LeadSource.GOOGLE_CSE,
        "website": LeadSource.WEBSITE_SCRAPE,
        "website_scrape": LeadSource.WEBSITE_SCRAPE,
        "referral": LeadSource.REFERRAL,
    }
    if raw in aliases:
        return aliases[raw]
    try:
        return LeadSource(raw)
    except ValueError:
        return LeadSource.MANUAL_IMPORT


def _coerce_lead_status(value: Any) -> Any:
    """把任意状态串归一为 LeadStatus 枚举（非法值/"new" 兜底 discovered）。"""
    from app.models.prospect_lead import LeadStatus

    if isinstance(value, LeadStatus):
        return value
    raw = _safe_str(value).lower()
    if not raw:
        return LeadStatus.DISCOVERED
    try:
        return LeadStatus(raw)
    except ValueError:
        return LeadStatus.DISCOVERED


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
    # ── W1 扩展（P0-2 / P0-4）：全部可选，向后兼容既有调用点 ──
    website: str = "",
    industry: str = "",
    linkedin_url: str = "",
    source: Any = None,
    status: Any = None,
    overall_score: Any = None,
    score_breakdown: Optional[dict] = None,
    lead_metadata: Optional[dict] = None,
    source_detail: Optional[dict] = None,
    dedup: bool = True,
    # ── W2 扩展（Intake Adapter 收口用）：全部可选，向后兼容 ──
    phone: str = "",
    domain: str = "",
    email_verified: str = "",
    fit_score: Any = None,
    provenance_metadata: Optional[dict] = None,
    notes: str = "",
) -> dict[str, Any]:
    """统一线索落库入口（唯一收口）——尽力写入 ``prospect_leads``。

    幂等（P0-4）：命中 ``uq_prospect_lead_email_tenant`` 唯一约束时降级为「跳过」，
    返回既有 id，不抛 500、不产生重复行。

    Returns:
        ``{persisted, id, action, reason, table, tenant_resolved}``

        - ``action``: ``created`` / ``duplicate`` / ``skipped`` / ``error``
        - ``persisted``: 仅当**新写入**成功为 ``True``
    """
    if db is None:
        return {"persisted": False, "id": None, "action": "skipped",
                "reason": "db_unavailable", "table": "prospect_leads", "tenant_resolved": None}
    if not email and not company_name and not contact_name:
        return {"persisted": False, "id": None, "action": "skipped",
                "reason": "no_identity_fields", "table": "prospect_leads", "tenant_resolved": None}

    from sqlalchemy.exc import IntegrityError

    tid = resolve_tenant_uuid(db, tenant_id) if _safe_str(tenant_id) else None
    try:
        # 注意：模型导入放在 try 内 —— 保证任何导入/构造失败都走「诚实降级」，
        # 不向调用方抛裸异常（既有单测依赖该语义）。
        from app.models.prospect_lead import LeadStatus, ProspectLead

        src = _coerce_lead_source(source, channel)
        st = _coerce_lead_status(status) if status is not None else LeadStatus.DISCOVERED
        first = contact_name
        last = ""
        if contact_name and " " in contact_name:
            parts = contact_name.split(None, 1)
            first, last = parts[0], parts[1]
        _default_notes = (f"ops_inquiry={_safe_str(inquiry_ref)}; buyer_type={_safe_str(buyer_type)}"
                          if inquiry_ref or buyer_type else None)
        lead = ProspectLead(
            email=_safe_str(email) or None,
            company_name=_safe_str(company_name) or None,
            country=_safe_str(country)[:8] or None,
            website=_safe_str(website) or None,
            industry=_safe_str(industry) or None,
            linkedin_url=_safe_str(linkedin_url) or None,
            first_name=_safe_str(first) or None,
            last_name=_safe_str(last) or None,
            title=_safe_str(contact_title) or None,
            notes=_safe_str(notes) or _default_notes,
        )
        # W2：可选扩展字段（候选晋级 / 种子导入需要，缺省不写）
        if phone and hasattr(lead, "phone"):
            lead.phone = _safe_str(phone)[:50] or None
        if domain and hasattr(lead, "domain"):
            lead.domain = _safe_str(domain) or None
        if email_verified and hasattr(lead, "email_verified"):
            lead.email_verified = _safe_str(email_verified)[:20]
        if fit_score is not None and hasattr(lead, "fit_score"):
            lead.fit_score = _clamp_score(fit_score, 50)
        if provenance_metadata and hasattr(lead, "provenance_metadata"):
            lead.provenance_metadata = provenance_metadata
        # multi-tenant 归属：业务 id 先解析成 tenants.id UUID，解析失败则不写（避免假归属）
        if tid and hasattr(lead, "tenant_id"):
            lead.tenant_id = tid
        if hasattr(lead, "source"):
            lead.source = src
        if hasattr(lead, "status"):
            lead.status = st
        if source_detail:
            lead.source_detail = source_detail
        if lead_metadata:
            lead.lead_metadata = lead_metadata
        # 评分：overall 优先，子分按 4 维拆入
        if overall_score is not None:
            lead.overall_score = _clamp_score(overall_score, 0)
        subs = _split_score_breakdown(score_breakdown)
        for attr, val in subs.items():
            if hasattr(lead, attr):
                setattr(lead, attr, val)
        db.add(lead)
        db.commit()
        rid = getattr(lead, "id", None)
        return {
            "persisted": True,
            "id": str(rid) if rid else None,
            "action": "created",
            "reason": "",
            "table": "prospect_leads",
            "tenant_resolved": tid,
        }
    except IntegrityError:
        # 幂等：email(+tenant) 命中唯一约束 → 跳过，返回既有线索 id
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass
        existing_id = None
        if dedup and _safe_str(email):
            try:
                row = (
                    db.query(ProspectLead)
                    .filter(ProspectLead.email == _safe_str(email))
                    .filter(ProspectLead.tenant_id == tid if tid else ProspectLead.tenant_id.is_(None))
                    .first()
                )
                existing_id = str(getattr(row, "id", "")) or None
            except Exception:  # noqa: BLE001
                existing_id = None
        return {
            "persisted": False,
            "id": existing_id,
            "action": "duplicate",
            "reason": "duplicate_email_tenant",
            "table": "prospect_leads",
            "tenant_resolved": tid,
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("persist_prospect_lead 失败: %s", exc)
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass
        return {"persisted": False, "id": None, "action": "error",
                "reason": str(exc)[:200], "table": "prospect_leads", "tenant_resolved": tid}


def persist_buyer_candidate(
    db: Any,
    *,
    tenant_id: str = "",
    title: str = "",
    region_label: str = "",
    country_code: str = "",
    buyer_type: str = "importer",
    fit_score: Any = 65,
    suggested_channel: str = "email",
    notes: str = "",
    source_tool: str = "",
    candidate_kind: str = "scraped",
    evidence_url: str = "",
    evidence_status: str = "",
    verified: bool = False,
    status: str = "discovered",
    commit: bool = False,
) -> dict[str, Any]:
    """候选池唯一构造入口（W2 · Intake Adapter 收口）。

    把各来源（Google / LinkedIn / Quora / Reddit / TikTok / WhatsApp / Sidecar）
    原先散落的 ``BuyerProspectLead(...)`` 直写收敛到此一处，便于
    ``grep -c 'BuyerProspectLead('`` 验收（仅 ``repo.py`` + Accio 画像生成处）。

    诚实降级：``db is None`` 或构造失败 → ``persisted=False, row=None``，不抛裸异常。

    Returns:
        ``{"persisted": bool, "id": str|None, "row": BuyerProspectLead|None, "reason": str}``
    """
    if db is None:
        return {"persisted": False, "id": None, "row": None, "reason": "db_unavailable"}
    try:
        from app.models.ubrain_accio import BuyerProspectLead

        kind = _safe_str(candidate_kind, "scraped")
        if kind not in ("archetype", "scraped", "imported"):
            kind = "scraped"
        ev_url = _safe_str(evidence_url)
        ev_status = _safe_str(evidence_status) or ("present" if ev_url.startswith("http") else "missing")
        row = BuyerProspectLead(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id or None,
            region_label=(_safe_str(region_label) or "unknown")[:80],
            country_code=(_safe_str(country_code) or "XX")[:8],
            buyer_type=(_safe_str(buyer_type) or "importer")[:40],
            title=(_safe_str(title) or "Prospect")[:200],
            fit_score=_clamp_score(fit_score, 65),
            suggested_channel=(_safe_str(suggested_channel) or "email")[:40],
            notes=_safe_str(notes) or None,
            status=(_safe_str(status) or "discovered")[:20],
            source_tool=(_safe_str(source_tool) or "find_buyers")[:64],
            candidate_kind=kind,
            verified=bool(verified),
            evidence_status=ev_status[:20],
        )
        db.add(row)
        if commit:
            db.commit()
        return {
            "persisted": True,
            "id": str(row.id),
            "row": row,
            "reason": "",
            "evidence_url": ev_url,
            "evidence_status": ev_status[:20],
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("persist_buyer_candidate 失败: %s", exc)
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass
        return {"persisted": False, "id": None, "row": None, "reason": str(exc)[:200]}


def promote_candidate_to_prospect_lead(
    db: Any,
    candidate: Any,
    *,
    email: str = "",
    company_name: str = "",
    country: str = "",
    website: str = "",
    industry: str = "",
    linkedin_url: str = "",
    contact_name: str = "",
    source: Any = None,
    overall_score: Any = None,
    evidence_url: str = "",
    extra_metadata: Optional[dict] = None,
) -> dict[str, Any]:
    """候选人 → 统一线索主档**自动晋级**（W2-2）。

    晋级动作：经 ``persist_prospect_lead`` 写 ``prospect_leads``（唯一主档），
    ``lead_metadata.promoted_from`` 记录来源候选 id，``source_detail`` 保留证据；
    候选行 ``status`` 置 ``promoted``。

    晋级条件由调用方判定（本函数只执行落地）。返回 ``{promoted, id, action, reason}``。
    """
    if candidate is None or db is None:
        return {"promoted": False, "id": None, "action": "skipped", "reason": "no_candidate"}
    cid = _safe_str(getattr(candidate, "id", ""))
    meta: dict[str, Any] = {"promoted_from": cid} if cid else {}
    meta.update(extra_metadata or {})
    res = persist_prospect_lead(
        db,
        tenant_id=_safe_str(getattr(candidate, "tenant_id", "")),
        email=email,
        company_name=company_name or _safe_str(getattr(candidate, "title", "")),
        country=country or _safe_str(getattr(candidate, "country_code", "")),
        website=website,
        industry=industry,
        linkedin_url=linkedin_url,
        contact_name=contact_name,
        source=source or _safe_str(getattr(candidate, "suggested_channel", "")) or "manual_import",
        status="discovered",
        overall_score=(overall_score if overall_score is not None
                       else getattr(candidate, "fit_score", None)),
        lead_metadata=meta,
        source_detail={
            "promoted_from": cid,
            "evidence_url": evidence_url,
            "source_tool": _safe_str(getattr(candidate, "source_tool", "")),
        },
    )
    action = res.get("action")
    promoted = action in ("created", "duplicate")
    if promoted:
        try:
            candidate.status = "promoted"
            db.commit()
        except Exception as exc:  # noqa: BLE001
            logger.warning("标记候选 promoted 失败: %s", exc)
            try:
                db.rollback()
            except Exception:  # noqa: BLE001
                pass
    return {"promoted": promoted, "id": res.get("id"), "action": action,
            "reason": res.get("reason", "")}
