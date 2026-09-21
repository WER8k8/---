# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""国内获客与内贸商机闭环服务包 (Domestic Acquisition & CRM Package)。"""
from __future__ import annotations

from app.services.domestic.domestic_inquiry_service import (
    DomesticBuyerType,
    DomesticInquiryService,
    DomesticInquiryStage,
)
from app.services.domestic.domestic_quote_service import DomesticQuoteService
from app.services.domestic.wecom_crm_connector import WeCOMCrmConnector
from app.services.domestic.domestic_deal_pipeline import DomesticDealPipeline

__all__ = [
    "DomesticBuyerType",
    "DomesticInquiryService",
    "DomesticInquiryStage",
    "DomesticQuoteService",
    "WeCOMCrmConnector",
    "DomesticDealPipeline",
]
