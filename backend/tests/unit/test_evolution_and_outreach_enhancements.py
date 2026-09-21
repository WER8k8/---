# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""自进化闭环与外贸拓客极智增强单元测试集 (Unit Tests for Evolution & Outreach Enhancements)"""
from __future__ import annotations

import datetime
import pytest

from app.services.acquisition.cadence_engine import OutboundCadenceEngine
from app.services.acquisition.ai_pitch_studio import AIPitchStudio
from app.services.outreach_batch_compensate_service import (
    push_to_dlq,
    get_dlq_items,
)
from app.services.billing.commission_settlement_service import CommissionSettlementService
from app.services.cross_border.fx_hedge_advisor import FXHedgeAdvisor
from app.services.platforms.b2b_platform_inbox_hub import B2BPlatformInboxHub
from app.services.attribution_service import parse_and_bind_utm_to_inquiry


def test_whatsapp_warmup_ladder_and_gate():
    """测试 WhatsApp 账号安全阶梯与门禁拦截。"""
    today = datetime.date.today()

    # 1. 刚注册 1 天的新号 -> 限额 10 条
    gate_new = OutboundCadenceEngine.warmup_gate(
        "+8613800138000",
        account_registered_date=today - datetime.timedelta(days=1),
        sent_today_count=5,
    )
    assert gate_new["daily_limit"] == 10
    assert gate_new["remaining_today"] == 5
    assert gate_new["safe_to_send"] is True
    assert "新账号" in gate_new["warning"]

    # 2. 达到上限时熔断
    gate_limit = OutboundCadenceEngine.warmup_gate(
        "+8613800138000",
        account_registered_date=today - datetime.timedelta(days=1),
        sent_today_count=10,
    )
    assert gate_limit["safe_to_send"] is False
    assert "过载熔断" in gate_limit["warning"]

    # 3. 注册 45 天成熟账号 -> 上限 200 条
    gate_mature = OutboundCadenceEngine.warmup_gate(
        "+8613800138000",
        account_registered_date=today - datetime.timedelta(days=45),
        sent_today_count=150,
    )
    assert gate_mature["daily_limit"] == 200
    assert gate_mature["remaining_today"] == 50
    assert gate_mature["safe_to_send"] is True


def test_spintax_variation_and_randomness():
    """测试 Spintax 变体与 {word1|word2} 动态语法展开。"""
    # 随机多次调用 _spin("greeting")，应覆盖多种问候语
    greetings = {AIPitchStudio._spin("greeting") for _ in range(30)}
    assert len(greetings) >= 2

    # 测试语法树展开
    template = "Hello {Director|Manager|Executive}, we are a {certified|leading|top-tier} manufacturer."
    expanded_set = {AIPitchStudio.apply_spintax(template) for _ in range(30)}
    assert len(expanded_set) > 1
    for text in expanded_set:
        assert "{" not in text and "}" not in text


def test_outreach_dlq_push_and_query():
    """测试死信队列 (DLQ) 推入与查询。"""
    sample_failed = {
        "id": "outreach_task_test_99",
        "reason": "SMTP Connect Timeout",
        "retry_count": 3,
    }
    ok = push_to_dlq(sample_failed)
    assert ok is True

    items = get_dlq_items(limit=10)
    assert any(i.get("id") == "outreach_task_test_99" for i in items)


def test_commission_settlement_service():
    """测试代理商 (3%) 与区域合伙人 (2%) 双层分润结算。"""
    svc = CommissionSettlementService(db=None)

    res = svc.settle_on_deal_won(
        order_id="ORD-2026-US-8890",
        deal_amount=50000.0,  # $50,000 大单
        currency="USD",
        agent_node_id="agent_node_shanghai_01",
        partner_node_id="partner_node_east_china_01",
        note="全款信用证交单成功",
    )
    assert res["status"] == "settlements_generated"
    assert res["settlements_count"] == 2

    agent_item = next(s for s in res["settlements"] if s["role"] == "agent")
    partner_item = next(s for s in res["settlements"] if s["role"] == "partner")

    assert agent_item["commission_amount"] == 1500.0  # $50,000 * 3%
    assert partner_item["commission_amount"] == 1000.0 # $50,000 * 2%
    assert res["total_commission_amount"] == 2500.0


def test_fx_hedge_advisor_risk_and_pi_clauses():
    """测试外汇汇率波动敏感度与多语种 PI 保护条款生成。"""
    # 正常小波动 (1%)
    eval_safe = FXHedgeAdvisor.evaluate_fx_risk(
        order_amount=100000.0,
        currency="USD",
        quoted_rate=7.20,
        current_rate=7.25,
    )
    assert eval_safe["risk_level"] == "safe"
    assert eval_safe["pnl_cny"] == 5000.0

    # 剧烈贬值 (5%) 触发紧急预警
    eval_crit = FXHedgeAdvisor.evaluate_fx_risk(
        order_amount=100000.0,
        currency="USD",
        quoted_rate=7.20,
        current_rate=6.84,
    )
    assert eval_crit["risk_level"] == "critical"
    assert "紧急锁汇机制" in eval_crit["warning"]

    # 多语种 PI 锁汇条款生成
    clauses = FXHedgeAdvisor.generate_pi_fx_clause(currency="USD", base_rate=7.235)
    assert "Exchange Rate Lock" in clauses["en"]
    assert "سعر الصرف" in clauses["ar"]
    assert "Cláusula de Tipo de Cambio" in clauses["es"]
    assert "汇率锁定保护条款" in clauses["zh"]


def test_b2b_platform_inbox_hub():
    """测试 Alibaba 和 Made-in-China 原始询盘的标准化清洗与归入。"""
    alibaba_raw = {
        "rfq_id": "ali_rfq_99120",
        "buyer_company": "Bin Laden Construction Group",
        "country": "SA",
        "email": "procurement@binladen.sa",
        "subject": "Need 30 containers of 600x600 porcelain tiles",
        "quantity": "30x20GP",
    }
    res_ali = B2BPlatformInboxHub.ingest_platform_inquiry(
        platform="alibaba",
        raw_payload=alibaba_raw,
        db=None,
    )
    assert res_ali["success"] is True
    assert res_ali["platform"] == "alibaba"
    lead = res_ali["standardized_lead"]
    assert lead["buyer_name"] == "Bin Laden Construction Group"
    assert lead["buyer_country"] == "SA"
    assert lead["target_quantity"] == "30x20GP"


def test_utm_binding_to_inquiry_entity():
    """测试 UTM 标记动态绑定与主要渠道分类。"""
    class MockInquiry:
        utm_source = None
        utm_medium = None
        utm_campaign = None
        utm_content = None
        utm_term = None
        attribution_channel = None

    inq = MockInquiry()
    parse_and_bind_utm_to_inquiry(
        inq,
        {
            "utm_source": "google_cpc",
            "utm_medium": "seo_search",
            "utm_campaign": "saudi_tiles_2026",
            "utm_content": "art_porcelain_88",
        },
    )
    assert inq.utm_source == "google_cpc"
    assert inq.utm_campaign == "saudi_tiles_2026"
    assert inq.attribution_channel == "seo"
