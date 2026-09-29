# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""第二层缺口 E · 成本事件与单位经济单元测试。"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
import pytest

from app.models.cost_event import CostEvent
from app.models.finance_ledger import FinanceLedgerEntry
from app.services.cost_service import record_cost_event, get_tenant_unit_economics


def test_cost_event_recording_and_margin(db_session):
    tenant_id = str(uuid.uuid4())

    # 1. 记入一笔营收（100 美元 = 10000 分）
    ledger = FinanceLedgerEntry(
        tenant_id=tenant_id,
        entry_type="revenue",
        category="subscription",
        amount_cents=10000,
        note="SaaS Subscription Plan",
        recorded_at=datetime.now(timezone.utc),
    )
    db_session.add(ledger)
    db_session.commit()

    # 2. 记入三笔成本：AI Token 成本 15.5，Browser 代理成本 8.0，存储成本 2.0
    c1 = record_cost_event(
        db_session,
        tenant_id=tenant_id,
        cost_code="cost.ai.token",
        cost_category="ai",
        amount=15.5,
        quantity=50000,
        unit="tokens",
        provider="deepseek",
    )
    c2 = record_cost_event(
        db_session,
        tenant_id=tenant_id,
        cost_code="cost.egress.proxy",
        cost_category="browser",
        amount=8.0,
        quantity=1,
        unit="ip_slot",
        provider="brightdata",
    )
    c3 = record_cost_event(
        db_session,
        tenant_id=tenant_id,
        cost_code="cost.infra.storage",
        cost_category="infra",
        amount=2.0,
        quantity=10,
        unit="gb",
    )
    assert c1.id is not None
    assert c2.id is not None

    # 3. 计算单位经济与毛利
    ue = get_tenant_unit_economics(db_session, tenant_id=tenant_id)
    assert ue["revenue"] == 100.0
    assert ue["direct_cost"] == 25.5
    assert ue["gross_margin"] == 74.5
    assert ue["gross_margin_rate"] == 0.745
    assert ue["cost_breakdown"] == {"ai": 15.5, "browser": 8.0, "infra": 2.0}
    assert ue["is_profitable"] is True
