# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""统一主动搜客 Intake Adapter（W2 · 团队任务 #3）。

**收敛原则**：所有主动来源（Google CSE / LinkedIn / Quora / Reddit / TikTok /
WhatsApp / Sidecar / 海关 / 行业目录 / CSV / 表单）的候选**只能**经此收口，
各来源自身不得再构造 ``BuyerProspectLead`` / ``ProspectLead`` 或自写 INSERT。

三条落库通道（全部复用 ``app.services.acquisition.repo`` 唯一收口）：

1. ``ingest_candidates`` —— 候选池通道：各来源采集到「候选 dict 列表」→
   ``repo.persist_buyer_candidate``（全库唯一构造点）写 ``buyer_prospect_leads``；
   满足晋级条件的候选再由 ``repo.promote_candidate_to_prospect_lead`` 晋级进
   ``prospect_leads`` 主档（``lead_metadata.promoted_from`` 溯源）。
2. ``ingest_found_leads`` —— 已处理通道：Google CSE 等已完成抓取+验证的
   ``FoundLead`` 列表 → ``repo.persist_prospect_lead``（id 幂等）。
3. ``intake`` / ``intake_many`` —— 原始通道：未归一化的原始 dict →
   ``LeadPipeline.create_default()``（标准化→去重→验证→评分→丰富→入库）。

红线：不新建平行业务账本；DB 不可用时明确 ``persisted=false``，不假装成功。
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────
# 通道 1：候选池 + 自动晋级
# ────────────────────────────────────────────────────────────

def _candidate_eligible(candidate: Any, raw: dict) -> bool:
    """晋级条件（契约 §1.4.2，满足其一即可）：
    ① ``evidence_url`` 命中（http/https）且 ``evidence_status='present'``；
    ② ``email`` 命中且 ``email_verified='valid'``。
    （③ 人工「确认采纳」由调用方显式 promote 处理，不在此自动判定。）
    """
    evidence_url = str(raw.get("evidence_url") or "")
    ev_status = str(getattr(candidate, "evidence_status", "") or "")
    if evidence_url.startswith("http") and ev_status == "present":
        return True
    email = str(raw.get("email") or "")
    verified = str(raw.get("email_verified") or "")
    return bool(email and verified == "valid")


def ingest_candidates(
    db: Any,
    prospects: list[dict],
    *,
    tenant_id: str,
    source: str,
    source_tool: str,
    title_default: str = "Prospect",
    suggested_channel: Any = "email",
    region_label: Optional[str] = None,
    notes_builder: Optional[Callable[[dict], str]] = None,
    candidate_kind: str = "scraped",
    extra_out: Optional[list[str]] = None,
    promote: bool = True,
    commit: bool = True,
) -> dict[str, Any]:
    """把某来源的候选 dict 列表收口落库（候选池）+ 自动晋级。

    各来源 Adapter 只需给出：``source``（LeadSource 值）/``source_tool``/
    标题兜底/建议渠道/来源专属 notes 组装器，其余构造细节全部由本函数与
    ``repo`` 承担。

    Returns:
        ``{"prospects": list[dict], "promoted_count": int, "source": str}``
        （``prospects`` 结构与既有各来源返回值 100% 一致，向后兼容）
    """
    from app.services.acquisition.repo import (
        persist_buyer_candidate,
        promote_candidate_to_prospect_lead,
    )

    out: list[dict] = []
    pending: list[tuple[Any, dict]] = []
    for p in prospects or []:
        if not isinstance(p, dict):
            continue
        evidence_url = p.get("evidence_url") or ""
        if notes_builder is not None:
            try:
                notes = notes_builder(p)
            except Exception:  # noqa: BLE001
                notes = p.get("notes") or ""
        else:
            notes = p.get("notes") or ""
        cres = persist_buyer_candidate(
            db,
            tenant_id=tenant_id,
            title=p.get("title") or title_default,
            region_label=region_label if region_label is not None else p.get("country", ""),
            country_code=p.get("country_code") or "XX",
            buyer_type=p.get("buyer_type") or "importer",
            fit_score=p.get("fit_score") or 65,
            suggested_channel=(suggested_channel(p) if callable(suggested_channel)
                               else suggested_channel),
            notes=notes,
            source_tool=source_tool,
            candidate_kind=candidate_kind,
            evidence_url=evidence_url,
        )
        row = cres.get("row")
        if row is None:
            # 诚实降级：单条失败不拖垮整批，记录原因
            logger.warning("[intake] 候选落库失败 source=%s reason=%s", source, cres.get("reason"))
            continue
        pending.append((row, p))
        out_row = {
            "id": row.id,
            "title": row.title,
            "buyer_type": row.buyer_type,
            "country_code": row.country_code,
            "fit_score": row.fit_score,
            "suggested_channel": row.suggested_channel,
            "notes": p.get("notes"),
            "evidence_url": p.get("evidence_url"),
            "email": p.get("email"),
            "email_source_url": p.get("evidence_url"),
            "confidence": p.get("confidence"),
            "verification_status": "待核实候选",
        }
        # 来源专属透传字段（如 WhatsApp 的 phone/whatsapp_number/whatsapp_link）
        for key in (extra_out or []):
            out_row[key] = p.get(key)
        out.append(out_row)

    if commit:
        try:
            db.commit()
        except Exception as exc:  # noqa: BLE001
            logger.warning("[intake] 候选池提交失败: %s", exc)
            try:
                db.rollback()
            except Exception:  # noqa: BLE001
                pass

    promoted = 0
    if promote:
        for row, p in pending:
            if not _candidate_eligible(row, p):
                continue
            pres = promote_candidate_to_prospect_lead(
                db,
                row,
                email=p.get("email") or "",
                company_name=p.get("company_name") or p.get("company") or "",
                country=p.get("country_code") or p.get("country") or "",
                website=p.get("website") or "",
                industry=p.get("industry") or "",
                linkedin_url=p.get("linkedin_url") or "",
                source=p.get("source") or source,
                evidence_url=p.get("evidence_url") or "",
                extra_metadata={"candidate_source_tool": source_tool},
            )
            if pres.get("promoted"):
                promoted += 1
    return {"prospects": out, "promoted_count": promoted, "source": source}


# ────────────────────────────────────────────────────────────
# 通道 2：已处理线索（FoundLead 列表）→ 主档（幂等）
# ────────────────────────────────────────────────────────────

def ingest_found_leads(
    db: Any,
    leads: list,
    *,
    tenant_id: str = "",
    keyword: str = "",
    source: str = "google_cse",
) -> dict:
    """Google CSE 等「已抓取+验证」的 ``FoundLead`` 列表 → ``prospect_leads``（幂等）。

    与 ``lead_generation.persist_found_leads`` 行为一致（向后兼容），
    但把收口逻辑集中到本 Adapter，供同步 ``/search`` 与异步 ``/search-async`` 共用。

    Returns:
        ``{"persisted_count": int, "persisted_ids": list[str], "skipped": list[dict]}``
    """
    from app.services.acquisition.repo import persist_prospect_lead

    created = 0
    ids: list[str] = []
    skipped: list[dict] = []
    for lead in leads or []:
        # asyncio.gather(return_exceptions=True) 可能带入异常对象 → 跳过
        if not hasattr(lead, "emails"):
            continue
        best = next((e for e in lead.emails if e and getattr(e, "email", None)), None)
        if best is None:
            skipped.append({
                "company_name": getattr(lead, "company_name", None),
                "website": getattr(lead, "website", None),
                "reason": "no_email",
            })
            continue
        result = persist_prospect_lead(
            db,
            tenant_id=tenant_id,
            email=best.email,
            company_name=getattr(lead, "company_name", "") or "",
            country=getattr(lead, "country", "") or "",
            website=getattr(lead, "website", "") or "",
            source=source,
            status="discovered",
            source_detail={"search_keyword": keyword, "page_url": getattr(lead, "website", "")},
            lead_metadata={
                "search_keyword": keyword,
                "page_url": getattr(lead, "website", ""),
                "snippet": getattr(lead, "snippet", None),
                "domain": getattr(lead, "domain", None),
                "email_confidence": getattr(best, "confidence", None),
                "email_verification_status": getattr(best, "verification_status", None),
            },
        )
        action = result.get("action")
        if action == "created":
            created += 1
            if result.get("id"):
                ids.append(result["id"])
        elif action == "duplicate":
            skipped.append({
                "company_name": getattr(lead, "company_name", None),
                "email": best.email,
                "reason": "duplicate_email_tenant",
                "existing_id": result.get("id"),
            })
        else:
            skipped.append({
                "company_name": getattr(lead, "company_name", None),
                "email": best.email,
                "reason": result.get("reason") or "persist_failed",
            })
    return {"persisted_count": created, "persisted_ids": ids, "skipped": skipped}


# ────────────────────────────────────────────────────────────
# 通道 3：原始 dict → LeadPipeline（标准化→去重→验证→评分→丰富→入库）
# ────────────────────────────────────────────────────────────

async def intake(raw: dict, *, source: str, tenant_id: str = "") -> dict[str, Any]:
    """单条原始候选 → ``LeadPipeline.create_default()`` 全链处理并入库。

    Returns:
        ``{"persisted", "id", "status", "action", "duplicate_of", "errors"}``
    """
    from app.services.ubrain.lead_processing_pipeline import LeadPipeline

    data: dict[str, Any] = dict(raw or {})
    data.setdefault("source", source)
    if tenant_id:
        data.setdefault("tenant_id", tenant_id)
    ctx = await LeadPipeline.create_default().process(data)
    persist_meta = (ctx.metadata or {}).get("persist") or {}
    status_val = getattr(ctx.status, "value", ctx.status)
    return {
        "persisted": bool(persist_meta.get("lead_id")) and str(status_val) == "completed",
        "id": persist_meta.get("lead_id"),
        "status": str(status_val),
        "action": persist_meta.get("action"),
        "duplicate_of": ctx.duplicate_of,
        "errors": list(ctx.errors or []),
    }


async def intake_many(
    raws: list[dict], *, source: str, tenant_id: str = "", max_concurrent: int = 5,
) -> list[dict[str, Any]]:
    """批量原始候选 → 逐条走 Pipeline（受控并发）。"""
    import asyncio

    semaphore = asyncio.Semaphore(max(1, int(max_concurrent)))

    async def _one(item: dict) -> dict[str, Any]:
        async with semaphore:
            try:
                return await intake(item, source=source, tenant_id=tenant_id)
            except Exception as exc:  # noqa: BLE001
                logger.warning("[intake] pipeline 失败: %s", exc)
                return {"persisted": False, "id": None, "status": "failed",
                        "action": "error", "duplicate_of": None, "errors": [str(exc)[:200]]}

    return await asyncio.gather(*[_one(r) for r in (raws or [])])
