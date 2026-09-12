"""Hermes 插件注册表 — 对内完整目录，对外经 marketplace 脱敏。"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_CATALOG_PATH = Path(__file__).resolve().parents[2] / "data" / "hermes_plugin_catalog.json"

# 新租户默认启用（旺财市场「官方推荐包」）
DEFAULT_TENANT_PLUGIN_IDS = (
    "ai_site_builder",
    "sales_flywheel_loop",
    "video_matrix_real_publish",
    "export_feasibility",
    "find_buyers",
    "market_research",
    "outreach_letter_pack",
    "inquiry_score",
    "weekly_lead_report",
    "sync_feedback",
    "geo_content_matrix",
    "china_platform_content",
)
def load_catalog() -> dict[str, Any]:
    """load_catalog。
    :return: 返回处理结果。
    """
    with open(_CATALOG_PATH, encoding="utf-8") as f:
        return json.load(f)


def list_plugins(*, visibility: str | None = None) -> list[dict[str, Any]]:
    """list_plugins。

    参数说明：
    :param visibility: 参数 visibility
    :return: 返回处理结果。
    """
    out: list[dict[str, Any]] = []
    for p in load_catalog().get("plugins", []):
        vis = p.get("visibility")
        if visibility == "public" and vis != "public":
            continue
        if visibility == "internal" and vis != "internal":
            continue
        out.append(p)
    return out


def get_plugin(plugin_id: str) -> dict[str, Any] | None:
    """get_plugin。

    参数说明：
    :param plugin_id: 参数 plugin_id
    :return: 返回处理结果。
    """
    for p in load_catalog().get("plugins", []):
        if p.get("id") == plugin_id:
            return p
    return None


def catalog_meta() -> dict[str, Any]:
    """catalog_meta。
    :return: 返回处理结果。
    """
    cat = load_catalog()
    plugins = cat.get("plugins", [])
    stable = sum(1 for p in plugins if p.get("maturity") == "stable")
    partial = sum(1 for p in plugins if p.get("maturity") == "partial")
    public = sum(1 for p in plugins if p.get("visibility") == "public")
    return {
        "catalog_version": cat.get("catalog_version"),
        "public_market_brand": cat.get("public_market_brand"),
        "internal_brand": cat.get("internal_brand"),
        "plugin_count": len(plugins),
        "public_count": public,
        "stable_count": stable,
        "partial_count": partial,
    }


def public_market_item(plugin: dict[str, Any]) -> dict[str, Any]:
    """旺财插件市场条目（无内部 handler / 无第三方商标）。"""
    pub = dict(plugin.get("public") or {})
    internal = plugin.get("internal") or {}
    kind = str(internal.get("kind") or "")
    item = {
        "id": plugin.get("id"),
        "version": plugin.get("version"),
        "name": pub.get("name"),
        "tagline": pub.get("tagline"),
        "description": pub.get("description"),
        "category": pub.get("category"),
        "icon": pub.get("icon"),
        "author": pub.get("author"),
        "maturity": plugin.get("maturity"),
        "plan_tier": plugin.get("plan_tier"),
        "requires_confirmation": bool(plugin.get("requires_confirmation")),
        "install_kind": "local_browser" if kind == "browser_companion" else "server",
    }
    if kind == "browser_companion":
        companion = dict(pub.get("companion") or {})
        item["companion"] = {
            "content_types": companion.get("content_types") or [],
            "platforms": companion.get("platforms") or [],
            "install": companion.get("install") or {},
            "disclaimer": companion.get("disclaimer"),
            "recommended_for": companion.get("recommended_for"),
            "platform_exclusive": bool(companion.get("platform_exclusive")),
            "launch_route": companion.get("launch_route"),
        }
    return item


def internal_plugin_item(plugin: dict[str, Any]) -> dict[str, Any]:
    """Hermes 对内运维视图。"""
    return {
        **public_market_item(plugin),
        "visibility": plugin.get("visibility"),
        "internal": plugin.get("internal"),
    }
