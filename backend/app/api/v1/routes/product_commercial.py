# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""产品商业化 API — FIX-74~81

- 代理体系
- 模板市场
- 行业解决方案
- 代运营服务
- 白标方案
- 客户成功
- 增长引擎
- 游戏化
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, Query

from app.core.security import get_current_user
from app.core.response import success_response
from app.services.ubrain.product_commercial_service import (
    agent_system_service,
    template_marketplace_service,
    industry_solution_service,
    managed_service_service,
    white_label_service,
    customer_success_service,
    growth_engine_service,
    gamification_service,
)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""
ROUTE_TAGS = ["产品商业化"]

router = APIRouter(prefix="/product-commercial", tags=["产品商业化"])


# ═══════════════════════════════════════════════════════════
# FIX-74: 代理体系
# ═══════════════════════════════════════════════════════════

@router.post("/agent/register")
def register_agent(
    user_id: str = Body(...),
    company_name: str = Body(...),
    region: str = Body(...),
    current_user=Depends(get_current_user),
):
    """注册代理。"""
    result = agent_system_service.register_agent(user_id, company_name, region)
    return success_response(data=result)


@router.post("/agent/commission")
def calculate_commission(
    user_id: str = Body(...),
    sale_amount: float = Body(...),
    current_user=Depends(get_current_user),
):
    """计算代理佣金。"""
    result = agent_system_service.calculate_commission(user_id, sale_amount)
    return success_response(data=result)


@router.get("/agent/report/{user_id}")
def get_agent_report(user_id: str, current_user=Depends(get_current_user)):
    """获取代理报告。"""
    result = agent_system_service.get_agent_report(user_id)
    return success_response(data=result)


@router.get("/agent/tiers")
def get_agent_tiers(current_user=Depends(get_current_user)):
    """获取代理层级。"""
    tiers = [
        {"name": t.name, "commission_rate": t.commission_rate,
         "min_monthly_revenue": t.min_monthly_revenue, "benefits": t.benefits}
        for t in agent_system_service.TIERS
    ]
    return success_response(data={"tiers": tiers})


# ═══════════════════════════════════════════════════════════
# FIX-75: 模板市场
# ═══════════════════════════════════════════════════════════

@router.get("/templates")
def list_templates(
    category: str = Query(""),
    industry: str = Query(""),
    language: str = Query(""),
    current_user=Depends(get_current_user),
):
    """列出模板。"""
    results = template_marketplace_service.list_templates(category, industry, language)
    return success_response(data={"templates": results})


@router.get("/templates/{template_id}")
def get_template(template_id: str, current_user=Depends(get_current_user)):
    """获取模板详情。"""
    result = template_marketplace_service.get_template(template_id)
    return success_response(data=result)


# ═══════════════════════════════════════════════════════════
# FIX-76: 行业解决方案
# ═══════════════════════════════════════════════════════════

@router.get("/solutions")
def list_solutions(current_user=Depends(get_current_user)):
    """列出行业解决方案。"""
    return success_response(data={"solutions": industry_solution_service.list_solutions()})


@router.get("/solutions/{industry}")
def get_solution(industry: str, current_user=Depends(get_current_user)):
    """获取指定行业方案。"""
    result = industry_solution_service.get_solution(industry)
    return success_response(data=result)


# ═══════════════════════════════════════════════════════════
# FIX-77: 代运营服务
# ═══════════════════════════════════════════════════════════

@router.get("/managed-service/packages")
def list_managed_packages(current_user=Depends(get_current_user)):
    """列取代运营套餐。"""
    return success_response(data={"packages": managed_service_service.list_packages()})


@router.get("/managed-service/packages/{package_id}")
def get_managed_package(package_id: str, current_user=Depends(get_current_user)):
    """获取代运营套餐详情。"""
    result = managed_service_service.get_package(package_id)
    return success_response(data=result)


# ═══════════════════════════════════════════════════════════
# FIX-78: 白标方案
# ═══════════════════════════════════════════════════════════

@router.post("/white-label/config")
def generate_white_label_config(
    brand_name: str = Body(...),
    primary_color: str = Body(...),
    logo_url: str = Body(...),
    domain: str = Body(...),
    current_user=Depends(get_current_user),
):
    """生成白标品牌配置。"""
    result = white_label_service.generate_brand_config(brand_name, primary_color, logo_url, domain)
    return success_response(data=result)


@router.get("/white-label/pricing")
def get_white_label_pricing(current_user=Depends(get_current_user)):
    """获取白标定价。"""
    return success_response(data=white_label_service.get_pricing())


# ═══════════════════════════════════════════════════════════
# FIX-79: 客户成功
# ═══════════════════════════════════════════════════════════

@router.post("/customer-success/health-score")
def calculate_health_score(
    tenant_data: dict[str, Any] = Body(...),
    current_user=Depends(get_current_user),
):
    """计算租户健康评分。"""
    result = customer_success_service.calculate_health_score(tenant_data)
    return success_response(data=result)


@router.post("/customer-success/ltv")
def calculate_ltv(
    monthly_revenue: float = Body(...),
    churn_rate: float = Body(...),
    gross_margin: float = Body(0.7),
    current_user=Depends(get_current_user),
):
    """计算客户 LTV。"""
    result = customer_success_service.calculate_ltv(monthly_revenue, churn_rate, gross_margin)
    return success_response(data=result)


# ═══════════════════════════════════════════════════════════
# FIX-80: 增长引擎
# ═══════════════════════════════════════════════════════════

@router.get("/growth/community")
def get_community_strategy(current_user=Depends(get_current_user)):
    """获取社区建设策略。"""
    return success_response(data=growth_engine_service.get_community_strategy())


@router.get("/growth/content")
def get_content_marketing_plan(current_user=Depends(get_current_user)):
    """获取内容营销计划。"""
    return success_response(data=growth_engine_service.get_content_marketing_plan())


@router.get("/growth/free-tools")
def get_free_tools(current_user=Depends(get_current_user)):
    """获取免费工具列表。"""
    return success_response(data={"tools": growth_engine_service.get_free_tools()})


# ═══════════════════════════════════════════════════════════
# FIX-81: 游戏化
# ═══════════════════════════════════════════════════════════

@router.post("/gamification/points")
def award_points(
    user_id: str = Body(...),
    action: str = Body(...),
    points: int = Body(10),
    current_user=Depends(get_current_user),
):
    """奖励积分。"""
    result = gamification_service.award_points(user_id, action, points)
    return success_response(data=result)


@router.post("/gamification/badges")
def award_badge(
    user_id: str = Body(...),
    badge_id: str = Body(...),
    current_user=Depends(get_current_user),
):
    """授予徽章。"""
    result = gamification_service.award_badge(user_id, badge_id)
    return success_response(data=result)


@router.get("/gamification/user/{user_id}")
def get_user_gamification(user_id: str, current_user=Depends(get_current_user)):
    """获取用户游戏化数据。"""
    result = gamification_service.get_user_gamification(user_id)
    return success_response(data=result)


@router.get("/gamification/leaderboard")
def get_leaderboard(
    limit: int = Query(10, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    """获取排行榜。"""
    result = gamification_service.get_leaderboard(limit)
    return success_response(data={"leaderboard": result})


@router.get("/gamification/badges")
def get_all_badges(current_user=Depends(get_current_user)):
    """获取所有徽章定义。"""
    return success_response(data={"badges": gamification_service.BADGES})