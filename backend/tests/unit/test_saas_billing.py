"""SaaS 订阅计费引擎测试"""
import pytest
from datetime import datetime, timedelta
from app.services.saas_billing import SaaSBillingEngine, PlanTier, PLAN_PRICES


@pytest.fixture
def engine():
    return SaaSBillingEngine()


class TestPlanTier:
    def test_prices_match_tiers(self):
        assert PLAN_PRICES[PlanTier.FREE] == 0
        assert PLAN_PRICES[PlanTier.STARTER] == 29
        assert PLAN_PRICES[PlanTier.PROFESSIONAL] == 99
        assert PLAN_PRICES[PlanTier.ENTERPRISE] == 299


class TestSaaSBillingEngine:
    def test_create_subscription(self, engine):
        result = engine.create_subscription("t1", PlanTier.PROFESSIONAL)
        assert result["tenant_id"] == "t1"
        assert result["plan"] == "professional"
        assert result["price_usd"] == 99
        assert result["billing_cycle"] == "monthly"
        assert result["status"] == "active"
        assert "started_at" in result
        assert "next_billing_at" in result

    def test_create_free_subscription(self, engine):
        result = engine.create_subscription("t2", PlanTier.FREE)
        assert result["price_usd"] == 0

    def test_check_billing_status(self, engine):
        result = engine.check_billing_status("t1")
        assert result["tenant_id"] == "t1"
        assert result["status"] == "active"
        assert result["overdue"] is False

    def test_process_renewal(self, engine):
        result = engine.process_renewal("t1")
        assert result["tenant_id"] == "t1"
        assert result["renewed"] is True
        next_billing = datetime.fromisoformat(result["next_billing_at"])
        assert next_billing > datetime.utcnow()
