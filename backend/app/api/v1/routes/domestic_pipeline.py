# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""国内建材获客与 CRM 管道 API 路由 (Domestic Acquisition & CRM Pipeline Routes)。

涵盖国内工程集采商、区域代理商与批发商全流程：
1. 国内询盘入库与阶段白名单推进
2. 增值税 RMB 工业核价（13%/3%、专票抵扣/普票包干）
3. 企微/微信智能跟进话术生成与多维客群标签
4. 国内商业漏斗全景转化率与管道指标
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.response import success_response
from app.services.domestic import (
    DomesticInquiryService,
    DomesticQuoteService,
    WeCOMCrmConnector,
    DomesticDealPipeline,
)

ROUTE_PREFIX = ""

router = APIRouter(prefix="/domestic-pipeline", tags=["国内获客与内贸商机中枢"])


# ── 请求与响应 Pydantic 模型 ─────────────────────────────────────
class CreateDomesticInquiryRequest(BaseModel):
    tenant_id: Optional[str] = Field("default_tenant", description="租户ID")
    buyer_name: str = Field(..., min_length=1, description="采购企业/项目名称，如万达工装集采部")
    buyer_type: Optional[str] = Field("engineering", description="买家类型 (engineering/distributor/wholesaler)")
    contact_name: Optional[str] = Field("", description="联系人姓名")
    contact_phone: Optional[str] = Field("", description="联系手机号")
    contact_wechat: Optional[str] = Field("", description="微信号/企业微信账号")
    external_userid: Optional[str] = Field("", description="企业微信外部联系人ID")
    product_category: Optional[str] = Field("瓷砖", description="产品品类")
    quantity_m2: Optional[float] = Field(0.0, ge=0, description="预估采购量(㎡)")
    project_name: Optional[str] = Field("", description="工程项目名")
    city: Optional[str] = Field("", description="所在城市")
    source_channel: Optional[str] = Field("wechat", description="线索渠道 (wechat/wecom/baidu/douyin/exhibition)")
    vat_type: Optional[str] = Field("general", description="开票类型 (general普票 / special专票)")
    vat_rate: Optional[float] = Field(0.13, description="增值税率")
    note: Optional[str] = Field("", description="初始跟进备注")


class AdvanceStageRequest(BaseModel):
    inquiry_id: str = Field(..., description="国内询盘ID")
    new_stage: str = Field(..., description="目标阶段 (contacted/quoted/sample/deal/lost)")
    quote_amount_rmb: Optional[float] = Field(None, description="报价总金额(RMB)")
    won_amount_rmb: Optional[float] = Field(None, description="最终成交金额(RMB)")
    lost_reason: Optional[str] = Field(None, description="丢单原因")
    note: Optional[str] = Field("", description="跟进推进备注")


class GenerateRmbQuoteRequest(BaseModel):
    product_category: Optional[str] = Field("ceramic_tile", description="建材品类 (ceramic_tile/natural_stone/sintered_stone/sand_gravel)")
    quantity_m2: float = Field(..., gt=0, description="工程采购面积(㎡)")
    unit_price_rmb: float = Field(..., gt=0, description="出厂基准单价(元/㎡)")
    surface_treatment: Optional[str] = Field("polished", description="表面加工工艺 (polished/matte/antique/flamed/bush_hammered)")
    thickness_mm: Optional[int] = Field(10, description="板材厚度(mm)")
    vat_type: Optional[str] = Field("general", description="开票类型 (general普票 / special专票)")
    logistics_km: Optional[float] = Field(500.0, ge=0, description="国内干线运距(公里)")
    buyer_type: Optional[str] = Field("engineering", description="买家客户类型 (engineering/distributor/wholesaler)")


class WecomFollowupRequest(BaseModel):
    buyer_name: str = Field(..., description="买家单位/公司名")
    buyer_type: Optional[str] = Field("engineering", description="买家类型")
    product_category: Optional[str] = Field("瓷砖", description="产品品类")
    quote_amount: Optional[float] = Field(0.0, description="已报总金额")
    stage: Optional[str] = Field("contacted", description="当前跟进阶段")
    contact_name: Optional[str] = Field("", description="联系人称谓")


class TagLeadRequest(BaseModel):
    external_userid: str = Field(..., description="企业微信外部联系人ID")
    buyer_type: Optional[str] = Field("engineering", description="买家类型")
    city: Optional[str] = Field("", description="城市")
    project_name: Optional[str] = Field("", description="工程项目名")
    quantity_m2: Optional[float] = Field(0.0, description="工程采购面积")


# ── 端点实现 ───────────────────────────────────────────────────
@router.post("/create-inquiry", summary="创建国内建材询盘")
async def create_domestic_inquiry(
    payload: CreateDomesticInquiryRequest,
    db: Session = Depends(get_db),
):
    """创建国内询盘档案（工程商/代理商/批发商独立漏斗）。"""
    svc = DomesticInquiryService(db)
    result = svc.create_domestic_inquiry(
        tenant_id=payload.tenant_id or "default_tenant",
        buyer_name=payload.buyer_name,
        buyer_type=payload.buyer_type or "engineering",
        contact_name=payload.contact_name or "",
        contact_phone=payload.contact_phone or "",
        contact_wechat=payload.contact_wechat or "",
        external_userid=payload.external_userid or "",
        product_category=payload.product_category or "瓷砖",
        quantity_m2=payload.quantity_m2 or 0.0,
        project_name=payload.project_name or "",
        city=payload.city or "",
        source_channel=payload.source_channel or "wechat",
        vat_type=payload.vat_type or "general",
        vat_rate=payload.vat_rate or 0.13,
        note=payload.note or "",
    )
    return success_response(data=result)


@router.post("/advance-stage", summary="推进国内询盘阶段")
async def advance_stage(
    payload: AdvanceStageRequest,
    db: Session = Depends(get_db),
):
    """推进国内询盘生命周期阶段，并在赢单/丢单时自动触发自进化经验环。"""
    svc = DomesticInquiryService(db)
    result = svc.advance_stage(
        inquiry_id=payload.inquiry_id,
        new_stage=payload.new_stage,
        quote_amount_rmb=payload.quote_amount_rmb,
        won_amount_rmb=payload.won_amount_rmb,
        lost_reason=payload.lost_reason,
        note=payload.note or "",
    )
    return success_response(data=result)


@router.post("/rmb-quote", summary="国内建材增值税 RMB 工业核价")
async def generate_rmb_quote(payload: GenerateRmbQuoteRequest):
    """计算含税/不含税、专票/普票、运费与工艺加价的国内 RMB 报价单。"""
    result = DomesticQuoteService.generate_rmb_quote(
        product_category=payload.product_category or "ceramic_tile",
        quantity_m2=payload.quantity_m2,
        unit_price_rmb=payload.unit_price_rmb,
        surface_treatment=payload.surface_treatment or "polished",
        thickness_mm=payload.thickness_mm or 10,
        vat_type=payload.vat_type or "general",
        logistics_km=payload.logistics_km or 0.0,
        buyer_type=payload.buyer_type or "engineering",
    )
    return success_response(data=result)


@router.post("/wecom-followup", summary="生成企业微信/微信跟进高情商话术")
async def generate_wecom_followup(payload: WecomFollowupRequest):
    """根据国内商务习惯与跟进阶段，生成企微/微信即时沟通话术。"""
    result = WeCOMCrmConnector.generate_domestic_followup_script(
        buyer_name=payload.buyer_name,
        buyer_type=payload.buyer_type or "engineering",
        product_category=payload.product_category or "瓷砖",
        quote_amount=payload.quote_amount or 0.0,
        stage=payload.stage or "contacted",
        contact_name=payload.contact_name or "",
    )
    return success_response(data=result)


@router.post("/tag-lead", summary="为企业微信联系人打标")
async def tag_domestic_lead(payload: TagLeadRequest):
    """根据采购商类型、工程规模、地域自动对企微客户打标。"""
    result = WeCOMCrmConnector.tag_domestic_lead(
        external_userid=payload.external_userid,
        buyer_type=payload.buyer_type or "engineering",
        city=payload.city or "",
        project_name=payload.project_name or "",
        quantity_m2=payload.quantity_m2 or 0.0,
    )
    return success_response(data=result)


@router.get("/summary", summary="国内商机管道与漏斗全景统计")
async def get_pipeline_summary(
    tenant_id: Optional[str] = Query("", description="租户ID"),
    db: Session = Depends(get_db),
):
    """获取国内建材商机转化漏斗与统计数据。"""
    pipe = DomesticDealPipeline(db)
    result = pipe.get_pipeline_summary(tenant_id=tenant_id or "")
    return success_response(data=result)
