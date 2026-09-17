# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""211 专家变现契约 — 每位角色须有赚钱路径，否则不得摸金上场。"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.services.hermes.agency.role_loader import list_roles, load_role

_REGISTRY_PATH = Path(__file__).resolve().parents[2] / "data" / "hermes_role_economics.json"
_ORCH_PATH = Path(__file__).resolve().parents[2] / "data" / "hermes_greedy_agency_orchestration.json"


@lru_cache(maxsize=1)
def load_role_economics_registry() -> dict[str, Any]:
    """load_role_economics_registry。
    :return: 返回处理结果。
    """
    if not _REGISTRY_PATH.is_file():
        return {}
    with open(_REGISTRY_PATH, encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _lane_pool_role_ids() -> frozenset[str]:
    """_lane_pool_role_ids。
    :return: 返回处理结果。
    """
    if not _ORCH_PATH.is_file():
        return frozenset()
    try:
        with open(_ORCH_PATH, encoding="utf-8") as f:
            orch = json.load(f)
    except (OSError, json.JSONDecodeError):
        return frozenset()
    ids: set[str] = set()
    for pool in (orch.get("lane_role_pools") or {}).values():
        for rid in pool or []:
            if rid:
                ids.add(str(rid).strip())
    return frozenset(ids)


def _category_of(role_id: str) -> str:
    """_category_of。

    参数说明：
    :param role_id: 参数 role_id
    :return: 返回处理结果。
    """
    rid = (role_id or "").strip().strip("/")
    return rid.split("/")[0] if "/" in rid else "specialized"


def resolve_role_economics(role_id: str) -> dict[str, Any]:
    """合并 category 默认 + role 覆盖 → 单角色变现契约。"""
    reg = load_role_economics_registry()
    cat = _category_of(role_id)
    base = dict((reg.get("category_defaults") or {}).get(cat) or {})
    override = dict((reg.get("role_overrides") or {}).get(role_id) or {})
    merged = {**base, **override}
    role = load_role(role_id)
    if not merged:
        merged = {
            "monetize_type": "asset_creation",
            "loop_stages": ["L2_orchestrate"],
            "deliverable_skus": ["generic_brief"],
            "kpi_hooks": ["needs_pm_mapping"],
            "economic_tier": "dormant",
        }

    tier = str(merged.get("economic_tier") or "bench")
    if role_id in _lane_pool_role_ids() and tier != "dormant":
        tier = "active"
    try:
        from app.services.hermes.greedy_contest_memory_service import is_role_contest_protected
        if is_role_contest_protected(role_id):
            tier = "active"
    except Exception:
        pass
    mem_contest = None
    try:
        from app.services.hermes.greedy_contest_memory_service import get_role_memory
        rm = get_role_memory(role_id)
        mem_contest = {
            "contest_tier": rm.get("contest_tier"),
            "protected": rm.get("protected"),
            "experience_points": rm.get("experience_points"),
            "never_offline": rm.get("never_offline"),
        }
    except Exception:
        mem_contest = None
    return {
        "role_id": role_id,
        "name": (role or {}).get("name") or role_id.split("/")[-1],
        "category": cat,
        "economic_tier": tier,
        "monetize_type": merged.get("monetize_type"),
        "loop_stages": list(merged.get("loop_stages") or []),
        "deliverable_skus": list(merged.get("deliverable_skus") or []),
        "kpi_hooks": list(merged.get("kpi_hooks") or []),
        "intent_affinity": list(merged.get("intent_affinity") or []),
        "note": merged.get("note"),
        "callable": tier != "dormant",
        "mandate": reg.get("mandate"),
        "in_lane_pool": role_id in _lane_pool_role_ids(),
        "contest": mem_contest,
    }


def list_publish_sku_catalog() -> dict[str, Any]:
    """list_publish_sku_catalog。
    :return: 返回处理结果。
    """
    reg = load_role_economics_registry()
    return dict(reg.get("publish_sku_catalog") or {})


def build_l4_publish_items(
    *,
    asset: dict[str, Any],
    locale: str,
    deliverable_skus: list[str] | None = None,
) -> list[dict[str, Any]]:
    """按 deliverable SKU 生成 L4 发布队列条目（含 game/XR 互动展示）。"""
    from datetime import datetime, timezone
    catalog = list_publish_sku_catalog()
    detected: list[str] = list(deliverable_skus or [])
    blob = json.dumps(asset, ensure_ascii=False).lower()
    for sku_id in catalog:
        if sku_id in detected or sku_id in blob:
            detected.append(sku_id)
    detected = list(dict.fromkeys(detected))
    body = (
        asset.get("greedy_summary")
        or asset.get("marketing_plan")
        or asset.get("demo_concept")
        or asset.get("xr_variant")
        or ""
    )[:4000]
    queued_at = datetime.now(timezone.utc).isoformat()
    items: list[dict[str, Any]] = []
    for sku in detected:
        meta = catalog.get(sku) or {}
        items.append(
            {
                "sku": sku,
                "label": meta.get("label") or sku,
                "locale": locale,
                "title": meta.get("label") or "Platform survival monetization brief",
                "body": body,
                "scope": "platform_survival_marketing",
                "publish_channels": list(meta.get("publish_channels") or []),
                "cta": meta.get("cta"),
                "l4_payload_type": meta.get("l4_payload_type") or "article",
                "primary_roles": list(meta.get("primary_roles") or []),
                "queued_at": queued_at,
            }
        )

    if not items:
        items.append(
            {
                "sku": "generic_survival_brief",
                "label": "Survival monetization brief",
                "locale": locale,
                "title": "Platform survival monetization brief",
                "body": body,
                "scope": "platform_survival_marketing",
                "publish_channels": ["independent_landing"],
                "l4_payload_type": "article",
                "queued_at": queued_at,
            }
        )
    return items


def _score_role_for_intent(eco: dict[str, Any], *, intent: str | None, lane: str | None) -> float:
    """_score_role_for_intent。

    参数说明：
    :param eco: 参数 eco
    :param intent: 参数 intent
    :param lane: 参数 lane
    :return: 返回处理结果。
    """
    score = 0.0
    tier = eco.get("economic_tier")
    if tier == "active":
        score += 3.0
    elif tier == "bench":
        score += 1.5
    else:
        score -= 2.0

    if intent and intent in (eco.get("intent_affinity") or []):
        score += 4.0

    reg = load_role_economics_registry()
    boost = (reg.get("intent_lane_boost") or {}).get(intent or "") or {}
    if boost and eco.get("category") in (boost.get("categories") or []):
        score += 2.0

    if lane:
        reg_cfg_path = Path(__file__).resolve().parents[2] / "data" / "hermes_greedy_agency_orchestration.json"
        try:
            with open(reg_cfg_path, encoding="utf-8") as f:
                orch = json.load(f)
            pool = (orch.get("lane_role_pools") or {}).get(lane) or []
            if eco.get("role_id") in pool:
                score += 2.5
        except OSError:
            pass

    return score


def rank_roles_for_survival(
    *,
    intent: str | None = None,
    lane: str | None = None,
    loop_stage: str | None = None,
    limit: int = 12,
    include_dormant: bool = False,
) -> list[dict[str, Any]]:
    """按 intent/lane/L 段为 survival 蜂群排序可上场专家。"""
    rows: list[dict[str, Any]] = []
    for r in list_roles():
        rid = r["role_id"]
        eco = resolve_role_economics(rid)
        if not include_dormant and not eco.get("callable"):
            continue
        if loop_stage and loop_stage not in (eco.get("loop_stages") or []):
            continue
        eco["survival_score"] = round(_score_role_for_intent(eco, intent=intent, lane=lane), 2)
        rows.append(eco)

    rows.sort(key=lambda x: (-float(x.get("survival_score") or 0), x.get("role_id") or ""))
    return rows[: max(1, min(limit, 50))]


def economics_coverage_report() -> dict[str, Any]:
    """编制内变现覆盖率 — PM 看板用。"""
    reg = load_role_economics_registry()
    roles = list_roles()
    tiers: dict[str, int] = {"active": 0, "bench": 0, "dormant": 0}
    by_category: dict[str, dict[str, int]] = {}
    for r in roles:
        eco = resolve_role_economics(r["role_id"])
        tier = str(eco.get("economic_tier") or "bench")
        tiers[tier] = tiers.get(tier, 0) + 1
        cat = eco.get("category") or "other"
        by_category.setdefault(cat, {"total": 0, "active": 0, "bench": 0, "dormant": 0})
        by_category[cat]["total"] += 1
        by_category[cat][tier] = by_category[cat].get(tier, 0) + 1

    return {
        "mandate": reg.get("mandate"),
        "role_count": len(roles),
        "tiers": tiers,
        "coverage_pct": round(100.0 * (1 - tiers.get("dormant", 0) / max(len(roles), 1)), 1),
        "by_category": by_category,
        "monetize_types": reg.get("monetize_types"),
        "lane_pool_active_count": len(_lane_pool_role_ids()),
        "publish_sku_count": len(reg.get("publish_sku_catalog") or {}),
    }
