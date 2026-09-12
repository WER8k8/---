"""标杆来源取长补短 — 供研究员 / Admin / ecosystem API 引用。"""

from __future__ import annotations

from typing import Any

from app.services.foreign_trade_ecosystem_service import load_ecosystem_catalog


def list_benchmark_sources(*, category: str | None = None) -> list[dict[str, Any]]:
    """实现 列出benchmarksources 的功能。
    
    :param category: 参数 category（类型: str | None）
    :return: 返回 list[dict[str, Any]] 结果
    """
    cat = load_ecosystem_catalog()
    items = list(cat.get("benchmark_sources") or [])
    if category:
        items = [i for i in items if i.get("category") == category]
    return items


def build_benchmark_matrix() -> dict[str, Any]:
    """能力 × 标杆 × 我们动作 — 一览表。"""
    cat = load_ecosystem_catalog()
    return {
        "catalog_version": cat.get("catalog_version"),
        "principle": cat.get("benchmark_principle"),
        "sources": cat.get("benchmark_sources") or [],
        "capability_matrix": cat.get("capability_benchmark_matrix") or [],
        "external_nav": cat.get("external_nav") or {},
        "docs": "docs/foreign-trade-benchmark-sources.md",
    }


def adopt_playbook_hints(gap_skill_id: str) -> list[dict[str, Any]]:
    """短板技能 → 推荐借鉴的外部 repo/playbook。"""
    cat = load_ecosystem_catalog()
    out: list[dict[str, Any]] = []
    skill_map = {s["id"]: s for s in cat.get("skills_registry") or [] if s.get("id")}
    target = skill_map.get(gap_skill_id)
    if not target:
        return out
    for src in cat.get("benchmark_sources") or []:
        adopts = src.get("adopt_into_us") or []
        if any(gap_skill_id in str(a) for a in adopts):
            out.append(
                {
                    "source_id": src.get("id"),
                    "repo": src.get("repo"),
                    "url": src.get("url"),
                    "take": src.get("take"),
                    "integrate_plan": src.get("integrate_plan"),
                }
            )
    return out
