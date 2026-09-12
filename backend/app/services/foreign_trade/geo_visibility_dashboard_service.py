"""GW-G-GEO-DASH — GEO/AEO 客户可见性看板（对标迈富时效果报告）。"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.content_master import ContentMaster
from app.models.tenant import Tenant
from app.services.foreign_trade.aeo_fact_audit_service import audit_tenant_content_masters


def _safe_settings(tenant: Tenant) -> dict[str, Any]:
    """实现 safe设置 的功能。
    
    :param tenant: 参数 tenant（类型: Tenant）
    :return: 返回 dict[str, Any] 结果
    """
    if not tenant.settings:
        return {}
    try:
        data = json.loads(tenant.settings)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def build_geo_visibility_dashboard(db: Session, *, tenant_id: str) -> dict[str, Any]:
    """实现 构建geovisibilitydashboard 的功能。
    
    :param db: 参数 db（类型: Session）
    :param tenant_id: 参数 tenant_id（类型: str）
    :return: 返回 dict[str, Any] 结果
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id, Tenant.is_active.is_(True)).first()
    if not tenant:
        return {"ok": False, "error_code": "TENANT_NOT_FOUND"}

    settings = _safe_settings(tenant)
    brand = settings.get("brand") if isinstance(settings.get("brand"), dict) else {}
    site_content = brand.get("site_content") if isinstance(brand.get("site_content"), dict) else {}
    masters = (
        db.query(ContentMaster)
        .filter(ContentMaster.tenant_id == tenant_id)
        .order_by(ContentMaster.updated_at.desc())
        .limit(50)
        .all()
    )
    published = sum(1 for m in masters if (m.status or "") in ("published", "scheduled"))
    draft = sum(1 for m in masters if (m.status or "") in ("draft", "review"))
    faq_ready = 0
    pages = site_content.get("pages") if isinstance(site_content.get("pages"), dict) else {}
    home = pages.get("home") if isinstance(pages.get("home"), dict) else {}
    faq = home.get("faq") or home.get("faqs")
    if isinstance(faq, list) and len(faq) >= 3:
        faq_ready = len(faq)

    cms_findings = audit_tenant_content_masters(db, tenant_id=tenant_id, limit=15)
    leak_count = sum(1 for f in cms_findings if f.get("kind") == "brand_leak")
    fact_count = sum(1 for f in cms_findings if f.get("kind") == "unverified_fact_claim")
    aeo_score = max(0, min(100, 100 - leak_count * 8 - fact_count * 5))
    products = site_content.get("products") if isinstance(site_content.get("products"), dict) else {}
    items = products.get("productItems") if isinstance(products.get("productItems"), list) else []
    with_images = sum(
        1
        for it in items
        if isinstance(it, dict) and str(it.get("image") or "").strip() and not str(it.get("image")).startswith("data:")
    )
    citations_stub = {
        "mode": "honest_stub",
        "note": "AI 引文追踪需接 DeerFlow/Headless 探针；当前展示 AEO+内容就绪度",
        "platforms_monitored": ["ChatGPT", "Perplexity", "Gemini", "Claude"],
        "citation_events_30d": None,
    }
    domain = str(tenant.domain or "").strip()
    llms_urls: dict[str, str | None] = {
        "llms_txt": f"/llms.txt?__tenant={domain}" if domain else None,
        "llms_full": f"/llms-full.txt?__tenant={domain}" if domain else None,
        "public_api_llms": f"/api/v1/public/tenants/{domain}/llms.txt" if domain else None,
        "public_api_geo_score": f"/api/v1/public/tenants/{domain}/geo-score" if domain else None,
    }
    return {
        "ok": True,
        "gw_task": "GW-G-GEO-DASH",
        "tenant_id": tenant_id,
        "tenant_domain": tenant.domain,
        "llms_urls": llms_urls,
        "unified_geo_schema": "unified-geo-v1",
        "scores": {
            "aeo_fact_score": aeo_score,
            "content_readiness": min(100, published * 10 + faq_ready * 5 + with_images * 8),
            "geo_productization": min(100, faq_ready * 12 + (20 if with_images >= 3 else 0)),
        },
        "content_stats": {
            "masters_total": len(masters),
            "masters_published": published,
            "masters_draft": draft,
            "faq_entries": faq_ready,
            "products_with_images": with_images,
        },
        "aeo_audit": {
            "brand_leaks": leak_count,
            "unverified_claims": fact_count,
            "findings_sample": cms_findings[:8],
        },
        "citations": citations_stub,
        "benchmark_ref": "marketingforce T-GEO 效果报告",
        "next_actions": [
            "补齐 FAQ 母版 ≥8 条以提升 AI 可引用面",
            "修复 AEO 审计标红的未核实数据表述",
            "配置 Headless 探针后开启 citation_events 实盘",
        ],
    }
