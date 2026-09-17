# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""外贸标杆能力 — 智能体编排门面（UBrain / Hermes / DeerFlow 统一入口）。"""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.services.foreign_trade.osint_service import run_osint_check
from app.services.foreign_trade.prospect_cleaner_service import clean_prospect_records
from app.services.foreign_trade.trade_document_service import build_proforma_invoice
from app.services.foreign_trade.website_icp_service import analyze_website_icp
from app.services.onboarding_chain_service import tenant_site_urls
from app.services.ubrain.tenant_memory_service import get_memory, record_tool_use

_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_DOMAIN_RE = re.compile(
    r"\b(?:https?://)?(?:www\.)?([a-z0-9][-a-z0-9]*(?:\.[-a-z0-9]+)+)\b",
    re.I,
)


def agent_envelope(
    skill_id: str,
    *,
    status: str = "ok",
    summary: str = "",
    data: dict[str, Any] | None = None,
    next_actions: list[str] | None = None,
    human_review_required: bool = False,
    expert_id: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """智能体统一返回包 — 供 UBrain / DeerFlow / 飞轮步骤消费。"""
    return {
        "skill_id": skill_id,
        "status": status,
        "summary": summary,
        "data": data or {},
        "next_actions": next_actions or [],
        "human_review_required": human_review_required,
        "expert_id": expert_id,
        **extra,
    }


def extract_osint_target(message: str, ctx: dict[str, Any] | None = None) -> str | None:
    """从用户消息或 context 提取背调目标（邮箱 > 域名 > target 字段）。"""
    ctx = ctx or {}
    if ctx.get("target"):
        return str(ctx["target"]).strip()
    if ctx.get("email"):
        return str(ctx["email"]).strip()
    if ctx.get("domain"):
        d = str(ctx["domain"]).strip()
        return d if d.startswith("http") else f"https://{d}"
    m = (message or "").strip()
    em = _EMAIL_RE.search(m)
    if em:
        return em.group(0)
    dm = _DOMAIN_RE.search(m)
    if dm:
        return dm.group(1)
    quoted = re.search(r"[「\"']([^「\"']+@[^「\"']+)[」\"']", m)
    if quoted:
        return quoted.group(1)
    return None


def extract_website_url(message: str, ctx: dict[str, Any] | None = None) -> str | None:
    """实现 提取websiteURL 的功能。
    
    :param message: 参数 message（类型: str）
    :param ctx: 参数 ctx（类型: dict[str, Any] | None）
    :return: 返回 str | None 结果
    """
    ctx = ctx or {}
    if ctx.get("website_url"):
        return str(ctx["website_url"]).strip()
    if ctx.get("domain"):
        d = str(ctx["domain"]).strip()
        return d if d.startswith("http") else f"https://{d}"
    m = (message or "").strip()
    url = re.search(r"https?://[^\s]+", m)
    if url:
        return url.group(0).rstrip(".,)")
    dm = _DOMAIN_RE.search(m)
    if dm:
        return f"https://{dm.group(1)}"
    return None


def resolve_tenant_website_url(db: Session, tenant_id: str) -> str | None:
    """实现 解析租户websiteURL 的功能。
    
    :param db: 参数 db（类型: Session）
    :param tenant_id: 参数 tenant_id（类型: str）
    :return: 返回 str | None 结果
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return None
    urls = tenant_site_urls(tenant)
    return urls.get("production") or None


def run_osint_agent(
    target: str,
    *,
    include_sanctions: bool = True,
    include_tech_stack: bool = True,
    include_linkedin: bool = True,
) -> dict[str, Any]:
    """背调专员 — 六层 OSINT。"""
    report = run_osint_check(
        target,
        include_sanctions=include_sanctions,
        include_tech_stack=include_tech_stack,
        include_linkedin=include_linkedin,
    )
    from app.services.crawlers.ecommerce_crawlers_sidecar import enrich_osint_with_qichacha
    qcc = enrich_osint_with_qichacha(target)
    if qcc:
        report["ecommerce_enrichment"] = qcc
    rating = report.get("overall_rating") or "unknown"
    score = report.get("overall_score", 0)
    flags = report.get("flags") or []
    summary = f"背调完成：风险 {rating}（{score}/100）"
    if flags:
        summary += f"，标记 {len(flags)} 项"
    next_actions = list(report.get("recommendations") or [])[:3]
    if rating == "high":
        next_actions.insert(0, "高风险：暂缓深入谈判，要求企业邮箱与资质证明")
    return agent_envelope(
        "osint_background_check",
        summary=summary,
        data=report,
        next_actions=next_actions,
        human_review_required=True,
        expert_id="expert_diligence",
        gw_task="osint_background_check",
    )


def run_website_icp_agent(
    db: Session,
    tenant_id: str,
    *,
    website_url: str | None = None,
    message: str = "",
    ctx: dict[str, Any] | None = None,
    max_pages: int = 5,
    persist_memory: bool = True,
) -> dict[str, Any]:
    """建站/onboarding — 官网 ICP 画像并可选写入租户记忆。"""
    url = website_url or extract_website_url(message, ctx) or resolve_tenant_website_url(db, tenant_id)
    if not url:
        return agent_envelope(
            "factory_onboarding_icp",
            status="needs_input",
            summary="未找到官网 URL，请提供域名或先完成建站。",
            next_actions=["完成 Hermes 建站", "或直接说「分析 example.com 官网 ICP」"],
            expert_id="expert_site",
        )
    raw = analyze_website_icp(url, max_pages=max_pages)
    icp = raw.get("icp") or {}
    summary = (
        f"已分析 {icp.get('domain') or url}："
        f"{icp.get('company_name', '')}；"
        f"抓取 {raw.get('pages') and len(raw['pages']) or 0} 页"
    )
    if persist_memory:
        patch: dict[str, Any] = {"website_url": icp.get("website") or url}
        if icp.get("value_props"):
            patch["icp_value_props"] = icp["value_props"][:500]
        if icp.get("certifications"):
            patch["icp_certifications"] = icp["certifications"][:10]
        if icp.get("product_pages"):
            patch["product_category"] = icp["product_pages"][0][:80]
        record_tool_use(db, tenant_id, "website_icp", context_patch=patch)
    return agent_envelope(
        "factory_onboarding_icp",
        summary=summary,
        data=raw,
        next_actions=raw.get("next_steps") or [],
        human_review_required=True,
        expert_id="expert_site",
        gw_task="factory_onboarding_icp",
    )


def run_proforma_agent(
    db: Session,
    tenant_id: str,
    *,
    message: str = "",
    ctx: dict[str, Any] | None = None,
    buyer: dict[str, Any] | None = None,
    lines: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """谈单顾问 — 形式发票 PI。"""
    mem = get_memory(db, tenant_id)
    ctx = ctx or {}
    company = mem.get("company_name") or mem.get("brand_name") or "Seller"
    seller = ctx.get("seller") or {
        "name": company,
        "address": ctx.get("seller_address") or "",
        "email": ctx.get("seller_email") or "",
    }
    buyer_payload = buyer or ctx.get("buyer") or _parse_buyer_from_message(message)
    line_items = lines or ctx.get("lines") or _parse_lines_from_message(message)
    if not line_items:
        line_items = [
            {
                "description": mem.get("product_category") or "Product",
                "quantity": 100,
                "unit_price": 0,
                "unit": "pcs",
            }
        ]
    doc = build_proforma_invoice(
        seller=seller,
        buyer=buyer_payload,
        lines=line_items,
        currency=str(ctx.get("currency") or "USD"),
        payment_terms=str(ctx.get("payment_terms") or "30% deposit, 70% before shipment"),
        delivery_terms=str(ctx.get("delivery_terms") or "FOB"),
        validity_days=int(ctx.get("validity_days") or 15),
        notes=str(ctx.get("notes") or ""),
    )
    record_tool_use(db, tenant_id, "proforma_invoice")
    return agent_envelope(
        "trade_doc_pi_contract",
        summary=f"已生成 PI {doc['pi_no']}，合计 {doc['subtotal']} {doc['currency']}",
        data=doc,
        next_actions=[
            "人工核对 MOQ/单价/条款后导出 PDF",
            "可结合 negotiation_draft 生成还价话术",
        ],
        human_review_required=True,
        expert_id="expert_negotiate",
        gw_task="trade_doc_pi_contract",
    )


def run_prospect_clean_agent(
    customers: list[dict[str, Any]],
    *,
    existing: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """找客专员 — 潜客去重打标。"""
    out = clean_prospect_records(customers, existing=existing)
    stats = out.get("stats") or {}
    return agent_envelope(
        "prospect_data_clean",
        summary=(
            f"清洗完成：输入 {stats.get('total_in', 0)} 条 → "
            f"输出 {stats.get('total_out', 0)} 条"
        ),
        data=out,
        next_actions=["对 high intent 线索优先 OSINT 背调", "再生成 outreach_letter_pack"],
        human_review_required=False,
        expert_id="expert_eva",
    )


def enrich_buyers_with_clean_and_osint(
    buyers: dict[str, Any],
    *,
    message: str = "",
    osint_limit: int = 1,
) -> dict[str, Any]:
    """飞轮步骤：找客结果 → 清洗 → 可选首条背调（不阻塞主流程）。"""
    prospects = buyers.get("prospects") or []
    as_customers = [
        {
            "email": p.get("email"),
            "phone": p.get("phone"),
            "title": p.get("title"),
            "notes": p.get("notes"),
            "platform": p.get("buyer_type"),
            "evidence_url": p.get("evidence_url"),
        }
        for p in prospects
    ]
    cleaned = run_prospect_clean_agent(as_customers)
    osint_reports: list[dict[str, Any]] = []
    target = extract_osint_target(message)
    if target and osint_limit > 0:
        try:
            osint_reports.append(run_osint_agent(target))
        except Exception as exc:
            osint_reports.append(
                agent_envelope(
                    "osint_background_check",
                    status="error",
                    summary=str(exc)[:120],
                )
            )
    return {
        "prospect_clean": cleaned,
        "osint_samples": osint_reports,
        "buyer_count": buyers.get("count", 0),
        "find_mode": buyers.get("mode"),
    }


def run_find_buyers_agent(
    db: Session,
    *,
    tenant_id: str,
    message: str,
    memory: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """找客专员 — Sidecar 优先 + Accio 模板兜底 + 清洗标记（Eric 全链路仅编排，不搬 SMTP）。"""
    from app.services.ubrain.accio_sales_service import find_buyer_prospects
    raw = find_buyer_prospects(db, tenant_id=tenant_id, message=message, memory=memory)
    enriched = enrich_buyers_with_clean_and_osint(raw, message=message, osint_limit=1)
    mode = raw.get("mode") or "accio_buyer_discovery"
    summary = f"找客完成（{mode}）：{raw.get('count', 0)} 条待核实候选"
    return agent_envelope(
        "find_buyers",
        summary=summary,
        data={**raw, "enrichment": enriched},
        next_actions=[
            "人工核实 evidence_url / 企业邮箱",
            "高 fit 线索生成 outreach_letter_pack（草稿，不自动发送）",
        ],
        human_review_required=True,
        expert_id="expert_eva",
        gw_task="find_buyers",
        workflow_ref="Eric_Frank/LangGraph（参考编排，未并入社媒爬虫与 SMTP）",
    )


def _parse_buyer_from_message(message: str) -> dict[str, Any]:
    """实现 解析buyerfrom消息 的功能。
    
    :param message: 参数 message（类型: str）
    :return: 返回 dict[str, Any] 结果
    """
    em = _EMAIL_RE.search(message or "")
    return {
        "name": "Buyer",
        "company": "Buyer Co",
        "country": "",
        "email": em.group(0) if em else "",
        "code": "B01",
    }


def _parse_lines_from_message(message: str) -> list[dict[str, Any]]:
    """实现 解析linesfrom消息 的功能。
    
    :param message: 参数 message（类型: str）
    :return: 返回 list[dict[str, Any]] 结果
    """
    qty_price = re.search(
        r"(\d+)\s*(?:pcs|件|个)?\s*[@×x]\s*\$?\s*([\d.]+)",
        message or "",
        re.I,
    )
    if qty_price:
        return [
            {
                "description": "Line item",
                "quantity": float(qty_price.group(1)),
                "unit_price": float(qty_price.group(2)),
                "unit": "pcs",
            }
        ]
    return []


def inquiry_osint_target(inquiry: Any) -> str | None:
    """从询盘记录解析背调目标。"""
    email = getattr(inquiry, "email", None) or ""
    if str(email).strip():
        return str(email).strip()
    message = getattr(inquiry, "message", None) or ""
    name = getattr(inquiry, "name", None) or ""
    return extract_osint_target(f"{message}\n{name}")


def run_inquiry_osint_agent(db: Session, inquiry: Any) -> dict[str, Any]:
    """询盘详情 — 一键背调。"""
    target = inquiry_osint_target(inquiry)
    if not target:
        return agent_envelope(
            "osint_background_check",
            status="needs_input",
            summary="该询盘无邮箱且留言中未识别域名，无法背调。",
            next_actions=["向客户索要企业邮箱", "或提供域名后说「背调 example.com」"],
            expert_id="expert_diligence",
        )
    result = run_osint_agent(target)
    tid = getattr(inquiry, "tenant_id", None)
    if tid:
        record_tool_use(db, str(tid), "osint_check", context_patch={"last_osint_target": target})
    result["inquiry_id"] = getattr(inquiry, "id", None)
    return result


def run_inquiry_proforma_agent(
    db: Session,
    tenant_id: str,
    inquiry: Any,
) -> dict[str, Any]:
    """询盘详情 — 生成 PI 草稿。"""
    mem = get_memory(db, tenant_id)
    product = getattr(inquiry, "product", None) or mem.get("product_category") or "Product"
    buyer = {
        "name": getattr(inquiry, "name", None) or "Buyer",
        "company": getattr(inquiry, "name", None) or "Buyer Co",
        "email": getattr(inquiry, "email", None) or "",
        "country": "",
        "code": str(getattr(inquiry, "id", "INQ"))[:8].upper(),
    }
    lines = [
        {
            "description": product,
            "quantity": 100,
            "unit_price": 0,
            "unit": "pcs",
        }
    ]
    result = run_proforma_agent(db, tenant_id, buyer=buyer, lines=lines)
    result["inquiry_id"] = getattr(inquiry, "id", None)
    return result
