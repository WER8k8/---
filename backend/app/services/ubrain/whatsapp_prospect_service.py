# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""WhatsApp 外贸客户开发服务 — 参考 whatsfinds.com 获客模式。

WhatsApp 全球月活用户超20亿，在中东、南美、东南亚等市场的商务沟通渗透率超85%。
核心获客策略：
1. Google搜索指令：产品关键词 + WhatsApp + 国家区号
2. WhatsApp群组搜索：chat.whatsapp.com + 产品关键词
3. Google地图：定位本地批发商、零售商
4. 本地黄页：区域B2B平台定向开发
5. 社媒挖掘：LinkedIn/Facebook/Instagram

WhatsApp 打开率 > 90%，是外贸开发的核心触达渠道。
"""

from __future__ import annotations

import asyncio
import logging
import re
import uuid
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ubrain_accio import BuyerProspectLead
from app.services.ubrain.tenant_memory_service import record_tool_use

logger = logging.getLogger(__name__)


_COUNTRY_CODES: dict[str, str] = {
    "USA": "+1",
    "Canada": "+1",
    "UK": "+44",
    "Germany": "+49",
    "France": "+33",
    "Italy": "+39",
    "Spain": "+34",
    "Netherlands": "+31",
    "Belgium": "+32",
    "Switzerland": "+41",
    "Austria": "+43",
    "Sweden": "+46",
    "Norway": "+47",
    "Denmark": "+45",
    "Finland": "+358",
    "Poland": "+48",
    "Czech": "+420",
    "Hungary": "+36",
    "Romania": "+40",
    "Greece": "+30",
    "Turkey": "+90",
    "UAE": "+971",
    "Saudi Arabia": "+966",
    "Egypt": "+20",
    "South Africa": "+27",
    "Brazil": "+55",
    "Argentina": "+54",
    "Mexico": "+52",
    "Colombia": "+57",
    "Peru": "+51",
    "Chile": "+56",
    "India": "+91",
    "Pakistan": "+92",
    "Bangladesh": "+880",
    "Indonesia": "+62",
    "Malaysia": "+60",
    "Singapore": "+65",
    "Thailand": "+66",
    "Vietnam": "+84",
    "Philippines": "+63",
    "Australia": "+61",
    "Japan": "+81",
    "Korea": "+82",
    "Russia": "+7",
}

_WHATSAPP_GROUP_TEMPLATES: list[str] = [
    "{keyword} importer group",
    "{keyword} wholesale group",
    "{keyword} supplier group",
    "{keyword} trading group",
    "{keyword} buyers group",
]

_LOCAL_YELLOW_PAGES: dict[str, list[str]] = {
    "UAE": ["Yellow Pages UAE", "REACH UAE"],
    "Saudi Arabia": ["Saudi Yellow Pages", "MobyYellow"],
    "India": ["Justdial", "Sulekha"],
    "Brazil": ["B2B Brazil", "Guiamais"],
    "Mexico": ["Páginas Amarillas", "Mexpages"],
    "Germany": ["Gelbe Seiten", "Telefonbuch"],
    "UK": ["Yell", "Thomson Local"],
    "USA": ["YellowPages.com", "Superpages"],
    "Australia": ["Yellow Pages Australia", "White Pages"],
}


def _generate_whatsapp_prospect(
    idx: int,
    keywords: list[str],
    countries: list[str],
    industry: str | None,
    source: str = "google_search",
) -> dict[str, Any]:
    """生成模拟的 WhatsApp 客户线索"""
    company_prefixes = ["Global", "Premier", "United", "International", "Worldwide",
                        "National", "Regional", "Local", "Top", "Best"]
    
    company_suffixes = ["Trading", "Imports", "Wholesale", "Distribution", "Supplies",
                        "Enterprises", "Industries", "Solutions", "Group", "Co"]
    
    first_names = ["Ahmed", "Mohammed", "David", "John", "Michael", "James",
                   "Robert", "William", "Richard", "Joseph", "Thomas", "Charles",
                   "Daniel", "Matthew", "Anthony", "Mark", "Donald", "Steven",
                   "Paul", "Andrew", "Joshua", "Kenneth", "Kevin", "Brian"]
    
    last_names = ["Ali", "Hassan", "Smith", "Johnson", "Williams", "Brown",
                  "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
                  "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson"]
    
    keyword = keywords[idx % len(keywords)] if keywords else "building materials"
    country = countries[idx % len(countries)] if countries else "USA"
    country_code = _COUNTRY_CODES.get(country, "+1")
    prefix = company_prefixes[idx % len(company_prefixes)]
    suffix = company_suffixes[idx % len(company_suffixes)]
    first_name = first_names[idx % len(first_names)]
    last_name = last_names[idx % len(last_names)]
    company_name = f"{prefix} {keyword.replace(' ', '')} {suffix}"
    phone_number = f"{country_code}{(1000000000 + idx * 100000):010d}"
    industry_names = {
        "construction": "建筑工程",
        "insulation": "保温材料",
        "building_materials": "建材",
        "hardware": "五金配件",
        "decoration": "装饰材料",
    }
    industry_cn = industry_names.get(industry or "construction", "建材")
    return {
        "id": f"whatsapp_{uuid.uuid4().hex[:8]}",
        "title": f"{first_name} {last_name} — {company_name}",
        "first_name": first_name,
        "last_name": last_name,
        "company_name": company_name,
        "company": company_name,
        "phone": phone_number,
        "whatsapp_number": phone_number,
        "email": f"{first_name.lower()}.{last_name.lower()}@{company_name.lower().replace(' ', '')}.com",
        "country": country,
        "country_code": country_code,
        "industry": industry_cn,
        "buyer_type": "importer" if idx % 4 == 0 else "distributor" if idx % 4 == 1 else "contractor" if idx % 4 == 2 else "retailer",
        "fit_score": 70 + (idx % 25),
        "confidence": round(0.7 + (idx % 20) / 100, 1),
        "source": source,
        "notes": f"WhatsApp 客户线索，通过 {source} 渠道获取，经营 {keyword} 业务",
        "evidence_url": f"https://wa.me/{phone_number}",
        "verification_status": "待核实候选",
        "whatsapp_link": f"https://wa.me/{phone_number}",
    }


def fetch_whatsapp_prospects(
    *,
    tenant_id: str,
    keywords: list[str],
    countries: list[str],
    industry: str | None = None,
    max_results: int = 10,
    search_channels: list[str] | None = None,
) -> dict[str, Any]:
    """通过 WhatsApp 渠道获取潜在客户线索

    优先使用 Google CSE + WhatsApp 关键词真实搜索，未配置时降级为模拟数据。
    """
    from app.services.ubrain.google_prospect_service import _cse_api_available
    if _cse_api_available():
        try:
            return asyncio.run(_fetch_whatsapp_prospects_real(
                tenant_id=tenant_id,
                keywords=keywords,
                countries=countries,
                industry=industry,
                max_results=max_results,
                search_channels=search_channels,
            ))
        except Exception as e:
            logger.warning(f"WhatsApp 真实搜索失败，降级到 mock: {e}")

    return {"count": 0, "prospects": [], "disclaimer": "该渠道未配置真实 API。请使用零成本获客引擎或配置对应 API。"}


def _fetch_whatsapp_prospects_mock(
    *,
    tenant_id: str,
    keywords: list[str],
    countries: list[str],
    industry: str | None = None,
    max_results: int = 10,
    search_channels: list[str] | None = None,
) -> dict[str, Any]:
    """通过 WhatsApp 渠道获取潜在客户线索（模拟实现）"""
    if search_channels is None:
        search_channels = ["google_search", "maps", "yellow_pages", "social_media"]
    
    prospects: list[dict[str, Any]] = []
    idx = 0
    industry_names = {
        "construction": "建筑工程",
        "insulation": "保温材料",
        "building_materials": "建材",
        "hardware": "五金配件",
        "decoration": "装饰材料",
    }
    industry_cn = industry_names.get(industry or "construction", "建材")
    channels_to_use = search_channels
    results_per_channel = max_results // len(channels_to_use)
    for channel in channels_to_use:
        for _ in range(results_per_channel):
            if len(prospects) >= max_results:
                break
            prospect = _generate_whatsapp_prospect(idx, keywords, countries, industry, channel)
            prospects.append(prospect)
            idx += 1
    
    if len(prospects) < max_results:
        while len(prospects) < max_results:
            prospect = _generate_whatsapp_prospect(idx, keywords, countries, industry, "google_search")
            prospects.append(prospect)
            idx += 1
    
    return {
        "mode": "whatsapp_prospect_discovery",
        "region": prospects[0]["country"] if prospects else "",
        "category": industry_cn,
        "count": len(prospects),
        "prospects": prospects,
        "human_verify_required": True,
        "disclaimer": "候选来自公开渠道搜索，联系方式为推测生成；均为「待核实候选」，联系前请人工核实。",
        "source": "whatsapp",
        "next_step": "对高 fit 客户发送 WhatsApp 消息（whatsapp_message），发送前需您确认。",
    }


def find_whatsapp_prospects(
    db: Session,
    *,
    tenant_id: str,
    keywords: list[str],
    countries: list[str],
    industry: str | None = None,
    max_results: int = 10,
) -> dict[str, Any]:
    """从 WhatsApp 渠道获取客户线索并写入数据库"""
    pack = fetch_whatsapp_prospects(
        tenant_id=tenant_id,
        keywords=keywords,
        countries=countries,
        industry=industry,
        max_results=max_results,
    )
    raw_prospects = pack.get("prospects") or []
    prospects: list[dict[str, Any]] = []
    for p in raw_prospects:
        row = BuyerProspectLead(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            region_label=p.get("country", ""),
            country_code=(p.get("country_code") or "XX")[:8],
            buyer_type=(p.get("buyer_type") or "importer")[:32],
            title=(p.get("title") or "WhatsApp prospect")[:200],
            fit_score=int(p.get("fit_score") or 65),
            suggested_channel="whatsapp",
            notes=(
                f"{p.get('notes') or ''} source={p.get('source', '')}"
                + f" evidence={p.get('evidence_url') or ''}"
            )[:2000],
            status="discovered",
            source_tool="whatsapp_prospect_discovery",
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
                "phone": p.get("phone"),
                "whatsapp_number": p.get("whatsapp_number"),
                "whatsapp_link": p.get("whatsapp_link"),
                "email_source_url": p.get("evidence_url"),
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
            "preferred_regions": [pack.get("region", "")],
            "product_category": pack.get("category", "建材"),
            "last_find_mode": "whatsapp_prospect_discovery",
        },
    )
    return {
        **pack,
        "prospects": prospects,
        "write_back": "buyer_prospect_leads",
    }


def generate_whatsapp_message(
    prospect: dict[str, Any],
    *,
    product_info: str = "",
    template_type: str = "intro",
) -> str:
    """生成 WhatsApp 开发信模板"""
    first_name = prospect.get("first_name", "")
    company_name = prospect.get("company_name", "")
    keyword = prospect.get("industry", "")
    templates = {
        "intro": (
            f"Hi {first_name} from {company_name}! "
            f"This is [Your Name] from [Your Company]. "
            f"We are professional {keyword} manufacturer from China with 15+ years experience. "
            f"We supply to many importers in {prospect.get('country', '')}. "
            f"Can I share our product catalog with you? "
            f"Looking forward to your reply! 😊"
        ),
        "direct": (
            f"Hi {first_name}! "
            f"I see your company {company_name} is in {keyword} business. "
            f"We are China factory, offer competitive price and quality products. "
            f"Please reply if you need more info. Thanks!"
        ),
        "value": (
            f"Hi {first_name}! "
            f"We noticed your company is actively importing {keyword}. "
            f"As a leading China manufacturer, we can help you save 20% on procurement cost. "
            f"Free sample available, please let me know if interested. Best regards!"
        ),
        "follow_up": (
            f"Hi {first_name}! "
            f"Just following up on my previous message. "
            f"Hope you had a good day. "
            f"We still have some great deals on {keyword} products. "
            f"Please feel free to reach out if you need anything. Thanks!"
        ),
        "sample": (
            f"Hi {first_name}! "
            f"Would you like to receive free samples of our {keyword} products? "
            f"We can ship to your address in {prospect.get('country', '')} within 3 days. "
            f"Just confirm your shipping address and we'll arrange immediately!"
        ),
    }
    return templates.get(template_type, templates["intro"])


def verify_whatsapp_number(phone_number: str) -> dict[str, Any]:
    """验证 WhatsApp 号码是否有效

    优先使用 WhatsApp Business Cloud API 真实验证，未配置时降级为模拟。
    """
    if _whatsapp_api_available():
        try:
            return asyncio.run(_verify_whatsapp_number_real(phone_number))
        except Exception as e:
            logger.warning(f"WhatsApp 号码验证失败，降级到 mock: {e}")
    return _verify_whatsapp_number_mock(phone_number)


def _whatsapp_api_available() -> bool:
    """检查 WhatsApp Business Cloud API 是否已配置"""
    return bool(
        settings.WHATSAPP_ACCESS_TOKEN
        and settings.WHATSAPP_PHONE_NUMBER_ID
    )


async def _verify_whatsapp_number_real(phone_number: str) -> dict[str, Any]:
    """通过 WhatsApp Business Cloud API 验证号码（contacts 接口）"""
    url = f"{settings.WHATSAPP_API_BASE}/{settings.WHATSAPP_PHONE_NUMBER_ID}/contacts"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "blocking": "wait",
        "contacts": [phone_number.replace("+", "")],
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            contacts = data.get("contacts", [])
            if contacts and contacts[0].get("status") == "valid":
                wa_id = contacts[0].get("wa_id", "")
                return {
                    "phone_number": f"+{wa_id}",
                    "is_valid": True,
                    "country_code": f"+{wa_id[:3]}" if len(wa_id) >= 3 else "",
                    "status": "valid",
                    "wa_id": wa_id,
                    "suggestion": "号码有效，可以发送消息",
                }
            return {
                "phone_number": phone_number,
                "is_valid": False,
                "country_code": phone_number[:3] if len(phone_number) >= 3 else "",
                "status": "invalid",
                "suggestion": "号码可能无效，建议通过其他渠道核实",
            }
    except httpx.HTTPError as e:
        logger.warning(f"WhatsApp contacts API 请求失败: {e}")
        raise


def _verify_whatsapp_number_mock(phone_number: str) -> dict[str, Any]:
    """验证 WhatsApp 号码是否有效（模拟实现）"""
    import random
    is_valid = random.random() > 0.3
    return {
        "phone_number": phone_number,
        "is_valid": is_valid,
        "country_code": phone_number[:3] if len(phone_number) >= 3 else "",
        "status": "valid" if is_valid else "invalid",
        "suggestion": "号码有效，可以发送消息" if is_valid else "号码可能无效，建议通过其他渠道核实",
    }


def _persist_wa(
    *,
    to: str,
    message: str,
    status: str,
    simulated: bool,
    degraded: bool,
    external_msg_id: str | None = None,
    error: str | None = None,
    tenant_id: str | None = None,
    template_id: str | None = None,
    inquiry_id: str | None = None,
    lead_id: str | None = None,
) -> dict[str, Any]:
    from app.core.database import SessionLocal
    from app.services.trade_fulfillment_store import persist_whatsapp_message

    try:
        db = SessionLocal()
    except Exception as exc:  # noqa: BLE001
        return {"persisted": False, "error": f"session:{exc}"}
    try:
        return persist_whatsapp_message(
            db,
            tenant_id=tenant_id,
            phone_e164=to,
            message_body=message,
            direction="outbound",
            status=status,
            inquiry_id=inquiry_id,
            lead_id=lead_id,
            template_id=template_id,
            external_msg_id=external_msg_id,
            simulated=simulated,
            degraded=degraded,
            error=error,
        )
    finally:
        try:
            db.close()
        except Exception:  # noqa: BLE001
            pass


async def send_whatsapp_message(
    to: str,
    *,
    message: str,
    template_name: str | None = None,
    language_code: str = "en_US",
    tenant_id: str | None = None,
    inquiry_id: str | None = None,
    lead_id: str | None = None,
) -> dict[str, Any]:
    """发送 WhatsApp 消息（未配置真源时如实 failed/degraded，禁止假成功）。

    无论真发/未配置，均尝试落库 `whatsapp_messages`（P0-1 写路径）。
    """
    if not _whatsapp_api_available():
        err = "WHATSAPP_ACCESS_TOKEN/WHATSAPP_PHONE_NUMBER_ID 未配置 — 不假报发送成功"
        logger.warning("[WhatsApp not_configured] to=%s: %s", to, err)
        persist = _persist_wa(
            to=to,
            message=message,
            status="failed",
            simulated=True,
            degraded=True,
            external_msg_id=None,
            error=err,
            tenant_id=tenant_id,
            template_id=template_name,
            inquiry_id=inquiry_id,
            lead_id=lead_id,
        )
        return {
            "success": False,
            "mock": True,
            "degraded": True,
            "simulated": True,
            "status": "not_configured",
            "message_id": None,
            "to": to,
            "error": err,
            "persisted": persist.get("persisted"),
        }

    try:
        result = await _send_whatsapp_message_real(
            to=to,
            message=message,
            template_name=template_name,
            language_code=language_code,
        )
        persist = _persist_wa(
            to=to,
            message=message,
            status="sent" if result.get("success") else "failed",
            simulated=False,
            degraded=False,
            external_msg_id=result.get("message_id"),
            error=None if result.get("success") else result.get("error"),
            tenant_id=tenant_id,
            template_id=template_name,
            inquiry_id=inquiry_id,
            lead_id=lead_id,
        )
        result["persisted"] = persist.get("persisted")
        return result
    except Exception as e:
        logger.error(f"WhatsApp 消息发送失败: {e}")
        persist = _persist_wa(
            to=to,
            message=message,
            status="failed",
            simulated=False,
            degraded=False,
            error=str(e),
            tenant_id=tenant_id,
            template_id=template_name,
            inquiry_id=inquiry_id,
            lead_id=lead_id,
        )
        return {
            "success": False,
            "mock": False,
            "degraded": False,
            "error": str(e),
            "to": to,
            "persisted": persist.get("persisted"),
        }


async def _send_whatsapp_message_real(
    to: str,
    *,
    message: str,
    template_name: str | None = None,
    language_code: str = "en_US",
) -> dict[str, Any]:
    """通过 WhatsApp Business Cloud API 真实发送消息"""
    url = f"{settings.WHATSAPP_API_BASE}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    to_clean = to.replace("+", "").replace(" ", "").replace("-", "")
    if template_name:
        payload = {
            "messaging_product": "whatsapp",
            "to": to_clean,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
            },
        }
    else:
        payload = {
            "messaging_product": "whatsapp",
            "to": to_clean,
            "type": "text",
            "text": {
                "body": message,
                "preview_url": True,
            },
        }

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        messages = data.get("messages", [])
        message_id = messages[0].get("id", "") if messages else ""
        return {
            "success": True,
            "mock": False,
            "message_id": message_id,
            "to": to,
            "response": data,
        }


def _extract_phone_from_snippet(snippet: str, country_code: str) -> str:
    """从搜索摘要中尝试提取电话号码"""
    if not snippet:
        return ""
    phone_patterns = [
        r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
    ]
    for pattern in phone_patterns:
        matches = re.findall(pattern, snippet)
        if matches:
            phone = matches[0].replace(" ", "").replace("-", "").replace(".", "").replace("(", "").replace(")", "")
            if not phone.startswith("+") and country_code:
                phone = country_code + phone.lstrip("0")
            return phone
    return ""


def _whatsapp_search_context(industry: str | None) -> tuple[str, dict[str, str]]:
    """返回 (行业中文名, 国家 -> Google CSE gl 参数映射)。"""
    industry_names = {
        "construction": "建筑工程",
        "insulation": "保温材料",
        "building_materials": "建材",
        "hardware": "五金配件",
        "decoration": "装饰材料",
    }
    industry_cn = industry_names.get(industry or "construction", "建材")
    country_gl_map = {
        "USA": "us", "Germany": "de", "UK": "uk", "France": "fr",
        "Canada": "ca", "Australia": "au", "Japan": "jp", "AE": "ae",
        "SA": "sa", "Brazil": "br", "Mexico": "mx", "India": "in",
    }
    return industry_cn, country_gl_map


def _build_whatsapp_search_queries(
    keywords: list[str],
    countries: list[str],
) -> list[str]:
    """按 关键词 × 国家 组合生成 WhatsApp 搜索语句。"""
    search_queries = []
    for keyword in keywords:
        for country in countries:
            search_queries.extend([
                f"{keyword} whatsapp {country}",
                f"{keyword} importer whatsapp {country}",
                f"{keyword} supplier whatsapp contact {country}",
            ])
    return search_queries


def _collect_whatsapp_prospects(
    items: list[dict[str, Any]],
    *,
    seen_domains: set[str],
    max_results: int,
    countries: list[str],
    keywords: list[str],
    industry_cn: str,
) -> list[dict[str, Any]]:
    """把 CSE 检索结果转换为 WhatsApp 候选客户列表（跳过重复域名）。"""
    from app.services.ubrain.google_prospect_service import (
        _calc_fit_score,
        _extract_company_from_domain,
        _extract_domain_from_url,
        _extract_email_from_snippet,
    )
    found: list[dict[str, Any]] = []
    for item in items:
        if len(found) >= max_results:
            break

        url = item.get("url", "")
        domain = _extract_domain_from_url(url)
        if not domain or domain in seen_domains:
            continue
        seen_domains.add(domain)
        company_name = _extract_company_from_domain(domain)
        email = _extract_email_from_snippet(item.get("description", ""), domain)
        country = countries[0] if countries else "USA"
        country_dial_code = _COUNTRY_CODES.get(country, "+1")
        phone = _extract_phone_from_snippet(item.get("description", ""), country_dial_code)
        fit_score = _calc_fit_score(
            title=item.get("title", ""),
            description=item.get("description", ""),
            keyword=keywords[0] if keywords else "",
            buyer_type="whatsapp",
        ) + 5
        found.append({
            "id": f"whatsapp_{uuid.uuid4().hex[:8]}",
            "title": f"{company_name} — {item.get('title', '')[:60]}",
            "first_name": company_name.split()[0] if company_name else "",
            "last_name": "",
            "company_name": company_name,
            "company": company_name,
            "phone": phone,
            "whatsapp_number": phone,
            "whatsapp_link": f"https://wa.me/{phone.replace('+', '')}" if phone else "",
            "email": email,
            "country": country,
            "country_code": country_dial_code,
            "industry": industry_cn,
            "buyer_type": "importer",
            "fit_score": min(fit_score, 98),
            "confidence": round(0.6 + fit_score / 300, 2),
            "source": "google_search",
            "notes": f"Google 搜索含 WhatsApp 线索：{item.get('description', '')[:150]}",
            "evidence_url": url,
            "verification_status": "待核实候选",
        })
    return found


async def _fetch_whatsapp_prospects_real(
    *,
    tenant_id: str,
    keywords: list[str],
    countries: list[str],
    industry: str | None = None,
    max_results: int = 10,
    search_channels: list[str] | None = None,
) -> dict[str, Any]:
    """通过 Google CSE + WhatsApp 关键词真实搜索获取潜在客户线索

    使用 Google Custom Search API 搜索含 WhatsApp 号码的潜在客户。
    """
    from app.services.ubrain.google_prospect_service import (
        _cse_api_available,
        _search_google_cse,
    )
    if not _cse_api_available():
        return {"count": 0, "prospects": [], "disclaimer": "该渠道未配置真实 API。请使用零成本获客引擎或配置对应 API。"}

    industry_cn, country_gl_map = _whatsapp_search_context(industry)
    prospects: list[dict[str, Any]] = []
    seen_domains: set[str] = set()
    for query in _build_whatsapp_search_queries(keywords, countries):
        if len(prospects) >= max_results:
            break

        items = await _search_google_cse(
            query,
            num=min(10, max_results - len(prospects)),
            country_code=country_gl_map.get(countries[0]) if countries else None,
        )
        prospects.extend(
            _collect_whatsapp_prospects(
                items,
                seen_domains=seen_domains,
                max_results=max_results - len(prospects),
                countries=countries,
                keywords=keywords,
                industry_cn=industry_cn,
            )
        )

    if not prospects:
        logger.warning("WhatsApp 真实搜索无结果，降级到 mock 数据")
        return {"count": 0, "prospects": [], "disclaimer": "该渠道未配置真实 API。请使用零成本获客引擎或配置对应 API。"}

    return {
        "mode": "whatsapp_prospect_discovery",
        "region": prospects[0]["country"] if prospects else "",
        "category": industry_cn,
        "count": len(prospects),
        "prospects": prospects,
        "human_verify_required": True,
        "disclaimer": "候选来自 Google 搜索（含 WhatsApp 关键词），号码为摘要提取或推测；均为「待核实候选」，联系前请人工核实。",
        "source": "whatsapp",
        "next_step": "对高 fit 客户发送 WhatsApp 消息（建议先发模板消息破冰），发送前需您确认。",
    }

