# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""租户产品画像 — 产品库优先 · 产业带 · 可选联网调研（开发信/建站共用）。"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.no_fake_delivery import NotConfiguredError
from app.models.product import Product
from app.models.tenant import Tenant
from app.services.tenant_product_context import resolve_tenant_product_hint

_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "industry_belt_hebei_insulation.json"


class ProductProfileRequiredError(NotConfiguredError):
    """无产品库/主营产品/调研结果，禁止生成开发信或建站文案。"""


def _safe_settings(raw: str | None) -> dict[str, Any]:
    """_safe_settings。

    参数说明：
    :param raw: 参数 raw
    :return: 返回处理结果。
    """
    if not raw:
        return {}
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def _load_belts() -> list[dict[str, Any]]:
    """_load_belts。
    :return: 返回处理结果。
    """
    if not _DATA_PATH.is_file():
        return []
    try:
        payload = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    belts = payload.get("belts")
    return belts if isinstance(belts, list) else []


def match_industry_belt(location_hint: str | None) -> dict[str, Any] | None:
    """match_industry_belt。

    参数说明：
    :param location_hint: 参数 location_hint
    :return: 返回处理结果。
    """
    text = (location_hint or "").strip().lower()
    if not text:
        return None
    for belt in _load_belts():
        tokens = belt.get("match_tokens") or []
        if any(str(t).lower() in text for t in tokens):
            return belt
    return None


def _product_row_dict(row: Product) -> dict[str, Any]:
    """_product_row_dict。

    参数说明：
    :param row: 参数 row
    :return: 返回处理结果。
    """
    specs: list[str] = []
    if row.thermal_conductivity:
        specs.append(f"导热系数 {row.thermal_conductivity}")
    if row.fire_rating:
        specs.append(f"防火 {row.fire_rating}")
    if row.density:
        specs.append(f"密度 {row.density}")
    if row.technical_params:
        specs.append(str(row.technical_params).strip()[:400])
    return {
        "id": str(row.id),
        "name": row.name,
        "subtitle": (row.subtitle or "")[:200],
        "description": (row.description or "")[:600],
        "technical_params": (row.technical_params or "")[:800],
        "application_scenarios": (row.application_scenarios or "")[:400],
        "advantages": (row.advantages or "")[:400],
        "spec_summary": "；".join(specs)[:500],
        "fire_rating": row.fire_rating or "",
        "source": "product_library",
    }


def _match_products_from_library(db: Session, product_hint: str, *, limit: int = 8) -> list[dict[str, Any]]:
    """_match_products_from_library。

    参数说明：
    :param db: 参数 db
    :param product_hint: 参数 product_hint
    :param limit: 参数 limit
    :return: 返回处理结果。
    """
    hint = (product_hint or "").strip()
    if not hint:
        return []
    q = db.query(Product).filter(Product.is_active.is_(True))
    # 关键词拆分：优先精确名，再模糊
    tokens = [t for t in re.split(r"[\s,，、/]+", hint) if len(t) >= 2]
    rows: list[Product] = []
    if tokens:
        for tok in tokens[:4]:
            part = (
                q.filter(Product.name.ilike(f"%{tok}%"))
                .order_by(Product.sort_order.asc(), Product.name.asc())
                .limit(limit)
                .all()
            )
            for r in part:
                if r not in rows:
                    rows.append(r)
    if not rows:
        rows = q.order_by(Product.sort_order.asc()).limit(limit).all()
    return [_product_row_dict(r) for r in rows[:limit]]


def _web_research_snippets(product_hint: str, location_hint: str | None) -> list[dict[str, str]]:
    """可选 AnySearch — 失败时不阻断，仅无 snippets。"""
    try:
        from app.services.hermes.anysearch_probe_service import run_anysearch
    except ImportError:
        return []
    loc = (location_hint or "河北廊坊").strip()
    query = f"{product_hint} {loc} 保温建材 厂家 规格 出口"
    result = run_anysearch(query, max_results=3, timeout_sec=45)
    if not result.get("ok"):
        return []
    hits = result.get("hits") or []
    return [
        {"title": h.get("title", "")[:200], "url": h.get("url", "")[:500], "snippet": h.get("snippet", "")[:400]}
        for h in hits
        if isinstance(h, dict)
    ]


def build_product_profile(
    db: Session,
    tenant: Tenant | None,
    *,
    product_hint: str | None = None,
    location_hint: str | None = None,
    run_web_research: bool = False,
) -> dict[str, Any]:
    """汇总：产品库 → 租户主营 → 产业带 → 可选外网调研。"""
    settings = _safe_settings(tenant.settings if tenant else None)
    onboarding = settings.get("onboarding") if isinstance(settings.get("onboarding"), dict) else {}
    brand = settings.get("brand") if isinstance(settings.get("brand"), dict) else {}
    hint = (product_hint or "").strip()
    if not hint and tenant:
        hint = resolve_tenant_product_hint(tenant) or ""
    if not hint:
        site = brand.get("site_content") if isinstance(brand.get("site_content"), dict) else {}
        pages = site.get("pages") if isinstance(site.get("pages"), dict) else {}
        home = pages.get("home") if isinstance(pages.get("home"), dict) else {}
        hint = str(home.get("title") or brand.get("site_title") or "").strip()

    loc = (location_hint or onboarding.get("location_hint") or onboarding.get("origin_region") or "").strip()
    belt = match_industry_belt(loc)
    library_products = _match_products_from_library(db, hint) if hint else []
    if not library_products and belt:
        # 产业带典型 SKU 作为候选（仍须用户确认/入库）
        library_products = [
            {
                "id": f"belt:{belt.get('id')}:{name}",
                "name": name,
                "spec_summary": belt.get("spec_focus_zh", ""),
                "application_scenarios": belt.get("export_angle_zh", ""),
                "source": "industry_belt_typical",
            }
            for name in (belt.get("typical_products") or [])[:6]
            if isinstance(name, str)
        ]

    primary = hint
    if library_products and library_products[0].get("source") == "product_library":
        primary = library_products[0].get("name") or hint

    spec_lines: list[str] = []
    app_lines: list[str] = []
    for p in library_products[:3]:
        if p.get("spec_summary"):
            spec_lines.append(f"{p.get('name')}: {p['spec_summary']}")
        elif p.get("technical_params"):
            spec_lines.append(f"{p.get('name')}: {p['technical_params'][:120]}")
        if p.get("application_scenarios"):
            app_lines.append(str(p["application_scenarios"])[:160])

    web_snippets = _web_research_snippets(primary, loc) if run_web_research and primary else []
    profile: dict[str, Any] = {
        "primary_product": primary,
        "product_category": _infer_category(primary, library_products),
        "location_hint": loc,
        "industry_belt": belt,
        "industry_belt_catalog_status": (belt or {}).get("catalog_status"),
        "product_categories": (belt or {}).get("product_categories"),
        "accessory_products": _belt_accessory_names(belt),
        "products": library_products,
        "spec_summary_zh": "；".join(spec_lines)[:800] or (belt or {}).get("spec_focus_zh", ""),
        "application_summary_zh": "；".join(app_lines)[:600] or (belt or {}).get("export_angle_zh", ""),
        "spec_summary_en": (belt or {}).get("spec_focus_en", ""),
        "export_angle_en": (belt or {}).get("export_angle_en", ""),
        "web_research": web_snippets,
        "sources": _collect_sources(library_products, belt, web_snippets),
        "ready_for_outreach": bool(primary and (library_products or hint)),
    }
    return profile


def _belt_accessory_names(belt: dict[str, Any] | None) -> list[str]:
    """_belt_accessory_names。

    参数说明：
    :param belt: 参数 belt
    :return: 返回处理结果。
    """
    if not belt:
        return []
    cats = belt.get("product_categories")
    if not isinstance(cats, dict):
        return []
    names: list[str] = []
    for key in (
        "accessories",
        "finish_accessories",
        "fixing_accessories",
        "mortar_adhesive",
        "seal_gasket",
        "pipe_building",
        "civil_ancillary",
    ):
        for item in cats.get(key) or []:
            if isinstance(item, str) and item.strip():
                names.append(item.strip())
    return names[:20]


def _infer_category(primary: str, products: list[dict[str, Any]]) -> str:
    """_infer_category。

    参数说明：
    :param primary: 参数 primary
    :param products: 参数 products
    :return: 返回处理结果。
    """
    text = primary
    for p in products[:2]:
        text += " " + str(p.get("name") or "")
    if "岩棉" in text:
        return "岩棉"
    if "玻璃棉" in text:
        return "玻璃棉"
    if "橡塑" in text:
        return "橡塑保温"
    if "聚氨酯" in text or "PIR" in text.upper():
        return "聚氨酯保温"
    if "挤塑" in text or "XPS" in text.upper():
        return "挤塑板"
    if "酚醛" in text:
        return "酚醛保温"
    if "密封" in text or "垫片" in text or "法兰" in text:
        return "密封橡胶配套"
    if "净化板" in text or "夹芯板" in text:
        return "板材系统"
    if "防火涂料" in text or "钢结构" in text:
        return "钢结构防火涂料"
    if "防腐" in text:
        return "防腐涂料"
    if "网格布" in text or "保温钉" in text or "砂浆" in text:
        return "保温辅材"
    if "保温" in text or "隔热" in text:
        return "保温建材"
    return primary or "建材"


def _collect_sources(
    products: list[dict[str, Any]],
    belt: dict[str, Any] | None,
    web: list[dict[str, str]],
) -> list[str]:
    """_collect_sources。

    参数说明：
    :param products: 参数 products
    :param belt: 参数 belt
    :param web: 参数 web
    :return: 返回处理结果。
    """
    out: list[str] = []
    if any(p.get("source") == "product_library" for p in products):
        out.append("product_library")
    if belt:
        out.append("industry_belt")
    if web:
        out.append("web_research")
    if not out and products:
        out.append("product_hint")
    return out


def persist_product_profile(db: Session, tenant: Tenant, profile: dict[str, Any]) -> dict[str, Any]:
    """persist_product_profile。

    参数说明：
    :param db: 参数 db
    :param tenant: 参数 tenant
    :param profile: 参数 profile
    :return: 返回处理结果。
    """
    settings = _safe_settings(tenant.settings)
    onboarding = settings.get("onboarding") if isinstance(settings.get("onboarding"), dict) else {}
    onboarding["product_profile"] = profile
    primary = str(profile.get("primary_product") or "").strip()
    if primary:
        onboarding["primary_product"] = primary
    if profile.get("location_hint"):
        onboarding["location_hint"] = profile["location_hint"]
    settings["onboarding"] = onboarding
    tenant.settings = json.dumps(settings, ensure_ascii=False)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return profile


def build_and_persist_product_profile(
    db: Session,
    tenant: Tenant,
    *,
    product_hint: str | None = None,
    location_hint: str | None = None,
    run_web_research: bool = False,
) -> dict[str, Any]:
    """build_and_persist_product_profile。

    参数说明：
    :param db: 参数 db
    :param tenant: 参数 tenant
    :param product_hint: 参数 product_hint
    :param location_hint: 参数 location_hint
    :param run_web_research: 参数 run_web_research
    :return: 返回处理结果。
    """
    profile = build_product_profile(
        db,
        tenant,
        product_hint=product_hint,
        location_hint=location_hint,
        run_web_research=run_web_research,
    )
    return persist_product_profile(db, tenant, profile)


def get_tenant_product_profile(db: Session, tenant_id: str) -> dict[str, Any]:
    """get_tenant_product_profile。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return {"ready_for_outreach": False, "products": []}
    settings = _safe_settings(tenant.settings)
    onboarding = settings.get("onboarding") if isinstance(settings.get("onboarding"), dict) else {}
    cached = onboarding.get("product_profile")
    if isinstance(cached, dict) and cached.get("primary_product"):
        return cached
    return build_product_profile(db, tenant, run_web_research=False)


def require_product_profile_for_outreach(db: Session, tenant_id: str) -> dict[str, Any]:
    """require_product_profile_for_outreach。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    profile = get_tenant_product_profile(db, tenant_id)
    if profile.get("ready_for_outreach"):
        return profile
    raise ProductProfileRequiredError(
        "PRODUCT_PROFILE_REQUIRED",
        "请先填写主营产品、录入产品库，或在建站时完成产品与产地调研；"
        "开发信必须基于真实产品规格，不能按默认「建材」模板生成。",
    )


def require_product_profile_for_content(db: Session, tenant_id: str) -> dict[str, Any]:
    """建站/SEO/内容生成共用 — 无产品画像则禁止泛写。"""
    profile = get_tenant_product_profile(db, tenant_id)
    if profile.get("ready_for_outreach"):
        return profile
    raise ProductProfileRequiredError(
        "PRODUCT_PROFILE_REQUIRED",
        "请先在产品库录入至少 1 个真实产品，或完成开户主营产品与产地（大城/河间）；"
        "SEO 文章与矩阵内容必须绑定真实规格，不能按默认「建材」乱写。",
    )
