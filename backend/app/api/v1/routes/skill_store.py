# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""技能商店 API — 参考 CocoLoop Skill Store 体系。

提供技能搜索、筛选、安全审核、精选集合等功能。
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.security import get_current_user, require_admin
from app.models.user import User
from app.services.ubrain.skill_audit_service import (
    analyze_skill_risk,
    get_featured_collections,
    get_skill_catalog_with_security,
    get_top_rated_skills,
    scan_skill_code,
    search_skills,
)

ROUTE_PREFIX = ""
router = APIRouter(prefix="/skill-store", tags=["技能商店"])


@router.get("/marketplace/summary")
async def marketplace_summary():
    """统一插件+技能市场汇总 — 合并 skill_store 与旺财插件数据。"""
    from app.services.hermes.registry import list_plugins, public_market_item, catalog_meta

    skills = get_skill_catalog_with_security()
    plugins = [public_market_item(p) for p in list_plugins(visibility="public")]
    return {
        "skills": {"items": skills, "count": len(skills)},
        "plugins": {"items": plugins, "count": len(plugins), "meta": catalog_meta()},
        "total": len(skills) + len(plugins),
    }


@router.get("/catalog")
async def get_skill_catalog():
    """获取完整技能目录（含安全信息）"""
    return get_skill_catalog_with_security()


@router.get("/skills")
async def search_skill_list(
    query: Annotated[str, Query(description="搜索关键词")] = "",
    risk_level: Annotated[str, Query(description="风险等级筛选: S/A/B/C/D")] = "",
    audit_status: Annotated[str, Query(description="审核状态筛选: approved/partial/pending/rejected")] = "",
    group_id: Annotated[str, Query(description="分组ID筛选")] = "",
    sort_by: Annotated[str, Query(description="排序字段: rating/users/name")] = "rating",
    sort_order: Annotated[str, Query(description="排序方向: asc/desc")] = "desc",
):
    """搜索和筛选技能"""
    skills = search_skills(
        query=query,
        risk_level=risk_level,
        audit_status=audit_status,
        group_id=group_id,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return {"skills": skills, "count": len(skills)}


@router.get("/skills/{skill_id}")
async def get_skill_detail(skill_id: str):
    """获取技能详情（含安全分析）"""
    return analyze_skill_risk(skill_id)


@router.post("/skills/{skill_id}/risk-analyze")
async def analyze_skill(skill_id: str, _admin: User = Depends(require_admin)):
    """分析技能安全风险"""
    return analyze_skill_risk(skill_id)


@router.post("/code-scan")
async def scan_code(
    code: dict[str, str],
    current_user: User = Depends(get_current_user),
):
    """扫描技能代码安全风险（需要登录）"""
    skill_code = code.get("code", "")
    return scan_skill_code(skill_code)


@router.get("/featured")
async def get_featured():
    """获取精选技能集合"""
    return {"collections": get_featured_collections()}


@router.get("/top-rated")
async def get_top_rated(
    limit: Annotated[int, Query(description="返回数量")] = 5,
):
    """获取评分最高的技能"""
    return {"skills": get_top_rated_skills(limit=limit)}


@router.get("/risk-levels")
async def get_risk_levels():
    """获取风险等级说明"""
    return {
        "levels": {
            "S": {"description": "最高安全等级，经过严格审核，无任何安全风险", "color": "#52c41a"},
            "A": {"description": "高安全等级，经过审核，基本无安全风险", "color": "#1890ff"},
            "B": {"description": "中等安全等级，存在一些潜在风险，建议谨慎使用", "color": "#faad14"},
            "C": {"description": "较低安全等级，存在明显风险，需要人工审核", "color": "#ff7875"},
            "D": {"description": "危险等级，存在严重安全风险，禁止使用", "color": "#ff4d4f"},
        }
    }
