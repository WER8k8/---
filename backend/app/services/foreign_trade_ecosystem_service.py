# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""外贸工具·技能·生态目录 — 随源码部署，供 Admin/API/研究员引用。"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_CATALOG_PATH = _DATA_DIR / "foreign_trade_ecosystem_catalog.json"
_EXPERTS_PATH = _DATA_DIR / "b2b_trade_experts.json"
_PLUGINS_PATH = _DATA_DIR / "hermes_plugin_catalog.json"


def _load_json(path: Path) -> dict[str, Any]:
    """_load_json。

    参数说明：
    :param path: 参数 path
    :return: 返回处理结果。
    """
    if not path.is_file():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_ecosystem_catalog() -> dict[str, Any]:
    """load_ecosystem_catalog。
    :return: 返回处理结果。
    """
    return _load_json(_CATALOG_PATH)


def list_skills(*, status: str | None = None, category: str | None = None) -> list[dict[str, Any]]:
    """list_skills。

    参数说明：
    :param status: 参数 status
    :param category: 参数 category
    :return: 返回处理结果。
    """
    items = list(load_ecosystem_catalog().get("skills_registry") or [])
    if status:
        items = [i for i in items if i.get("status") == status]
    if category:
        items = [i for i in items if i.get("category") == category]
    return items


def list_gaps(*, priority: str = "P0") -> list[dict[str, Any]]:
    """list_gaps。

    参数说明：
    :param priority: 参数 priority
    :return: 返回处理结果。
    """
    cat = load_ecosystem_catalog()
    key = f"open_gaps_{priority.lower()}"
    if key in cat:
        return list(cat.get(key) or [])
    if priority.upper() == "P0":
        return list(cat.get("open_gaps_p0") or [])
    return []


def build_ecosystem_overview() -> dict[str, Any]:
    """build_ecosystem_overview。
    :return: 返回处理结果。
    """
    cat = load_ecosystem_catalog()
    skills = cat.get("skills_registry") or []
    by_status: dict[str, int] = {}
    for s in skills:
        st = s.get("status") or "unknown"
        by_status[st] = by_status.get(st, 0) + 1

    experts = _load_json(_EXPERTS_PATH).get("experts") or []
    plugins = _load_json(_PLUGINS_PATH).get("plugins") or []
    return {
        "catalog_version": cat.get("catalog_version"),
        "title": cat.get("title"),
        "deploy_tiers": cat.get("deploy_tiers"),
        "gap_summary": cat.get("gap_summary"),
        "skills_total": len(skills),
        "skills_by_status": by_status,
        "bundled_capabilities_count": len(cat.get("bundled_capabilities") or []),
        "optional_sidecars_count": len(cat.get("optional_sidecars") or []),
        "github_curated_count": len(cat.get("github_curated") or []),
        "open_p0_gaps": cat.get("open_gaps_p0") or [],
        "b2b_experts_count": len(experts),
        "hermes_plugins_count": len(plugins),
        "knowledge_assets": cat.get("knowledge_assets_in_repo") or [],
        "github_search_url": (cat.get("github_search") or {}).get("url"),
    }


def build_deploy_manifest() -> dict[str, Any]:
    """运维部署清单：bundled + optional + env。"""
    cat = load_ecosystem_catalog()
    return {
        "bundled": cat.get("bundled_capabilities") or [],
        "optional_sidecars": cat.get("optional_sidecars") or [],
        "knowledge_assets": cat.get("knowledge_assets_in_repo") or [],
        "env_template": "deploy/production/env.template",
        "deploy_readme": "deploy/docs/FOREIGN-TRADE-ECOSYSTEM-DEPLOY.md",
    }


def recommend_integrations_for_gaps() -> list[dict[str, Any]]:
    """短板 → 推荐 GitHub/侧car 补齐（不自动安装）。"""
    cat = load_ecosystem_catalog()
    curated = {c["repo"]: c for c in cat.get("github_curated") or [] if c.get("repo")}
    out: list[dict[str, Any]] = []
    for gap in cat.get("open_gaps_p0") or []:
        row = dict(gap)
        if "UTM" in gap.get("title", ""):
            row["github_hint"] = "leadscloud/inquiry"
        elif "MEDDPICC" in gap.get("title", ""):
            row["github_hint"] = "iPythoning/b2b-sdr-agent-template"
        elif "AEO" in gap.get("title", ""):
            row["github_hint"] = "zeeler/ecomm"
        out.append(row)
    for skill in cat.get("skills_registry") or []:
        if skill.get("status") != "reference":
            continue
        gh = skill.get("github")
        if gh and gh in curated:
            out.append(
                {
                    "skill_id": skill.get("id"),
                    "github": gh,
                    "integrate": skill.get("integrate") or curated[gh].get("integrate_plan"),
                }
            )
    return out


def list_b2b_experts() -> dict[str, Any]:
    """B2B 外贸 AI 专家角色库（Admin「AI 外贸团队」页）。"""
    raw = _load_json(_EXPERTS_PATH)
    experts = list(raw.get("experts") or [])
    return {
        "catalog_version": raw.get("catalog_version"),
        "platform_note": raw.get("platform_note"),
        "parent_doc": raw.get("parent_doc"),
        "experts": experts,
        "total": len(experts),
    }
