"""大城+河间 SEO/GEO 词库 — Client 预览与入库（W3）。"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.services.dacheng_keyword_seed_service import (
    list_belt_packs,
    load_dacheng_keyword_pack,
    seed_industry_belt_keywords,
)
from app.services.tenant_product_profile_service import get_tenant_product_profile


def preview_belt_keywords(db: Session, tenant: Tenant) -> dict[str, Any]:
    """实现 previewbelt关键词 的功能。
    
    :param db: 参数 db（类型: Session）
    :param tenant: 参数 tenant（类型: Tenant）
    :return: 返回 dict[str, Any] 结果
    """
    profile = get_tenant_product_profile(db, str(tenant.id))
    region = profile.get("region_label_zh") or ""
    packs = list_belt_packs(belt_id="all")
    matched: list[dict[str, Any]] = []
    for pack in packs:
        label = str(pack.get("label") or "")
        if not region or any(tok in region for tok in (pack.get("regions") or [])):
            matched.append(
                {
                    "belt_id": pack.get("belt_id"),
                    "label": label,
                    "products": (pack.get("products") or [])[:8],
                    "ranking_keywords": (pack.get("ranking_keywords") or [])[:8],
                }
            )
    if not matched:
        matched = [
            {
                "belt_id": p.get("belt_id"),
                "label": p.get("label"),
                "products": (p.get("products") or [])[:8],
                "ranking_keywords": (p.get("ranking_keywords") or [])[:8],
            }
            for p in packs[:2]
        ]
    root = load_dacheng_keyword_pack()
    return {
        "region_label": region,
        "primary_product": profile.get("primary_product"),
        "belts": matched,
        "long_tail_templates": root.get("long_tail_templates") or [],
        "honest_note": "词库来自产业带参考包；上线前请对照自家真实产品名核对。",
        "seed_route": "/api/v1/cross-border/seo-keywords/seed",
    }


def seed_keywords_for_tenant(
    db: Session,
    *,
    belt_id: str = "all",
    include_ranking: bool = True,
) -> dict[str, Any]:
    """实现 seed关键词for租户 的功能。
    
    :param db: 参数 db（类型: Session）
    :param belt_id: 参数 belt_id（类型: str）
    :param include_ranking: 参数 include_ranking（类型: bool）
    :return: 返回 dict[str, Any] 结果
    """
    return seed_industry_belt_keywords(db, belt_id=belt_id, include_ranking=include_ranking)
