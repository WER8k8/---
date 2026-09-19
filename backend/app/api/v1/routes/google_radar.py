# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
谷歌商机大数据与 AI 拓客雷达 API 路由 (Google Intelligence Radar Routes)。
"""

from typing import Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.core.response import success_response
from app.services.google_intelligence import (
    GoogleB2BDorkingEngine,
    GoogleEmailValidator,
    GlobalTradeRadarEngine,
    GoogleEEATSchemaEngine,
)

ROUTE_PREFIX = ""

router = APIRouter(prefix="/google-radar", tags=["谷歌商机大数据雷达"])


class DorkMatrixRequest(BaseModel):
    keyword: str = Field(..., min_length=1, description="品类关键词，如 ceramic tiles, marble")
    country: Optional[str] = Field("Global", description="目标国家，如 Saudi Arabia")


class VerifyEmailRequest(BaseModel):
    email: str = Field(..., description="待验证的海外买家邮箱")


class EEATSchemaRequest(BaseModel):
    brand_name: str = "YouDing"
    product_name: str = "Calacatta Gold Marble Slab"
    description: str = "Premium Italian marble slab for luxury architectural flooring"
    image_url: str = "https://www.youding.com/images/marble-calacatta.jpg"
    price_usd: float = 85.0
    moq: int = 100
    hs_code: str = "6802.91.00"


@router.post("/dork-matrix", summary="谷歌 B2B 全球 Dorking 穿透语法生成")
def generate_dork_matrix(req: DorkMatrixRequest):
    """生成针对海外采购决策人、独立进口商、公开提单和招标书的 4 维穿透搜索语法。"""
    res = GoogleB2BDorkingEngine.generate_dork_matrix(req.keyword, req.country or "Global")
    return success_response(data=res, message="谷歌 Dorking 穿透向量已生成")


@router.post("/verify-email", summary="谷歌级 DNS MX 握手与邮箱可达性预检")
def verify_email(req: VerifyEmailRequest):
    """执行 DNS 解析、一次性高危域名过滤、企业域名判别与投递信誉评分。"""
    res = GoogleEmailValidator.validate_email(req.email)
    return success_response(data=res, message="邮箱连通性校验完成")


@router.get("/trade-flow", summary="全球海关 HS 编码大宗进出口流向雷达")
def get_trade_flow(keyword: str = Query("marble", description="建材品类关键词")):
    """检索对应 HS 编码的全球 Top5 进口国、关税壁垒、准入认证与采购旺季。"""
    res = GlobalTradeRadarEngine.get_market_intelligence(keyword)
    return success_response(data=res, message="全球海关贸易雷达数据已就绪")


@router.post("/eeat-schema", summary="谷歌 EEAT 工业级富媒体结构化数据生成")
def generate_eeat_schema(req: EEATSchemaRequest):
    """为独立站生成秒级被谷歌收录并展现高阶富媒体摘要的 JSON-LD。"""
    product_ld = GoogleEEATSchemaEngine.generate_product_schema(
        brand_name=req.brand_name,
        product_name=req.product_name,
        description=req.description,
        image_url=req.image_url,
        price_usd=req.price_usd,
        moq=req.moq,
        hs_code=req.hs_code,
    )
    faq_ld = GoogleEEATSchemaEngine.generate_faq_schema(req.product_name)
    return success_response(
        data={"product_schema": product_ld, "faq_schema": faq_ld},
        message="谷歌 EEAT 结构化数据生成完成"
    )
