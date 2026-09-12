"""AccioWork 卖货核心：找客、开发信、谈单草稿（画像级 + 人审发送）。"""

from __future__ import annotations

import json
import re
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.ubrain_accio import BuyerProspectLead
from app.services.trade_intel_service import blue_ocean
from app.services.ubrain.commercial_os_bridge import retrieve_insights_for_accio
from app.services.ubrain.outreach_deliverability_service import (
    enrich_letter,
    pack_deliverability_summary,
)
from app.services.ubrain.tenant_memory_service import get_memory, record_tool_use
from app.services.tenant_product_profile_service import require_product_profile_for_outreach

_REGION_COUNTRIES: dict[str, list[str]] = {
    "中东": ["SA", "AE", "QA", "KW", "OM"],
    "东南亚": ["VN", "TH", "MY", "ID", "PH"],
    "南亚": ["IN", "BD", "PK"],
    "非洲": ["NG", "KE", "EG", "ZA"],
    "拉美": ["MX", "BR", "CL"],
    "欧美": ["US", "DE", "PL"],
}

_COUNTRY_ALIASES: dict[str, str] = {
    "沙特": "SA",
    "阿联酋": "AE",
    "越南": "VN",
    "泰国": "TH",
    "印尼": "ID",
    "印度": "IN",
    "美国": "US",
    "德国": "DE",
    "墨西哥": "MX",
}

_BUYER_ARCHETYPES: list[tuple[str, str, str]] = [
    ("distributor", "建材进口分销商", "常做规格集采与区域分销，关注 MOQ 与账期"),
    ("contractor", "工程总包/施工方", "关注防火等级、交付周期与现场技术支持"),
    ("epc", "EPC 总包单位", "项目型采购，重视资质案例与分批供货"),
    ("importer", "本地进口商", "关注 HS 编码、清关与到岸价"),
]


def _parse_count(message: str, default: int = 8) -> int:
    """_parse_count。

    参数说明：
    :param message: 参数 message
    :param default: 参数 default
    :return: 返回处理结果。
    """
    m = re.search(r"(\d+)\s*(家|个|封|份|条)", message)
    if m:
        return max(3, min(int(m.group(1)), 30))
    m2 = re.search(r"(\d+)", message)
    if m2:
        return max(3, min(int(m2.group(1)), 30))
    return default


def _parse_region(message: str, memory: dict[str, Any]) -> str:
    """_parse_region。

    参数说明：
    :param message: 参数 message
    :param memory: 参数 memory
    :return: 返回处理结果。
    """
    for region in _REGION_COUNTRIES:
        if region in message:
            return region
    for alias in _COUNTRY_ALIASES:
        if alias in message:
            if alias in ("沙特", "阿联酋"):
                return "中东"
            if alias in ("越南", "泰国", "印尼"):
                return "东南亚"
    prefs = memory.get("preferred_regions") or []
    return prefs[0] if prefs else "中东"


def _parse_language(message: str, memory: dict[str, Any]) -> str:
    """_parse_language。

    参数说明：
    :param message: 参数 message
    :param memory: 参数 memory
    :return: 返回处理结果。
    """
    if re.search(r"英文|english|en\b", message, re.I):
        return "en"
    if re.search(r"双语|中英", message):
        return "bilingual"
    pref = memory.get("letter_language") or "bilingual"
    if pref in ("zh", "en", "bilingual"):
        return pref
    return "bilingual"



def _find_buyer_prospects_via_sidecar(db, tenant_id, region, category, message, sidecar, raw_prospects, prior_insights, feedback_hints):
    """_find_buyer_prospects_via_sidecar。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param region: 参数 region
    :param category: 参数 category
    :param message: 参数 message
    :param sidecar: 参数 sidecar
    :param raw_prospects: 参数 raw_prospects
    :param prior_insights: 参数 prior_insights
    :param feedback_hints: 参数 feedback_hints
    :return: 返回处理结果。
    """
    from app.services.ubrain.domain_email_extractor_sidecar import enrich_prospect_emails
    enriched_prospects, email_meta = enrich_prospect_emails(
        raw_prospects,
        tenant_id=tenant_id,
    )
    if email_meta:
        sidecar = {**sidecar, "email_enrichment": email_meta}
    prospects: list[dict[str, Any]] = []
    for p in enriched_prospects:
        row = BuyerProspectLead(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            region_label=region,
            country_code=(p.get("country_code") or "XX")[:8],
            buyer_type=(p.get("buyer_type") or "importer")[:32],
            title=(p.get("title") or "Sidecar prospect")[:200],
            fit_score=int(p.get("fit_score") or 65),
            suggested_channel=(p.get("suggested_channel") or "email")[:32],
            notes=(
                f"{p.get('notes') or ''} evidence={p.get('evidence_url') or ''}"
                + (
                    f" email_src={p.get('email_source_url')}"
                    if p.get("email_source_url")
                    else ""
                )
            )[:2000],
            status="discovered",
            source_tool=(
                "ai_find_customer_sidecar_stub"
                if sidecar.get("probe_mode") == "stub"
                else "ai_find_customer_sidecar"
            ),
        )
        db.add(row)
        prospects.append(
            {
                "id": row.id,
                "title": row.title,
                "buyer_type": row.buyer_type,
                "country_code": row.country_code,
                "fit_score": row.fit_score,
                "suggested_channel": row.suggested_channel,
                "notes": p.get("notes"),
                "evidence_url": p.get("evidence_url"),
                "email": p.get("email"),
                "email_source_url": p.get("email_source_url"),
                "email_enrichment": p.get("email_enrichment"),
                "confidence": p.get("confidence"),
                "verification_status": "待核实候选",
            }
        )
    db.commit()
    record_tool_use(
        db,
        tenant_id,
        "find_buyers",
        context_patch={
            "preferred_regions": [region],
            "product_category": category,
            "last_find_mode": "ai_find_customer_sidecar",
        },
    )
    return {
        **sidecar,
        "region": region,
        "category": category,
        "count": len(prospects),
        "prospects": prospects,
        "write_back": "buyer_prospect_leads",
        "next_step": "对高 fit 客户生成开发信（outreach_letter_pack），发送前需您确认。",
        "prior_insights": prior_insights,
        "feedback_hints": feedback_hints,
    }
def _find_buyer_prospects_via_archetypes(db, tenant_id, region, category, countries, count, prior_insights):
    """_find_buyer_prospects_via_archetypes。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param region: 参数 region
    :param category: 参数 category
    :param countries: 参数 countries
    :param count: 参数 count
    :param prior_insights: 参数 prior_insights
    :return: 返回处理结果。
    """
    prospects: list[dict[str, Any]] = []
    idx = 0
    while len(prospects) < count:
        btype, title_cn, note = _BUYER_ARCHETYPES[idx % len(_BUYER_ARCHETYPES)]
        cc = countries[idx % len(countries)]
        fit = 55 + (idx % 4) * 8
        if category.startswith("保温"):
            fit += 5
        if prior_insights:
            fit += 3
        note_extra = ""
        if prior_insights and idx == 0:
            note_extra = f" 研究记忆：{prior_insights[0].get('summary', '')[:80]}"
        title = f"{region}·{cc} {title_cn}（{category}画像 #{idx + 1}）"
        row = BuyerProspectLead(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            region_label=region,
            country_code=cc,
            buyer_type=btype,
            title=title[:200],
            fit_score=min(fit, 95),
            suggested_channel="email" if btype != "contractor" else "whatsapp",
            notes=(note + note_extra)[:2000],
            status="discovered",
            source_tool="find_buyers",
        )
        db.add(row)
        prospects.append(
            {
                "id": row.id,
                "title": row.title,
                "buyer_type": btype,
                "country_code": cc,
                "fit_score": row.fit_score,
                "suggested_channel": row.suggested_channel,
                "notes": note,
                "verification_status": "待核实候选",
            }
        )
        idx += 1
    return prospects


def find_buyer_prospects(
    db: Session,
    *,
    tenant_id: str,
    message: str,
    memory: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """按区域/品类生成采购商候选；优先 Sidecar（须 evidence_url），否则 Accio 画像模板。"""
    mem = memory or get_memory(db, tenant_id)
    category = mem.get("product_category") or "建材"
    if "保温" in message:
        category = "保温建材"
    region = _parse_region(message, mem)
    count = _parse_count(message, 8)
    prior_insights = retrieve_insights_for_accio(
        db, tenant_id, region=region, category=category, limit=5
    )
    feedback_hints = mem.get("research_hints") or []
    from app.services.ubrain.ai_find_customer_sidecar import fetch_sidecar_prospects
    sidecar = fetch_sidecar_prospects(
        tenant_id=tenant_id,
        query=message or f"{region} {category} B2B buyer",
        region=region,
        category=category,
        count=count,
    )
    if sidecar and sidecar.get("prospects"):
        return _find_buyer_prospects_via_sidecar(
            db, tenant_id, region, category, message, sidecar,
            sidecar["prospects"], prior_insights, feedback_hints,
        )

    countries = _REGION_COUNTRIES.get(region, ["SA", "AE"])
    if not any(r in message for r in _REGION_COUNTRIES) and not any(
        a in message for a in _COUNTRY_ALIASES
    ):
        bo = blue_ocean(f"{category}蓝海市场")
        for rec in (bo.get("recommendations") or [])[:2]:
            cc = rec.get("country_code")
            if cc and cc not in countries:
                countries.append(cc)

    prospects = _find_buyer_prospects_via_archetypes(
        db, tenant_id, region, category, countries, count, prior_insights
    )
    db.commit()
    record_tool_use(
        db,
        tenant_id,
        "find_buyers",
        context_patch={"preferred_regions": [region], "product_category": category},
    )
    return {
        "mode": "accio_buyer_discovery",
        "region": region,
        "category": category,
        "count": len(prospects),
        "prospects": prospects,
        "human_verify_required": True,
        "disclaimer": "候选为公开 B2B 采购画像模板，非阿里站内实名数据；均为「待核实候选」，联系前请人工核实。",
        "write_back": "buyer_prospect_leads",
        "next_step": "对高 fit 客户生成开发信（outreach_letter_pack），发送前需您确认。",
        "prior_insights": prior_insights,
        "feedback_hints": feedback_hints,
    }


_REGION_LETTER_PROFILES: dict[str, dict[str, str]] = {
    "中东": {
        "hook_zh": "针对中东工程项目与分销渠道",
        "hook_en": "for Middle East project and distribution channels",
        "compliance_zh": "可提供防火等级说明与出口配套文件。",
        "compliance_en": "Fire-rating specs and export documentation available.",
    },
    "东南亚": {
        "hook_zh": "针对东南亚湿热项目配套",
        "hook_en": "for humid-climate projects in Southeast Asia",
        "compliance_zh": "可说明防潮包装与海运防霉方案。",
        "compliance_en": "Moisture-proof packing and sea-freight protection available.",
    },
    "欧美": {
        "hook_zh": "针对欧美合规采购",
        "hook_en": "for EU/US compliant procurement",
        "compliance_zh": "可补充 CE/ASTM 等标准对应说明（以实际证书为准）。",
        "compliance_en": "CE/ASTM alignment notes available upon request.",
    },
}


def _region_letter_profile(region: str) -> dict[str, str]:
    """_region_letter_profile。

    参数说明：
    :param region: 参数 region
    :return: 返回处理结果。
    """
    if region in _REGION_LETTER_PROFILES:
        return _REGION_LETTER_PROFILES[region]
    return {
        "hook_zh": f"针对{region}出口项目",
        "hook_en": f"for {region} export projects",
        "compliance_zh": "可提供规格书与批量报价区间。",
        "compliance_en": "Spec sheets and MOQ pricing available.",
    }


_CATEGORY_LETTER_PROFILES: dict[str, dict[str, str]] = {
    "保温建材": {
        "spec_zh": "厚度/密度/导热系数与防火等级（A1/A2）",
        "spec_en": "thickness, density, lambda value and fire rating (A1/A2)",
        "app_zh": "建筑外墙保温、工业设备保温",
        "app_en": "facade insulation and industrial thermal applications",
    },
    "岩棉": {
        "spec_zh": "容重、防水率、降噪系数与船级/防火认证",
        "spec_en": "density, water repellency, NRC and marine/fire certs",
        "app_zh": "高层建筑防火隔离带、船舶舱室",
        "app_en": "high-rise fire barriers and marine compartments",
    },
    "玻璃棉": {
        "spec_zh": "纤维直径、包覆铝箔、憎水性与施工便捷性",
        "spec_en": "fiber diameter, foil facing, hydrophobicity and ease of install",
        "app_zh": "HVAC 风管、钢结构保温",
        "app_en": "HVAC ducting and steel structure insulation",
    },
    "建材": {
        "spec_zh": "规格参数、批量 MOQ 与出口包装方案",
        "spec_en": "specs, MOQ tiers and export packing",
        "app_zh": "工程项目与分销渠道配套",
        "app_en": "project supply and distribution channels",
    },
}


def _category_letter_profile(category: str) -> dict[str, str]:
    """_category_letter_profile。

    参数说明：
    :param category: 参数 category
    :return: 返回处理结果。
    """
    cat = (category or "建材").strip()
    for key in ("岩棉", "玻璃棉", "保温"):
        if key in cat:
            return _CATEGORY_LETTER_PROFILES.get(
                "岩棉" if key == "岩棉" else "玻璃棉" if key == "玻璃棉" else "保温建材",
                _CATEGORY_LETTER_PROFILES["建材"],
            )
    return _CATEGORY_LETTER_PROFILES["建材"]


def _build_outreach_letters_batch(brand, region_profile, primary, spec_zh, spec_en, app_zh, app_en, belt_note_zh, belt_note_en, sku_hint_zh, sku_hint_en, pool, count, language, site_cta):
    """_build_outreach_letters_batch。

    参数说明：
    :param brand: 参数 brand
    :param region_profile: 参数 region_profile
    :param primary: 参数 primary
    :param spec_zh: 参数 spec_zh
    :param spec_en: 参数 spec_en
    :param app_zh: 参数 app_zh
    :param app_en: 参数 app_en
    :param belt_note_zh: 参数 belt_note_zh
    :param belt_note_en: 参数 belt_note_en
    :param sku_hint_zh: 参数 sku_hint_zh
    :param sku_hint_en: 参数 sku_hint_en
    :param pool: 参数 pool
    :param count: 参数 count
    :param language: 参数 language
    :param site_cta: 参数 site_cta
    :return: 返回处理结果。
    """
    letters: list[dict[str, Any]] = []
    for i in range(count):
        p = pool[i % len(pool)]
        variant = i % 3
        if variant == 0:
            angle_zh = f"分销/集采合作 — {region_profile['hook_zh']}"
            angle_en = f"Distribution & bulk supply {region_profile['hook_en']}"
        elif variant == 1:
            angle_zh = f"工程项目配套 — {region_profile['hook_zh']}"
            angle_en = f"Project supply {region_profile['hook_en']}"
        else:
            angle_zh = f"进口商长期供货 — {region_profile['hook_zh']}"
            angle_en = f"Importer partnership {region_profile['hook_en']}"
        subject_zh = f"{primary} 规格咨询 — {p.get('country_code', 'export')}"
        body_zh = (
            f"您好，\n\n"
            f"我们是{brand}{belt_note_zh}，主营{primary}（{app_zh}）。"
            f"注意到贵司在{p.get('title', region_profile.get('region_zh', '目标市场'))}方向可能有配套需求。\n\n"
            f"可提供的资料：{spec_zh}。"
            f"{sku_hint_zh}"
            f"批量 MOQ 区间与{region_profile['compliance_zh']}\n"
            f"若方便，请回复目标规格与目的港，或访问{site_cta}。\n\n"
            f"此致"
        )
        subject_en = f"{primary} — {angle_en} ({p.get('country_code', 'export')})"
        body_en = (
            f"Hello,\n\n"
            f"We supply {primary}{belt_note_en} for {app_en} {region_profile['hook_en']}.\n"
            f"Key specs: {spec_en}. {sku_hint_en} {region_profile['compliance_en']}\n"
            f"If useful, please reply with target specs and destination port, or visit our {site_cta}.\n\n"
            f"Best regards,\n{brand or 'Export team'}"
        )
        if language == "zh":
            letters.append(
                {"index": i + 1, "prospect_id": p.get("id"), "subject": subject_zh, "body": body_zh}
            )
        elif language == "en":
            letters.append(
                {"index": i + 1, "prospect_id": p.get("id"), "subject": subject_en, "body": body_en}
            )
        else:
            letters.append(
                {
                    "index": i + 1,
                    "prospect_id": p.get("id"),
                    "subject_zh": subject_zh,
                    "subject_en": subject_en,
                    "body_zh": body_zh,
                    "body_en": body_en,
                }
            )
    return letters


def build_outreach_letters(
    *,
    category: str,
    region: str,
    count: int,
    language: str,
    tone: str,
    brand_name: str,
    prospects: list[dict[str, Any]] | None = None,
    site_cta: str = "独立域询盘表单",
    product_profile: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """build_outreach_letters。

    参数说明：
    :param category: 参数 category
    :param region: 参数 region
    :param count: 参数 count
    :param language: 参数 language
    :param tone: 参数 tone
    :param brand_name: 参数 brand_name
    :param prospects: 参数 prospects
    :param site_cta: 参数 site_cta
    :param product_profile: 参数 product_profile
    :return: 返回处理结果。
    """
    brand = brand_name or "Our factory"
    region_profile = _region_letter_profile(region)
    cat_profile = _category_letter_profile(category)
    pp = product_profile or {}
    primary = str(pp.get("primary_product") or category).strip()
    spec_zh = str(pp.get("spec_summary_zh") or cat_profile["spec_zh"]).strip()
    spec_en = str(pp.get("spec_summary_en") or cat_profile["spec_en"]).strip()
    app_zh = str(pp.get("application_summary_zh") or cat_profile["app_zh"]).strip()
    app_en = str(pp.get("export_angle_en") or cat_profile["app_en"]).strip()
    belt = pp.get("industry_belt") if isinstance(pp.get("industry_belt"), dict) else None
    belt_note_zh = ""
    belt_note_en = ""
    if belt:
        belt_note_zh = f"（{belt.get('region_label_zh', '')}）"
        belt_note_en = f" ({belt.get('region_label_en', '')})"
    product_lines = pp.get("products") if isinstance(pp.get("products"), list) else []
    sku_hint_zh = ""
    sku_hint_en = ""
    lib_names = [str(p.get("name") or "") for p in product_lines if p.get("source") == "product_library"][:3]
    if lib_names:
        sku_hint_zh = f"在供 SKU：{'、'.join(lib_names)}。"
        sku_hint_en = f"Active SKUs: {', '.join(lib_names)}."
    pool = prospects or [{"title": f"{region} buyer", "country_code": "XX"}]
    letters = _build_outreach_letters_batch(
        brand, region_profile, primary, spec_zh, spec_en, app_zh, app_en,
        belt_note_zh, belt_note_en, sku_hint_zh, sku_hint_en, pool, count, language, site_cta,
    )
    return letters


def _enrich_outreach_letters(letters, prospects, category, brand, insight_line):
    """_enrich_outreach_letters。

    参数说明：
    :param letters: 参数 letters
    :param prospects: 参数 prospects
    :param category: 参数 category
    :param brand: 参数 brand
    :param insight_line: 参数 insight_line
    :return: 返回处理结果。
    """
    enriched: list[dict[str, Any]] = []
    for i, letter in enumerate(letters):
        cc = (prospects[i % len(prospects)].get("country_code") if prospects else "XX") or "XX"
        row = enrich_letter(
            letter,
            product=category,
            country_code=str(cc),
            company_name=brand,
        )
        if insight_line and i == 0:
            for key in ("body_zh", "body", "body_en"):
                if key in row and row[key]:
                    row[key] = f"{row[key]}\n\n(Prior market note: {insight_line})"
        enriched.append(row)
    return enriched


def outreach_letter_pack(
    db: Session,
    *,
    tenant_id: str,
    message: str,
    memory: dict[str, Any] | None = None,
    prospect_ids: list[str] | None = None,
) -> dict[str, Any]:
    """outreach_letter_pack。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param message: 参数 message
    :param memory: 参数 memory
    :param prospect_ids: 参数 prospect_ids
    :return: 返回处理结果。
    """
    product_profile = require_product_profile_for_outreach(db, tenant_id)
    mem = memory or get_memory(db, tenant_id)
    category = product_profile.get("product_category") or mem.get("product_category") or "建材"
    region = _parse_region(message, mem)
    count = _parse_count(message, 5)
    lang = _parse_language(message, mem)
    tone = mem.get("tone") or "专业、简洁"
    q = db.query(BuyerProspectLead).filter(
        BuyerProspectLead.tenant_id == tenant_id,
        BuyerProspectLead.status == "discovered",
    )
    if prospect_ids:
        q = q.filter(BuyerProspectLead.id.in_(prospect_ids))
    rows = q.order_by(BuyerProspectLead.fit_score.desc()).limit(count).all()
    prospects = [
        {"id": r.id, "title": r.title, "country_code": r.country_code}
        for r in rows
    ]
    if not prospects:
        fb = find_buyer_prospects(db, tenant_id=tenant_id, message=message, memory=mem)
        prospects = fb.get("prospects") or []

    insights = retrieve_insights_for_accio(
        db, tenant_id, region=region, category=category, limit=3
    )
    insight_line = ""
    if insights:
        insight_line = insights[0].get("summary", "")[:120]
    brand = mem.get("company_name") or mem.get("brand_name") or ""
    letters = build_outreach_letters(
        category=category,
        region=region,
        count=count,
        language=lang,
        tone=tone,
        brand_name=brand,
        prospects=prospects,
        site_cta=mem.get("site_cta") or "独立域询盘表单",
        product_profile=product_profile,
    )
    letters = _enrich_outreach_letters(letters, prospects, category, brand, insight_line)
    for i, row in enumerate(rows[: len(letters)]):
        if i < len(letters):
            body = letters[i].get("body") or letters[i].get("body_en") or ""
            row.outreach_draft = body[:4000]
            row.status = "draft_ready"
    db.commit()
    record_tool_use(db, tenant_id, "outreach_letter_pack", context_patch={"letter_language": lang})
    return {
        "mode": "accio_outreach",
        "letter_count": len(letters),
        "language": lang,
        "category_profile": product_profile.get("spec_summary_zh") or _category_letter_profile(category).get("spec_zh"),
        "product_profile": {
            "primary_product": product_profile.get("primary_product"),
            "sources": product_profile.get("sources"),
            "location_hint": product_profile.get("location_hint"),
            "industry_belt_id": (product_profile.get("industry_belt") or {}).get("id"),
            "library_sku_count": sum(
                1 for p in (product_profile.get("products") or []) if p.get("source") == "product_library"
            ),
        },
        "letters": letters,
        "deliverability_summary": pack_deliverability_summary(letters),
        "human_send_required": True,
        "disclaimer": "开发信为审核草稿；送达率取决于 SPF/DKIM/域名预热与收件人质量，禁止未确认自动外发。",
        "write_back": "buyer_prospect_leads.outreach_draft",
        "prior_insights": insights,
    }


def negotiation_draft(message: str, ctx: dict[str, Any], memory: dict[str, Any]) -> dict[str, Any]:
    """多轮谈单话术：报价、反报价、账期、MOQ。"""
    category = memory.get("product_category") or ctx.get("category") or "建材"
    tone = memory.get("tone") or "专业、简洁"
    qty_m = re.search(r"(\d+)\s*(吨|立方|平|平方|柜|柜量|件)", message)
    qty_hint = qty_m.group(0) if qty_m else "您提到的数量"
    price_m = re.search(r"(\d+(?:\.\d+)?)\s*(元|美元|USD|usd|\$)", message)
    price_hint = price_m.group(0) if price_m else "对方报价"
    rounds = [
        {
            "round": 1,
            "scene": "首轮报价回应",
            "zh": (
                f"感谢询价。针对{qty_hint}的{category}，我们建议先确认规格（厚度/防火等级）与目的港，"
                f"再给出 EXW/FOB 区间报价，避免价差误解。"
            ),
            "en": (
                "Thanks for your inquiry. Please confirm specs (thickness/fire rating) and destination port "
                "so we can share EXW/FOB range pricing."
            ),
        },
        {
            "round": 2,
            "scene": "客户压价 / 反报价",
            "zh": (
                f"理解您对价格的关注。在{price_hint}基础上，若量能达到 MOQ 且账期可控，"
                f"我们可优化包装与排产批次；请确认是否接受分批交货。"
            ),
            "en": (
                "We can optimize batch planning and packaging if MOQ and payment terms are acceptable. "
                "Partial shipments can be arranged."
            ),
        },
        {
            "round": 3,
            "scene": "临门一脚 — 确认订单要素",
            "zh": (
                "建议今日确认：规格终版、数量、目的港、贸易条款、定金比例与交期。"
                "确认后 2 小时内出具 PI，并同步物流与质检节点。"
            ),
            "en": (
                "Please confirm final specs, quantity, Incoterm, deposit ratio and ETD. "
                "We will issue PI within 2 hours after confirmation."
            ),
        },
    ]
    return {
        "mode": "accio_negotiation",
        "tone": tone,
        "category": category,
        "rounds": rounds,
        "cost_floor_hint": ctx.get("cost_floor_hint")
        or memory.get("cost_floor_hint")
        or "【内部参考·不对外发送】请在此填写可接受底价/毛利底线，系统不会自动改价。",
        "human_send_required": True,
        "tips": [
            "不自动改价、不自动签约",
            "大额折扣需超管或负责人二次确认",
            f"语气参考：{tone}",
        ],
    }


def list_prospects(
    db: Session,
    tenant_id: str,
    *,
    limit: int = 50,
) -> dict[str, Any]:
    """list_prospects。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param limit: 参数 limit
    :return: 返回处理结果。
    """
    rows = (
        db.query(BuyerProspectLead)
        .filter(BuyerProspectLead.tenant_id == tenant_id)
        .order_by(BuyerProspectLead.created_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "items": [
            {
                "id": r.id,
                "title": r.title,
                "buyer_type": r.buyer_type,
                "country_code": r.country_code,
                "fit_score": r.fit_score,
                "status": r.status,
                "has_draft": bool(r.outreach_draft),
                "verification_status": (
                    "已联系待回复"
                    if r.status in ("contacted", "contact_sent")
                    else "待核实候选"
                ),
            }
            for r in rows
        ],
        "total": len(rows),
    }


def confirm_outreach_send(
    db: Session,
    *,
    tenant_id: str,
    prospect_id: str,
    channel: str,
) -> dict[str, Any]:
    """记录用户确认发送（审计）；实际发信仍由人工在邮箱/IM 完成。"""
    row = (
        db.query(BuyerProspectLead)
        .filter(
            BuyerProspectLead.id == prospect_id,
            BuyerProspectLead.tenant_id == tenant_id,
        )
        .first()
    )
    if not row:
        raise ValueError("prospect_not_found")
    row.status = "contact_sent"
    meta = {"channel": channel, "confirmed": True}
    row.notes = ((row.notes or "") + "\n" + json.dumps(meta, ensure_ascii=False)).strip()[:2000]
    db.commit()
    record_tool_use(db, tenant_id, "confirm_outreach")
    return {"id": row.id, "status": row.status, "channel": channel}
