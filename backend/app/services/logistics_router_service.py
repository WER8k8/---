# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""物流智能路由规划与多商比价 —— §10 缺口补齐。

多物流商比价 + 智能路由选择（多目标加权排序）+ 时效预测。
不依赖外部运价 API 时，用内置规则运价表估算（明确标记 estimate=True），
保证可离线跑通；接真实运价源后替换 _rule_quote 即可。
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, List, Optional

# ── 内置承运商档案（规则运价，接真实 API 前用）────────────────────
# cost_per_kg: 首公里单价；transit_days: 基准时效；reliability: 0-1
_CARRIERS: dict[str, dict[str, Any]] = {
    "dhl": {"cost_per_kg": 4.5, "transit_days": 4, "reliability": 0.97, "type": "air"},
    "ups": {"cost_per_kg": 3.8, "transit_days": 5, "reliability": 0.95, "type": "air"},
    "fedex": {"cost_per_kg": 4.2, "transit_days": 4, "reliability": 0.96, "type": "air"},
    "dhl_express": {"cost_per_kg": 5.0, "transit_days": 2, "reliability": 0.99, "type": "air"},
    "sea_standard": {"cost_per_kg": 0.4, "transit_days": 30, "reliability": 0.88, "type": "sea"},
    "sea_premium": {"cost_per_kg": 0.6, "transit_days": 20, "reliability": 0.92, "type": "sea"},
    "rail_eurasia": {"cost_per_kg": 0.8, "transit_days": 18, "reliability": 0.90, "type": "rail"},
    "land_lcl": {"cost_per_kg": 1.2, "transit_days": 12, "reliability": 0.85, "type": "land"},
}

# 多目标权重（默认）
DEFAULT_WEIGHTS: dict[str, float] = {"cost": 0.4, "time": 0.3, "reliability": 0.3}
# 偏好模板
PREFERENCE_WEIGHTS: dict[str, dict[str, float]] = {
    "cheapest": {"cost": 0.7, "time": 0.15, "reliability": 0.15},
    "fastest": {"cost": 0.15, "time": 0.65, "reliability": 0.2},
    "safest": {"cost": 0.15, "time": 0.2, "reliability": 0.65},
    "balanced": DEFAULT_WEIGHTS,
}


@dataclass
class FreightQuote:
    """单个承运商的报价。"""
    carrier: str
    service_type: str
    cost: float
    transit_days: int
    reliability: float
    estimated_delivery_date: Optional[str] = None
    weight_kg: float = 0.0
    estimate: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _rule_quote(carrier: str, weight_kg: float) -> FreightQuote:
    """内置规则报价（无真实运价 API 时的估算，estimate=True）。"""
    info = _CARRIERS[carrier]
    cost = round(info["cost_per_kg"] * max(weight_kg, 1.0), 2)
    return FreightQuote(
        carrier=carrier,
        service_type=info["type"],
        cost=cost,
        transit_days=int(info["transit_days"]),
        reliability=float(info["reliability"]),
        weight_kg=round(weight_kg, 2),
        estimate=True,
    )


def list_available_carriers() -> List[str]:
    return list(_CARRIERS.keys())


def query_multiple_providers(
    *,
    origin: str,
    destination: str,
    weight_kg: float,
    volume: float = 0.0,
    urgency: str = "standard",
    carriers: Optional[List[str]] = None,
) -> List[FreightQuote]:
    """多物流商比价（规则估算，接真实 API 前可用）。

    urgency: standard / express —— express 只留时效快的（air/express 类）。
    """
    selected = carriers or list_available_carriers()
    quotes: List[FreightQuote] = []
    for c in selected:
        if c not in _CARRIERS:
            continue
        q = _rule_quote(c, float(weight_kg or 0.0))
        if urgency == "express" and _CARRIERS[c]["type"] not in ("air",):
            continue
        q.estimated_delivery_date = None  # 由上层按 transit_days 推算
        quotes.append(q)
    return quotes


def rank_quotes(
    quotes: List[FreightQuote],
    *,
    preference: str = "balanced",
    weights: Optional[dict[str, float]] = None,
) -> List[FreightQuote]:
    """多目标加权排序：cost*wc + time*wt + reliability*wr（越小越好的归一化）。

    cost/time 越低越好，reliability 越高越好；统一转成 0-1 的"优劣分"再加权。
    返回按综合分从高到低排序的报价（最优在前）。
    """
    w = dict(weights or PREFERENCE_WEIGHTS.get(preference, DEFAULT_WEIGHTS))
    if not quotes:
        return []
    max_cost = max(q.cost for q in quotes) or 1.0
    max_time = max(q.transit_days for q in quotes) or 1.0

    scored: list[tuple[float, int, FreightQuote]] = []
    for i, q in enumerate(quotes):
        cost_good = 1.0 - (q.cost / max_cost)            # 越便宜越好
        time_good = 1.0 - (q.transit_days / max_time)     # 越快越好
        rel_good = q.reliability
        composite = (
            cost_good * w.get("cost", 0.4)
            + time_good * w.get("time", 0.3)
            + rel_good * w.get("reliability", 0.3)
        )
        scored.append((composite, -i, q))
    scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return [q for _, _, q in scored]


def plan_route(
    *,
    origin: str,
    destination: str,
    weight_kg: float,
    volume: float = 0.0,
    urgency: str = "standard",
    preference: str = "balanced",
    weights: Optional[dict[str, float]] = None,
) -> dict[str, Any]:
    """一站式路由规划：比价 + 排序 + 推荐 + 时效预测。"""
    quotes = query_multiple_providers(
        origin=origin, destination=destination,
        weight_kg=weight_kg, volume=volume, urgency=urgency,
    )
    ranked = rank_quotes(quotes, preference=preference, weights=weights)
    best = ranked[0].to_dict() if ranked else None
    return {
        "origin": origin,
        "destination": destination,
        "weight_kg": round(float(weight_kg or 0.0), 2),
        "urgency": urgency,
        "preference": preference,
        "all_quotes": [q.to_dict() for q in quotes],
        "ranked": [q.to_dict() for q in ranked],
        "recommended": best,
        "transit_forecast": _transit_forecast(best["transit_days"]) if best else {},
        "note": "估算值，接真实运价源后替换 _rule_quote",
    }


def _transit_forecast(transit_days: int) -> dict[str, Any]:
    """时效预测：给个区间（±15%），基于航线常识。"""
    lo = max(1, int(transit_days * 0.85))
    hi = int(transit_days * 1.15)
    return {"min_days": lo, "max_days": hi, "expected_days": transit_days}


# ── 兼容旧 /lbs-routing 端点的测距占位（真实测距待接地图 API）────
def lbs_distance_estimate(origin: Optional[dict], dest_city: Optional[str]) -> dict[str, Any]:
    """无地图 API 时的保守测距占位：返回估算值并明确标记 estimate。"""
    return {
        "distance_km": 0,
        "estimated_time_min": 0,
        "route_points": [],
        "toll_fee": 0,
        "estimate": True,
        "note": "未接地图测距 API，返回 0 占位；接 Google/高德后替换本函数",
    }
