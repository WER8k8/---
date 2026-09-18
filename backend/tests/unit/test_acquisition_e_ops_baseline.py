# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""E 系列：限流 + 对账 + 队列监控 + 压测基线。"""
from __future__ import annotations

import pytest

from app.api.v1.routes import acquisition as acq_api
from app.services.acquisition import ops_card_store
from app.services.acquisition.baseline_bench import run_claim_collision_baseline, run_dispatch_baseline
from app.services.acquisition.ops_observability import TenantRateLimiter, acq_rate_limiter, billing_reconcile
from app.services.acquisition.queue_monitor import queue_monitor_report, _queue_of
from app.services.acquisition.sales_collision import claim_inquiry


class _User:
    id = "u1"
    username = "tester"


def _user() -> _User:
    return _User()


def setup_function():
    ops_card_store._by_inquiry.clear()
    ops_card_store._by_id.clear()
    # 重置限流窗口避免串测
    acq_rate_limiter._hits.clear()


def test_rate_limiter_blocks_and_allows():
    lim = TenantRateLimiter(default_limit=3, window_sec=60)
    for i in range(3):
        r = lim.check(tenant_id="demo", action="t")
        assert r["allowed"] is True
    r4 = lim.check(tenant_id="demo", action="t")
    assert r4["allowed"] is False
    assert r4["code"] == "rate_limited"
    assert "限流" in r4["plain"]
    # 另一租户不受影响
    r5 = lim.check(tenant_id="other", action="t")
    assert r5["allowed"] is True
    st = lim.stats()
    assert "demo|t" in st["active"]


def test_rate_limit_api_probe():
    acq_rate_limiter._hits.clear()
    # 强制小窗口：直接改单例 limit 行为 — 用独立 action 名
    for _ in range(3):
        acq_rate_limiter.check(tenant_id="probe-tenant", action="probe_action")
    # 将单例调到已满
    acq_rate_limiter.default_limit = 3
    try:
        resp = acq_api.acquisition_rate_limit_probe(
            acq_api.RateLimitProbeRequest(tenant_id="probe-tenant", action="probe_action", times=1),
            current_user=_user(),
        )
        assert resp["allowed"] is False
        with pytest.raises(Exception) as ei:
            acq_api._rate_limit_or_raise("probe-tenant", action="probe_action")
        assert getattr(ei.value, "status_code", None) == 429 or "429" in str(ei.value) or "限流" in str(ei.value)
    finally:
        acq_rate_limiter.default_limit = 60
        acq_rate_limiter._hits.clear()


def test_billing_reconcile_no_db_honest():
    out = billing_reconcile(None, tenant_id="demo")
    assert out["ok"] is False
    assert "诚实" in out["plain_summary"] or "无数据库" in out["plain_summary"]
    api = acq_api.acquisition_billing_reconcile(tenant_id="demo", current_user=_user(), db=None)
    assert "plain_summary" in api


def test_queue_classifier_and_monitor():
    assert _queue_of("outreach.letter") == "outreach"
    assert _queue_of("hermes_node:order") == "ops"
    assert _queue_of("content.generate") == "content"
    assert _queue_of("") == "default"
    out = queue_monitor_report(None, tenant_id="demo")
    assert out["ok"] is False
    api = acq_api.acquisition_queue_monitor(tenant_id="demo", current_user=_user(), db=None)
    assert "plain_summary" in api


def test_baseline_dispatch_and_claim():
    ops_card_store.materialize(tenant_id="demo", inquiry_id="INQ-BASE-SETUP", owner_user_id="alice")
    card_base = run_dispatch_baseline(ops_store=ops_card_store, n=8)
    assert card_base["n"] == 8
    assert card_base["errors"] == 0
    assert card_base["idempotent_errors"] == 0
    assert card_base["p50_ms"] >= 0
    claim = run_claim_collision_baseline(
        claim_fn=lambda **kw: claim_inquiry(ops_card_store, **kw),
        inquiry_id="INQ-BASE-SETUP",
    )
    assert claim["ok"] is True
    assert claim["second_code"] in ("collision", "already_owner")
    api = acq_api.acquisition_baseline(n=5, current_user=_user())
    assert api["ok"] is True
    assert "基线" in api["plain_summary"]
