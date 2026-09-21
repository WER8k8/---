# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""国内建材获客与 CRM 管道单元测试集 (Unit Tests for Domestic Pipeline)"""
from __future__ import annotations

import pytest
from app.services.domestic import (
    DomesticInquiryService,
    DomesticInquiryStage,
    DomesticBuyerType,
    DomesticQuoteService,
    WeCOMCrmConnector,
    DomesticDealPipeline,
)


def test_domestic_inquiry_creation_and_stage():
    """测试国内询盘创建与阶段白名单推进。"""
    svc = DomesticInquiryService(db=None)

    created = svc.create_domestic_inquiry(
        tenant_id="tenant_dom_01",
        buyer_name="华润置地工装集采部",
        buyer_type="engineering",
        contact_name="张总监",
        contact_phone="13800138000",
        product_category="岩板",
        quantity_m2=5000,
        city="深圳",
        vat_type="special",
    )
    assert created["success"] is True
    assert created["buyer_type"] == "engineering"
    assert created["stage"] == DomesticInquiryStage.INQUIRY.value
    assert created["currency"] == "CNY"
    assert created["vat_type"] == "special"

    # 推进到已报价
    adv1 = svc.advance_stage(
        created["inquiry_id"],
        new_stage="quoted",
        quote_amount_rmb=450000.0,
        note="已发送专票工程核价单",
    )
    assert adv1["success"] is True
    assert adv1["new_stage"] == "quoted"

    # 推进到无效阶段拦截
    bad = svc.advance_stage(created["inquiry_id"], new_stage="unknown_invalid_stage")
    assert bad["success"] is False
    assert "无效" in bad["reason"]

    # 推进到成交 (Deal)
    adv_deal = svc.advance_stage(
        created["inquiry_id"],
        new_stage="deal",
        won_amount_rmb=438000.0,
        note="首笔 30% 订金已到账",
    )
    assert adv_deal["success"] is True
    assert adv_deal["new_stage"] == "deal"


def test_domestic_quote_service_special_vat():
    """测试增值税专用发票 (13%) 抵扣核价。"""
    res = DomesticQuoteService.generate_rmb_quote(
        product_category="ceramic_tile",
        quantity_m2=2000.0,
        unit_price_rmb=90.0,
        surface_treatment="matte",  # 哑光 +3 元
        thickness_mm=12,            # 12mm 增加 3%
        vat_type="special",
        logistics_km=400.0,
        buyer_type="engineering",   # 92 折
    )
    assert res["currency"] == "CNY"
    assert res["vat_type"] == "special"
    assert res["vat_rate"] == 0.13
    assert res["surface_fee_per_m2"] == 3.0
    assert res["thickness_factor"] > 1.0
    assert res["total_net_amount"] > 0
    assert res["total_vat_amount"] > 0
    assert res["grand_total_rmb"] == pytest.approx(res["total_net_amount"] + res["total_vat_amount"], rel=1e-2)
    assert "专用发票" in res["invoice_description"]
    assert "30% 预付款" in res["payment_terms"]


def test_domestic_quote_service_general_vat_wholesaler():
    """测试增值税普通发票与批发商大宗折扣。"""
    res = DomesticQuoteService.generate_rmb_quote(
        product_category="sand_gravel",
        quantity_m2=1000.0,
        unit_price_rmb=50.0,
        vat_type="general",
        buyer_type="wholesaler", # 85 折
    )
    assert res["vat_rate"] == 0.03  # 砂石骨料简易征收 3%
    assert res["buyer_discount_rate"] == 0.85
    assert "普通发票" in res["invoice_description"]


def test_wecom_crm_connector_tagging_and_script():
    """测试企微打标与分阶段跟进话术生成。"""
    tags_res = WeCOMCrmConnector.tag_domestic_lead(
        "wm_usr_9981",
        buyer_type="engineering",
        city="成都市",
        project_name="天府金融中心幕墙工程",
        quantity_m2=65000,
    )
    assert tags_res["status"] == "synchronized"
    assert "工程集采总包" in tags_res["tags_assigned"]
    assert "地区:成都市" in tags_res["tags_assigned"]
    assert any("大型重点工程" in t for t in tags_res["tags_assigned"])

    script_quoted = WeCOMCrmConnector.generate_domestic_followup_script(
        buyer_name="四川华西建设",
        buyer_type="engineering",
        product_category="通体大理石瓷砖",
        quote_amount=880000.0,
        stage="quoted",
        contact_name="李工",
    )
    assert "李工" in script_quoted["script"]
    assert "同窑炉编号" in script_quoted["script"]
    assert "880,000.00" in script_quoted["script"]

    script_deal = WeCOMCrmConnector.generate_domestic_followup_script(
        buyer_name="四川华西建设",
        stage="deal",
        contact_name="李工",
    )
    assert "1v1 专属履约服务群" in script_deal["script"]


def test_domestic_deal_pipeline_summary():
    """测试商机管道指标统计。"""
    pipe = DomesticDealPipeline(db=None)
    summary = pipe.get_pipeline_summary()
    assert summary["currency"] == "CNY"
    assert "stage_funnel" in summary
    assert "quote_conversion_rate" in summary
    assert summary["total_leads"] > 0
