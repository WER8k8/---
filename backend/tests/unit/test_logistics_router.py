"""§10 物流智能路由单元测试（纯规则，不依赖外部运价 API）。"""

from __future__ import annotations

from app.services.logistics_router_service import (
    _rule_quote,
    list_available_carriers,
    plan_route,
    query_multiple_providers,
    rank_quotes,
    lbs_distance_estimate,
    _transit_forecast,
)


class TestQuotes:
    def test_all_carriers_have_positive_cost(self):
        for c in list_available_carriers():
            q = _rule_quote(c, 100)
            assert q.cost > 0
            assert q.transit_days > 0

    def test_unknown_carrier_skipped(self):
        qs = query_multiple_providers(
            origin="CN", destination="US", weight_kg=10, carriers=["nope", "dhl"],
        )
        assert [q.carrier for q in qs] == ["dhl"]

    def test_express_filters_air(self):
        qs = query_multiple_providers(
            origin="CN", destination="US", weight_kg=10, urgency="express",
        )
        for q in qs:
            assert q.service_type == "air"


class TestRanking:
    def test_cheapest_prefers_low_cost(self):
        """cheapest 偏好是加权多目标（cost 0.7/time 0.15/reliability 0.15），
        最便宜的承运商应排前列（前 3），而非被快而贵的空运压到末尾。"""
        qs = query_multiple_providers(
            origin="CN", destination="US", weight_kg=1000,
        )
        ranked = rank_quotes(qs, preference="cheapest")
        min_cost = min(q.cost for q in qs)
        cheap = [q for q in ranked if q.cost == min_cost]
        assert cheap and cheap[0] in ranked[:3]
        # 且贵空运（cost 最高）不应排第一
        most_expensive = max(q.cost for q in qs)
        assert ranked[0].cost != most_expensive

    def test_fastest_prefers_lowest_days(self):
        qs = query_multiple_providers(
            origin="CN", destination="US", weight_kg=10,
        )
        ranked = rank_quotes(qs, preference="fastest")
        assert ranked[0].transit_days == min(q.transit_days for q in qs)

    def test_empty_returns_empty(self):
        assert rank_quotes([], preference="balanced") == []


class TestPlanRoute:
    def test_plan_structure(self):
        plan = plan_route(
            origin="Shanghai", destination="Rotterdam",
            weight_kg=500, preference="balanced",
        )
        assert plan["recommended"] is not None
        assert "transit_forecast" in plan
        assert plan["ranked"]
        assert all(q["estimate"] for q in plan["all_quotes"])

    def test_forecast_bounds(self):
        fc = _transit_forecast(10)
        assert fc["min_days"] <= 10 <= fc["max_days"]


class TestLbsPlaceholder:
    def test_placeholder_marks_estimate(self):
        r = lbs_distance_estimate(None, "Rotterdam")
        assert r["estimate"] is True
        assert r["distance_km"] == 0  # 占位，接地图 API 前
