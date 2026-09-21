# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""国内询盘与内贸 CRM 数据模型 (Domestic B2B Inquiries Model)。

独立于外贸漏斗，专为国内工程采购商、区域代理商与批发商设计：
- 支持 RMB 计价与增值税 (13%/3%)、普票/专票区分
- 支持企业微信/微信对接字段与国内货运物流
"""
from __future__ import annotations

import uuid as _uuid_lib
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.sql import func

from app.core.database import Base, UUID_TYPE
from app.models.soft_delete import SoftDeleteMixin


class DomesticInquiry(SoftDeleteMixin, Base):
    """国内询盘模型。"""
    __tablename__ = "domestic_inquiries"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(_uuid_lib.uuid4()))
    tenant_id = Column(String(36), nullable=False, index=True)

    buyer_name = Column(String(200), nullable=False, comment="采购方企业/项目名称")
    buyer_type = Column(
        String(50),
        nullable=False,
        default="engineering",
        index=True,
        comment="买家类型: engineering(工程商), distributor(代理商), wholesaler(批发商)",
    )
    contact_name = Column(String(100), nullable=True, comment="联系人姓名")
    contact_phone = Column(String(50), nullable=True, index=True, comment="联系电话")
    contact_wechat = Column(String(100), nullable=True, comment="微信号/企业微信账号")
    external_userid = Column(String(100), nullable=True, index=True, comment="企业微信外部联系人ID")

    product_category = Column(String(100), nullable=True, default="瓷砖", comment="意向产品品类")
    quantity_m2 = Column(Float, nullable=False, default=0.0, comment="预估工程量(㎡/吨)")
    project_name = Column(String(300), nullable=True, comment="具体落地工程项目名")
    city = Column(String(100), nullable=True, index=True, comment="所在省市/工地地址")
    source_channel = Column(
        String(50),
        nullable=True,
        default="wechat",
        comment="线索渠道: wechat/wecom/baidu/douyin/exhibition/referral",
    )

    stage = Column(
        String(50),
        nullable=False,
        default="inquiry",
        index=True,
        comment="销售阶段: inquiry(来询) -> contacted(已联系) -> quoted(已报价) -> sample(打样) -> deal(成交) -> lost(流失)",
    )
    currency = Column(String(10), nullable=False, default="CNY", comment="结算币种")
    vat_type = Column(String(20), nullable=False, default="general", comment="发票类型: general(普票), special(专票)")
    vat_rate = Column(Float, nullable=False, default=0.13, comment="增值税率")
    logistics_type = Column(String(50), nullable=True, default="domestic_freight", comment="国内物流方式")

    quote_amount_rmb = Column(Float, nullable=True, default=0.0, comment="报价总金额(RMB)")
    won_amount_rmb = Column(Float, nullable=True, default=0.0, comment="最终成交金额(RMB)")
    lost_reason = Column(String(500), nullable=True, comment="丢单/流失主因")
    note = Column(Text, nullable=True, comment="跟进备注")

    # 归因与元数据
    utm_source = Column(String(200), nullable=True, index=True)
    utm_medium = Column(String(120), nullable=True)
    utm_campaign = Column(String(200), nullable=True)
    provenance_metadata = Column(JSON, nullable=True, comment="数据血缘与背调水印")

    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<DomesticInquiry(buyer={self.buyer_name}, type={self.buyer_type}, stage={self.stage})>"
