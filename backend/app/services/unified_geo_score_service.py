# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""统一 GEO 评分口径 — unified-geo-v1（合并 AEO / Optimizer / Engine / AI Search）。"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from sqlalchemy.orm import Session

from app.geo_engine.geo_optimizer import GEOOptimizer
from app.models.tenant import Tenant
from app.services.ai_search_probe_service import run_ai_search_probes
from app.services.foreign_trade.geo_visibility_dashboard_service import build_geo_visibility_dashboard
from app.services.geo_engine_service import GEOEngine
from app.services.media_tenant_traffic_service import get_tenant_by_domain
from app.services.tenant_llms_txt_service import extract_tenant_site_plaintext, _safe_settings
from app.services.tenant_product_context import resolve_tenant_product_hint

SCHEMA_VERSION = "unified-geo-v1"


def _calc_product_coverage_score(db: Session) -> float:
    """计算产品 SEO 覆盖度评分（0-100）。

    检查维度：
    - 产品是否有 meta_title
    - 产品是否有 meta_description
    - 产品是否有 image_url（主图）
    - 产品是否有 slug（SEO 友好 URL）
    - 产品是否有 alt_text 图片
    """
    from app.models.product import Product, ProductImage
    products = db.query(Product).filter(Product.is_active.is_(True)).all()
    if not products:
        return 0.0

    total_checks = 0
    passed_checks = 0
    for p in products:
        # 4 项基础 SEO 检查
        checks = [
            bool(p.meta_title),
            bool(p.meta_description),
            bool(p.image_url),
            bool(p.slug),
        ]
        total_checks += len(checks)
        passed_checks += sum(1 for c in checks if c)
        # 图片 alt_text 检查
        has_alt = db.query(ProductImage).filter(
            ProductImage.product_id == str(p.id),
            ProductImage.alt_text.isnot(None),
            ProductImage.alt_text != "",
        ).first()
        total_checks += 1
        if has_alt:
            passed_checks += 1

    return round(passed_checks / total_checks * 100, 1) if total_checks else 0.0


def _keywords_from_tenant(tenant: Tenant) -> list[str]:
    """_keywords_from_tenant。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    settings = _safe_settings(tenant)
    brand = settings.get("brand") if isinstance(settings.get("brand"), dict) else {}
    site_content = brand.get("site_content") if isinstance(brand.get("site_content"), dict) else {}
    pages = site_content.get("pages") if isinstance(site_content.get("pages"), dict) else {}
    home = pages.get("home") if isinstance(pages.get("home"), dict) else {}
    raw = str(home.get("seoKeywords") or "").strip()
    if raw:
        return [k.strip() for k in raw.split(",") if k.strip()][:8]
    hint = resolve_tenant_product_hint(tenant) or tenant.name or "export products"
    return [hint]


async def _run_model_mention_probe(
    db: Session,
    *,
    primary_kw: str,
    brand_name: str,
) -> tuple[float | None, dict[str, Any]]:
    """运行 GEO 引擎模型提及率探针（失败降级）。"""
    detail: dict[str, Any] = {"mode": "skipped", "reason": "probe_disabled"}
    try:
        engine_result = await GEOEngine.check_keyword(
            primary_kw,
            probe_mode="recommend",
            brand_name=str(brand_name),
            product_category=primary_kw,
            db=db,
        )
        summary = engine_result.get("summary") if isinstance(engine_result.get("summary"), dict) else {}
        rate = float(summary.get("indexed_rate") or 0)
        detail = {
            "mode": "geo_engine",
            "probe_mode": "recommend",
            "indexed_rate": rate,
            "models_checked": summary.get("total_models"),
        }
        return rate, detail
    except Exception as exc:
        return None, {"mode": "error", "reason": str(exc)[:200]}


async def _run_ai_search_probes(
    *,
    primary_kw: str,
    brand_name: str,
) -> tuple[float | None, dict[str, Any]]:
    """运行 AI 搜索探针并计算收录率（失败返回跳过）。"""
    detail: dict[str, Any] = {"mode": "skipped"}
    try:
        detail = await run_ai_search_probes(
            keyword=primary_kw,
            brand_name=str(brand_name),
            product_category=primary_kw,
        )
        models = detail.get("models") or []
        configured = [m for m in models if m.get("status") != "not_configured"]
        if not configured:
            return None, detail
        hits = sum(1 for m in configured if m.get("status") == "indexed")
        return round(hits / len(configured) * 100, 1), detail
    except Exception:
        return None, detail


def _compute_geo_weighted_overall(
    *,
    aeo_score: float,
    content_visibility: float,
    content_readiness: float,
    model_mention_rate: float | None,
    ai_search_score: float | None,
    product_coverage_score: float,
) -> float:
    """按权重计算 GEO 综合得分。"""
    weights: list[tuple[float, float | None]] = [
        (0.25, aeo_score),
        (0.20, content_visibility),
        (0.15, content_readiness),
        (0.15, model_mention_rate),
        (0.10, ai_search_score),
        (0.15, product_coverage_score),
    ]
    active = [(w, s) for w, s in weights if s is not None]
    weight_sum = sum(w for w, _ in active) or 1.0
    return round(sum(w * s for w, s in active) / weight_sum, 1)


def _build_geo_result_payload(
    *,
    domain: str,
    tenant_id: str,
    overall: float,
    aeo_score: float,
    content_visibility: float,
    content_readiness: float,
    model_mention_rate: float | None,
    model_mention_detail: dict[str, Any],
    ai_search_score: float | None,
    ai_search_detail: dict[str, Any],
    product_coverage_score: float,
) -> dict[str, Any]:
    """组装 GEO 评分结果负载。"""
    return {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "score_id": "unified-geo-v1",
        "tenant_domain": domain,
        "tenant_id": tenant_id,
        "overall": overall,
        "components": {
            "aeo_readiness": {
                "score": aeo_score,
                "source": "geo_visibility_dashboard.aeo_fact_score",
                "weight": 0.25,
            },
            "content_visibility": {
                "score": content_visibility,
                "source": "geo_optimizer.visibility_score",
                "weight": 0.20,
            },
            "content_readiness": {
                "score": content_readiness,
                "source": "geo_visibility_dashboard.content_readiness",
                "weight": 0.15,
            },
            "model_mention": {
                "score": model_mention_rate,
                "source": "geo_engine.recommend.indexed_rate",
                "weight": 0.15,
                "detail": model_mention_detail,
            },
            "ai_search_probes": {
                "score": ai_search_score,
                "source": "ai_search_probe_service",
                "weight": 0.10,
                "detail": ai_search_detail,
            },
            "external_skill": {
                "score": None,
                "source": "geo-optimizer-skill-cli",
                "mode": "optional",
                "note": "可接 Auriti-Labs/geo-optimizer-skill MCP；未运行时不在 overall 中计分",
            },
            "product_coverage": {
                "score": product_coverage_score,
                "source": "product_seo_coverage",
                "weight": 0.15,
            },
        },
        "provenance": [
            "geo_visibility_dashboard_service",
            "geo_optimizer.GEOOptimizer",
            "geo_engine_service.GEOEngine",
            "ai_search_probe_service",
        ],
        "out_of_scope": [
            "非实盘 ChatGPT 网页搜索榜",
            "未配置 Key 的探针不计为收录",
        ],
    }


async def build_unified_geo_score(
    db: Session,
    *,
    domain: str,
    include_probes: bool = True,
) -> dict[str, Any]:
    """构建统一 GEO 综合评分（AEO/内容可见/就绪度/模型提及/AI搜索/产品覆盖）。"""
    tenant = get_tenant_by_domain(db, domain)
    if not tenant:
        return {"ok": False, "error_code": "TENANT_NOT_FOUND", "schema_version": SCHEMA_VERSION}

    tenant_id = str(tenant.id)
    dash = build_geo_visibility_dashboard(db, tenant_id=tenant_id)
    dash_scores = dash.get("scores") if isinstance(dash.get("scores"), dict) else {}
    aeo_score = float(dash_scores.get("aeo_fact_score") or 0)
    content_readiness = float(dash_scores.get("content_readiness") or 0)
    plaintext = extract_tenant_site_plaintext(tenant, language="en")
    keywords = _keywords_from_tenant(tenant)
    optimizer = GEOOptimizer(db_connection=db)
    geo_opt = await optimizer.analyze_content(plaintext, keywords, context={"domain": domain})
    content_visibility = float(geo_opt.visibility_score)
    brand_name = (
        (_safe_settings(tenant).get("brand") or {}).get("company_name")
        if isinstance(_safe_settings(tenant).get("brand"), dict)
        else None
    ) or tenant.name or domain
    primary_kw = keywords[0] if keywords else brand_name

    model_mention_rate: float | None = None
    model_mention_detail: dict[str, Any] = {"mode": "skipped", "reason": "probe_disabled"}
    if include_probes:
        model_mention_rate, model_mention_detail = await _run_model_mention_probe(
            db, primary_kw=primary_kw, brand_name=str(brand_name)
        )

    ai_search_score: float | None = None
    ai_search_detail: dict[str, Any] = {"mode": "skipped"}
    if include_probes:
        ai_search_score, ai_search_detail = await _run_ai_search_probes(
            primary_kw=primary_kw, brand_name=str(brand_name)
        )

    product_coverage_score = _calc_product_coverage_score(db)
    overall = _compute_geo_weighted_overall(
        aeo_score=aeo_score,
        content_visibility=content_visibility,
        content_readiness=content_readiness,
        model_mention_rate=model_mention_rate,
        ai_search_score=ai_search_score,
        product_coverage_score=product_coverage_score,
    )
    return _build_geo_result_payload(
        domain=domain,
        tenant_id=tenant_id,
        overall=overall,
        aeo_score=aeo_score,
        content_visibility=content_visibility,
        content_readiness=content_readiness,
        model_mention_rate=model_mention_rate,
        model_mention_detail=model_mention_detail,
        ai_search_score=ai_search_score,
        ai_search_detail=ai_search_detail,
        product_coverage_score=product_coverage_score,
    )


def build_unified_geo_score_sync(db: Session, *, domain: str, include_probes: bool = True) -> dict[str, Any]:
    """build_unified_geo_score_sync。

    参数说明：
    :param db: 参数 db
    :param domain: 参数 domain
    :param include_probes: 参数 include_probes
    :return: 返回处理结果。
    """
    return asyncio.run(build_unified_geo_score(db, domain=domain, include_probes=include_probes))
