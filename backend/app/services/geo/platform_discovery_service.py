# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""平台发现与扩展 — 对照 catalog / live 适配器，持续拉高 GEO 覆盖面。"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.services.geo.platform_rank_registry import (
    PlatformRankProfile,
    all_platform_rank_profiles,
    publish_order_for_ranking,
)
from app.services.platform_catalog import PLATFORMS_CN, PLATFORMS_GLOBAL, all_catalog_rows
from app.services.publish_capability_registry import TEXT_ADAPTER_PLATFORM_NAMES


def catalog_platform_names() -> set[str]:
    """实现 catalog平台names 的功能。
    
    :return: 返回 set[str] 结果
    """
    return {row[0] for row in all_catalog_rows()}


def live_adapter_names() -> set[str]:
    """实现 liveadapternames 的功能。
    
    :return: 返回 set[str] 结果
    """
    return set(TEXT_ADAPTER_PLATFORM_NAMES)


def exploration_gap_report() -> dict[str, Any]:
    """catalog 中有、但尚无 live 图文适配器的平台 — 按 GEO 权重排序待建设。"""
    catalog = catalog_platform_names()
    live = live_adapter_names()
    profiles = {p.name: p for p in all_platform_rank_profiles()}
    missing_live: list[dict[str, Any]] = []
    for name in sorted(catalog - live):
        prof = profiles.get(name)
        missing_live.append(
            {
                "name": name,
                "geo_weight": prof.geo_weight if prof else 0.5,
                "adapter_status": prof.adapter_status if prof else "exploration",
                "rank_priority": prof.rank_priority if prof else 99,
                "region": prof.region if prof else ("cn" if name in {r[0] for r in PLATFORMS_CN} else "global"),
            }
        )
    missing_live.sort(key=lambda x: (-x["geo_weight"], x["rank_priority"]))
    registered = {p.name for p in all_platform_rank_profiles()}
    unregistered_in_catalog = sorted(catalog - registered)
    return {
        "catalog_total": len(catalog),
        "live_adapter_count": len(live),
        "coverage_rate": round(len(live) / max(len(catalog), 1), 4),
        "missing_live_adapters": missing_live,
        "next_build_queue": missing_live[:8],
        "unregistered_in_rank_registry": unregistered_in_catalog,
        "recommended_publish_order_cn": publish_order_for_ranking(region="cn", limit=8),
        "recommended_publish_order_global": publish_order_for_ranking(region="global", limit=8),
        "principle": "平台数 × 有效发布 ≈ GEO 引用面；排名优先于功能展示",
    }


def propose_platform_registration(
    name: str,
    *,
    region: str = "cn",
    content_type: str = "article",
    geo_weight: float = 0.5,
) -> PlatformRankProfile:
    """客户/运营发现新渠道时，生成探索级排名档案（不写 DB，供 PM 排期）。"""
    label = (name or "").strip()
    if not label:
        raise ValueError("平台名称不能为空")
    return PlatformRankProfile(
        name=label,
        geo_weight=min(1.0, max(0.1, geo_weight)),
        adapter_status="exploration",
        region="global" if region in ("global", "intl") else "cn",
        content_type=content_type or "article",
        rank_priority=60,
    )


def discovery_snapshot(db: Session | None = None) -> dict[str, Any]:
    """合并 catalog 对齐 + 排名队列（API / tech-radar 用）。"""
    gap = exploration_gap_report()
    db_counts: dict[str, int] = {}
    if db is not None:
        try:
            from app.models.content import Platform
            db_counts["active_platforms"] = (
                db.query(Platform).filter(Platform.is_active.is_(True)).count()
            )
        except Exception:
            db_counts["active_platforms"] = 0
    return {**gap, **db_counts}
