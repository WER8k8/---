# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""关键词热度查询、SEMrush 数据网关与谷歌热门排行榜路由。"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.keyword_research_service import (
    SUPPORTED_TARGET_LOCALES,
    analyze_keyword_heat,
    check_zero_volume_guard,
    generate_full_site_seo_blueprint,
    get_google_hot_leaderboard,
    run_wangcai_deerflow_deep_research,
    save_keywords_to_tenant_library,
    transmute_chinese_keyword_to_multilingual,
)
from app.services.tenant_scenario_service import resolve_tenant_id_for_user

ROUTE_PREFIX = "/keyword-research"
ROUTE_TAGS = ["关键词热度查询"]

router = APIRouter()


class KeywordAnalyzeRequest(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=200, description="查询关键词")
    market: str = Field(default="global", description="目标市场: global|me_sea|us_eu|cn")
    target_country: str = Field(default="US", description="目标国家: US|DE|ES|SA|RU|FR|VN")
    target_language: Optional[str] = Field(default=None, description="目标语言: en|de|es|ar|ru|fr|vi")
    category: Optional[str] = Field(default=None, description="行业分类")


class CheckZeroVolumeRequest(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=200, description="待检测关键词")
    target_country: str = Field(default="US", description="目标国家代码: US|DE|ES|SA|RU|FR|VN")


class TransmuteMultilingualRequest(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=200, description="中文产品词或待置换词")
    target_country: Optional[str] = Field(default="US", description="目标国家代码: US|DE|ES|SA|RU|FR|VN")
    target_language: Optional[str] = Field(default=None, description="目标语言代码: en|de|es|ar|ru|fr|vi")


class SaveToLibraryRequest(BaseModel):
    keywords: List[dict[str, Any]] = Field(..., min_length=1, description="待保存关键词列表")


@router.post("/analyze")
def analyze_keyword(
    req: KeywordAnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询指定关键词的热度指数、搜索量、竞争度、趋势折线、区域需求与长尾拓展（含零搜索量熔断检测与多国母语自动置换）。"""
    try:
        result = analyze_keyword_heat(
            db,
            req.keyword,
            market=req.market,
            target_country=req.target_country,
            target_language=req.target_language,
            category=req.category,
        )
        return success_response(data=result, message="关键词热度分析成功")
    except ValueError as e:
        return error_response(400, str(e))
    except Exception as e:
        return error_response(500, f"分析失败: {str(e)}")


@router.post("/check-zero-volume")
def check_zero_volume(
    req: CheckZeroVolumeRequest,
    current_user: User = Depends(get_current_user),
):
    """零搜索量硬性拦截门禁：检测关键词是否为无人搜索的死词，若违规强制推荐 Google 真实高热替代词；输入中文自动执行母语置换。"""
    try:
        guard = check_zero_volume_guard(req.keyword, target_country=req.target_country)
        return success_response(data=guard)
    except Exception as e:
        return error_response(500, f"检测失败: {str(e)}")


@router.post("/transmute-multilingual")
def transmute_multilingual_keywords(
    req: TransmuteMultilingualRequest,
    current_user: User = Depends(get_current_user),
):
    """【多国母语关键词智能自动置换】将中国卖家输入的中文产品意图自动置换为对应国家、对应采购商搜索母语词。"""
    try:
        data = transmute_chinese_keyword_to_multilingual(
            req.keyword,
            target_country=req.target_country or "US",
            target_language=req.target_language,
        )
        return success_response(data=data, message="母语关键词自动置换成功")
    except Exception as e:
        return error_response(500, f"自动置换失败: {str(e)}")


@router.get("/target-locales")
def get_target_locales(
    current_user: User = Depends(get_current_user),
):
    """获取系统支持的海外目标市场与母语国家配置列表。"""
    locales = [
        {
            "code": code,
            "country_name": meta["country_name"],
            "language_code": meta["language_code"],
            "language_name": meta["language_name"],
            "currency": meta["currency"],
            "currency_code": meta["currency_code"],
            "flag": meta["flag"],
        }
        for code, meta in SUPPORTED_TARGET_LOCALES.items()
    ]
    return success_response(data=locales)


@router.get("/google-leaderboard")
def google_leaderboard(
    category: str = Query("all", description="品类: all|insulation|sealing|tiles_stone|doors_windows"),
    current_user: User = Depends(get_current_user),
):
    """调取 Google 官方与 SEMrush 全球外贸关键词热门排行榜（直接抄大词/黄金词）。"""
    try:
        board = get_google_hot_leaderboard(category)
        return success_response(data=board)
    except Exception as e:
        return error_response(500, f"拉取排行榜失败: {str(e)}")


@router.post("/save-to-library")
def save_to_tenant_library(
    req: SaveToLibraryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """将热度挖掘得到的长尾词一键保存到当前租户的专属词库（多租户绝对隔离）。"""
    tenant_id = resolve_tenant_id_for_user(db, current_user)
    if not tenant_id and current_user.role not in ("admin", "super_admin"):
        return error_response(403, "当前用户未关联租户或无权操作专属词库")

    target_tenant_id = tenant_id or "platform"

    try:
        res = save_keywords_to_tenant_library(db, target_tenant_id, req.keywords)
        return success_response(data=res, message=f"成功保存 {res['saved_count']} 个关键词到专属词库")
    except Exception as e:
        return error_response(500, f"保存失败: {str(e)}")


@router.get("/popular-presets")
def get_popular_presets(
    market: str = Query("global", description="市场类型: global|cn"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取建材外贸与产业带高热度预设词，方便租户一键点击探索。"""
    if market == "cn":
        presets = [
            {"category": "绝热保温", "keywords": ["岩棉保温板", "玻璃棉卷毡", "橡塑保温管", "硅酸铝针刺毯"]},
            {"category": "密封配件", "keywords": ["法兰金属缠绕垫", "柔性石墨填料环", "聚四氟乙烯四氟垫", "耐高温盘根"]},
            {"category": "石材建材", "keywords": ["天然大理石大板", "花岗岩路沿石", "仿古地砖瓷砖", "外墙干挂石材"]},
            {"category": "门窗五金", "keywords": ["断桥铝门窗", "不锈钢防火门", "中空钢化玻璃", "重型地弹簧"]},
        ]
    else:
        presets = [
            {"category": "Thermal Insulation", "keywords": ["Rock Wool Board", "Glass Wool Blanket", "Rubber Foam Pipe", "Ceramic Fiber Blanket"]},
            {"category": "Gaskets & Sealing", "keywords": ["Spiral Wound Gasket", "Expanded PTFE Sheet", "Pure Graphite Ring", "High Temp Packing"]},
            {"category": "Stone & Tiles", "keywords": ["Polished Porcelain Tiles", "Natural Granite Slabs", "Calacatta Marble", "Ceramic Wall Tiles"]},
            {"category": "Doors & Windows", "keywords": ["Thermal Break Aluminum Window", "Fire Rated Steel Door", "Insulated Glass Unit", "Curtain Wall System"]},
        ]
    return success_response(data={"market": market, "categories": presets})


class WangcaiAutopilotRequest(BaseModel):
    product_or_topic: str = Field(default="Rock Wool Insulation Board", max_length=300, description="产品或行业主题")
    target_market: str = Field(default="global", description="目标市场: global|me_sea|us_eu|cn")
    target_country: str = Field(default="US", description="首选目标出口国代码: US|DE|ES|SA|RU|FR|VN")
    auto_apply: bool = Field(default=True, description="是否自动注入专属词库与SEO")


@router.post("/wangcai-autopilot")
def wangcai_autopilot_research(
    req: WangcaiAutopilotRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """【旺财 × DeerFlow 2.0 深度研究全自动化托管】
    客户无需后台调研搜索量、询盘数与转化率，由旺财调用 DeerFlow 2.0 自动识别中文产品词，
    自动置换多国母语采购词矩阵，推演潜在转化并一键部署。
    """
    tenant_id = resolve_tenant_id_for_user(db, current_user)
    target_tenant_id = tenant_id or "platform"

    try:
        res = run_wangcai_deerflow_deep_research(
            db,
            target_tenant_id,
            req.product_or_topic,
            auto_apply=req.auto_apply,
            target_market=req.target_market,
            target_country=req.target_country,
        )
        return success_response(data=res, message="旺财 × DeerFlow 2.0 全自动深度研究与多国母语置换已就绪")
    except Exception as e:
        return error_response(500, f"自动化深度研究执行失败: {str(e)}")


class FullSiteBlueprintRequest(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=200, description="产品名称或行业")
    product_parameters: Optional[str] = Field(default="", description="产品核心参数/规格/型号（如密度120kg/m3、厚度50mm、耐火A1级）")
    substitute_products: Optional[str] = Field(default="", description="被替代的传统老产品/老材料（如聚苯板EPS、传统陶粒、加气砖）")
    industry_standards: Optional[str] = Field(default="", description="适用的国际技术标准/认证（如ASTM C578、EN 13501、ISO 9001、CE）")
    customer_faqs: Optional[str] = Field(default="", description="真实外商常见技术疑问/痛点（如极寒耐受、MOQ、包装装箱量）")
    competitor_urls: Optional[List[str]] = Field(default=[], description="可选：对标同行网站域名/链接")
    target_country: str = Field(default="US", description="首选目标出口国代码: US|DE|ES|SA|RU|FR|VN")
    target_market: str = Field(default="global", description="目标市场: global|me_sea|us_eu|cn")


@router.post("/full-site-blueprint")
def create_full_site_blueprint(
    req: FullSiteBlueprintRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """【全站 SEO 关键词布局与避坑拓扑蓝图】
    解决导航纯靠直觉、忽略型号规格长尾、页面过深权重衰减、盲目抄同行等 4 大死穴；
    无同行时启动五维正向推演（应用方案、替代品截流、国际标准、真实FAQ、多国母语），
    生成完整全站 10~14 个页面的扁平化拓扑与落地执行总表。
    """
    tenant_id = resolve_tenant_id_for_user(db, current_user)
    target_tenant_id = tenant_id or "platform"

    try:
        res = generate_full_site_seo_blueprint(
            db,
            target_tenant_id,
            req.product_name,
            product_parameters=req.product_parameters or "",
            substitute_products=req.substitute_products or "",
            industry_standards=req.industry_standards or "",
            customer_faqs=req.customer_faqs or "",
            competitor_urls=req.competitor_urls or [],
            target_country=req.target_country,
            target_market=req.target_market,
        )
        return success_response(data=res, message="全站 SEO 关键词布局与避坑拓扑蓝图生成成功")
    except ValueError as e:
        return error_response(400, str(e))
    except Exception as e:
        return error_response(500, f"蓝图生成失败: {str(e)}")

