"""èªå¨è°å - æéä¾è®©è§å/å­¡æ¹æµ/ç­ç¥æ¨¡æ¿ ååæµè¯0:"""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta, timezone

from app.services.foreign_trade.negotiation_rules import (
    ConcessionResult,
    NegotiationRules,
    apply_concession,
)
from app.services.foreign_trade.approval_flow import (
    ApprovalFlow,
    ApprovalLevel,
    ApprovalStatus,
    ApprovalRecord,
    get_approval_flow,
    register_audit_hook,
    fire_audit_event,
)
from app.services.foreign_trade.strategy_templates import (
    for_fo_strategy,
    cif_strategy,
    ddp_strategy,
    get_strategy,
    list_strategies,
)


# 1. negotiation_rules - éä¾è®©å¼æ


class TestNegotiationRules:
    BASE_PRICE = 100.0
    BASE_COST = 80.0  # floor at 80 * 1.08 = 86.4

    def _rules(self, **kwargs):
        defaults = dict(floor_margin_pct=8.0, max_auto_discount_pct=5.0)
        defaults.update(kwargs)
        return NegotiationRules(**defaults)

    def test_round_1_no_discount(self):
        rules = self._rules()
        result = apply_concession(
            rules=rules, round_no=1,
            requested_discount=10.0,
            base_price=self.BASE_PRICE, base_cost=self.BASE_COST,
        )
        assert result.concession_price == self.BASE_PRICE
        assert result.concession_rate == 0.0
        assert result.needs_approval is False

    def test_round_2_within_threshold(self):
        rules = self._rules()
        result = apply_concession(
            rules=rules, round_no=2,
            requested_discount=3.0,
            base_price=self.BASE_PRICE, base_cost=self.BASE_COST,
        )
        assert result.needs_approval is False
        assert result.concession_rate == 3.0
        assert result.concession_price == 97.0

    def test_round_2_exceeds_threshold(self):
        rules = self._rules()
        result = apply_concession(
            rules=rules, round_no=2,
            requested_discount=8.0,
            base_price=self.BASE_PRICE, base_cost=self.BASE_COST,
        )
        assert result.needs_approval is True

    def test_floor_price_protection(self):
        # base_cost=100, floor_margin=8% -> floor=108
        # base_price=120, request 20% -> exceeds round 3 max (10%) -> approval
        rules = self._rules(floor_margin_pct=8.0)
        result = apply_concession(
            rules=rules, round_no=3,
            requested_discount=20.0,
            base_price=120.0, base_cost=100.0,
        )
        assert result.needs_approval is True  # exceeds round 3 threshold of 10%
        assert result.concession_price == 96.0  # 120 * (1 - 0.20)

    def test_floor_price_clamped_within_authorization(self):
        # base_cost=100, floor_margin=8% -> floor=108
        # base_price=120, request 5% -> within round 3 max (10%) -> no approval
        # 120*0.95=114 > 108 -> no clamp needed
        rules = self._rules(floor_margin_pct=8.0)
        result = apply_concession(
            rules=rules, round_no=3,
            requested_discount=5.0,
            base_price=120.0, base_cost=100.0,
        )
        assert result.needs_approval is False
        assert result.concession_price == 114.0

    def test_floor_price_clamped_when_low_price(self):
        # base_cost=100, floor_margin=8% -> floor=108
        # base_price=100, request 3% -> within round 2 max (5%) -> no approval
        # 100*0.97=97 < 108 -> clamp to 108
        rules = self._rules(floor_margin_pct=8.0)
        result = apply_concession(
            rules=rules, round_no=2,
            requested_discount=3.0,
            base_price=100.0, base_cost=100.0,
        )
        assert result.concession_price == 108.0
        assert result.needs_approval is False  # clamped, not over threshold

    def test_moq_bonus_added(self):
        rules = self._rules(
            moq_discount_table=[{"min_qty": 100, "discount_pct": 2.0}],
        )
        result = apply_concession(
            rules=rules, round_no=2,
            requested_discount=3.0,
            base_price=100.0, base_cost=80.0,
            quantity=150,
        )
        # effective = 3 + 2 = 5, equals max_auto_discount_pct=5 -> still in range
        assert result.needs_approval is False

    def test_default_rules_match_hardcoded_behavior(self):
        rules = NegotiationRules.DEFAULT
        r1 = rules.apply_concession(round_no=1, requested_discount=5.0,
                                     base_price=100.0, base_cost=80.0)
        assert r1.concession_rate == 0.0
        assert r1.needs_approval is False
        r2 = rules.apply_concession(round_no=2, requested_discount=3.0,
                                     base_price=100.0, base_cost=80.0)
        assert r2.concession_rate == 3.0
        assert r2.needs_approval is False
        r2b = rules.apply_concession(round_no=2, requested_discount=8.0,
                                      base_price=100.0, base_cost=80.0)
        assert r2b.needs_approval is True


# 2. approval_flow - åçº§å®¡æ¹æµ


class TestApprovalFlow:
    def test_submit_creates_pending_request(self):
        flow = ApprovalFlow()
        req = flow.submit_for_approval(
            negotiation_id="neg-001", tenant_id="t1",
            round_no=2, requested_discount=3.0,
            concession_price=97.0, base_price=100.0,
            requester_id="user-1",
        )
        assert req.status == ApprovalStatus.PENDING
        assert req.current_level == ApprovalLevel.SALES_REP
        assert req.negotiation_id == "neg-001"

    def test_escalation_to_manager_at_5_percent(self):
        flow = ApprovalFlow()
        req = flow.submit_for_approval(
            negotiation_id="neg-002", tenant_id="t1",
            round_no=2, requested_discount=6.0,
            concession_price=94.0, base_price=100.0,
            requester_id="user-1",
        )
        assert req.current_level == ApprovalLevel.SALES_MANAGER

    def test_escalation_to_director_at_10_percent(self):
        flow = ApprovalFlow()
        req = flow.submit_for_approval(
            negotiation_id="neg-003", tenant_id="t1",
            round_no=3, requested_discount=12.0,
            concession_price=88.0, base_price=100.0,
            requester_id="user-1",
        )
        assert req.current_level == ApprovalLevel.DIRECTOR

    def test_approve_success(self):
        flow = ApprovalFlow()
        flow.submit_for_approval(
            negotiation_id="neg-004", tenant_id="t1",
            round_no=2, requested_discount=3.0,
            concession_price=97.0, base_price=100.0,
            requester_id="user-1",
        )
        req = flow.approve(
            negotiation_id="neg-004", tenant_id="t1",
            approver_id="mgr-1", approver_role="sales_manager",
            notes="approved",
        )
        assert req.status == ApprovalStatus.APPROVED
        assert req.decision_by == "mgr-1"
        assert len(req.history) == 1
        assert req.history[0].action == "approve"

    def test_reject_success(self):
        flow = ApprovalFlow()
        flow.submit_for_approval(
            negotiation_id="neg-005", tenant_id="t1",
            round_no=2, requested_discount=3.0,
            concession_price=97.0, base_price=100.0,
            requester_id="user-1",
        )
        req = flow.reject(
            negotiation_id="neg-005", tenant_id="t1",
            rejecter_id="mgr-1", rejecter_role="sales_manager",
        )
        assert req.status == ApprovalStatus.REJECTED
        assert len(req.history) == 1
        assert req.history[0].action == "reject"

    def test_pending_returns_request(self):
        flow = ApprovalFlow()
        flow.submit_for_approval(
            negotiation_id="neg-006", tenant_id="t1",
            round_no=1, requested_discount=0.0,
            concession_price=100.0, base_price=100.0,
            requester_id="user-1",
        )
        req = flow.pending(negotiation_id="neg-006", tenant_id="t1")
        assert req is not None
        assert req.status == ApprovalStatus.PENDING

    def test_pending_returns_none_for_unknown(self):
        flow = ApprovalFlow()
        req = flow.pending(negotiation_id="neg-999", tenant_id="t1")
        assert req is None

    def test_timeout_detection(self):
        flow = ApprovalFlow()
        old_time = datetime.now(timezone.utc) - timedelta(hours=25)
        flow.submit_for_approval(
            negotiation_id="neg-007", tenant_id="t1",
            round_no=2, requested_discount=3.0,
            concession_price=97.0, base_price=100.0,
            requester_id="user-1",
        )
        req = flow.pending(negotiation_id="neg-007", tenant_id="t1")
        req.submitted_at = old_time
        timed_out = flow.check_timeouts()
        assert len(timed_out) == 1
        assert timed_out[0].status == ApprovalStatus.TIMEOUT

    def test_clear_removes_request(self):
        flow = ApprovalFlow()
        flow.submit_for_approval(
            negotiation_id="neg-008", tenant_id="t1",
            round_no=1, requested_discount=0.0,
            concession_price=100.0, base_price=100.0,
            requester_id="user-1",
        )
        assert flow.clear(tenant_id="t1", negotiation_id="neg-008") is True
        assert flow.pending(negotiation_id="neg-008", tenant_id="t1") is None

    def test_double_approve_raises(self):
        flow = ApprovalFlow()
        flow.submit_for_approval(
            negotiation_id="neg-009", tenant_id="t1",
            round_no=1, requested_discount=0.0,
            concession_price=100.0, base_price=100.0,
            requester_id="user-1",
        )
        flow.approve(negotiation_id="neg-009", tenant_id="t1",
                     approver_id="mgr-1", approver_role="sales_manager")
        with pytest.raises(ValueError):
            flow.approve(negotiation_id="neg-009", tenant_id="t1",
                         approver_id="mgr-2", approver_role="sales_manager")


# 3. strategy_templates - ä»ä»·ç­ç¥æ¨¡æ¿


class TestStrategyTemplates:
    def test_for_fo_strategy_exists(self):
        assert for_fo_strategy.incoterms == "FOB Shenzhen"
        assert for_fo_strategy.base_profit_margin_pct == 15.0
        assert for_fo_strategy.first_round_discount_pct == 0.0

    def test_cif_strategy_exists(self):
        assert cif_strategy.incoterms == "CIF Rotterdam"
        assert cif_strategy.base_profit_margin_pct == 20.0

    def test_ddp_strategy_exists(self):
        assert ddp_strategy.incoterms == "DDP Amsterdam"
        assert ddp_strategy.base_profit_margin_pct == 25.0

    def test_get_strategy_by_key(self):
        assert get_strategy("FOB") is for_fo_strategy
        assert get_strategy("cif") is cif_strategy  # case-insensitive
        assert get_strategy("DDP") is ddp_strategy

    def test_get_strategy_fallback_to_fob(self):
        result = get_strategy("UNKNOWN")
        assert result is for_fo_strategy

    def test_list_strategies(self):
        strategies = list_strategies()
        assert "FOB" in strategies
        assert "CIF" in strategies
        assert "DDP" in strategies
        assert len(strategies) == 3

    def test_fo_build_quote_params(self):
        params = for_fo_strategy.build_quote_params(base_cost=80.0, quantity=100)
        assert params["incoterms"] == "FOB Shenzhen"
        assert params["quoted_unit_price"] == 92.0  # 80 * 1.15
        assert params["floor_price"] == 86.4  # 80 * 1.08
        # MOQ 100 >= 100 -> 1% extra discount
        assert params["moq_extra_discount_pct"] == 1.0

    def test_cif_build_quote_params(self):
        params = cif_strategy.build_quote_params(base_cost=80.0, quantity=100)
        assert params["incoterms"] == "CIF Rotterdam"
        # first_round=2%, MOQ 50>=50 -> 1% extra -> total 3%
        assert params["moq_extra_discount_pct"] == 1.0

    def test_ddp_build_quote_params(self):
        params = ddp_strategy.build_quote_params(base_cost=80.0, quantity=100)
        assert params["incoterms"] == "DDP Amsterdam"
        # MOQ 100>=100 -> 1.5% extra
        assert params["moq_extra_discount_pct"] == 1.5

    def test_sample_mode_no_moq(self):
        # Create a strategy with sample_mode=True
        from app.services.foreign_trade.strategy_templates import StrategyParams
        sp = StrategyParams(
            incoterms="FOB Test",
            base_profit_margin_pct=15.0,
            first_round_discount_pct=0.0,
            max_auto_discount_pct=5.0,
            floor_margin_pct=8.0,
            moq_discounts=[{"min_qty": 100, "discount_pct": 5.0}],
            sample_mode=True,
        )
        params = sp.build_quote_params(base_cost=80.0, quantity=5)
        # sample mode with qty<10 should not apply MOQ
        assert params["moq_extra_discount_pct"] == 0.0

    def test_floor_price_clamped(self):
        params = for_fo_strategy.build_quote_params(
            base_cost=100.0, quantity=1000,
            unit_price_override=100.0,
        )
        # floor = 100 * 1.08 = 108, quoted=100, but max discount would go below floor
        # With MOQ 3% and first_round 0%, total=3%, price=97 < 108 -> clamped to 108
        assert params["final_unit_price"] == 108.0
