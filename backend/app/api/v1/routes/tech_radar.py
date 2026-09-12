"""GEO 技术雷达 API — 定时抓取 + 自动进化"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.admin_auth import get_current_super_admin
from app.core.database import get_db
from app.core.response import success_response
from app.models.user import User


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/tech-radar"
ROUTE_TAGS = ["技术雷达"]

router = APIRouter()


class ApplyFindingsRequest(BaseModel):
    """Tech Radar 发现应用请求"""
    min_score: float = Field(0.5, ge=0.0, le=1.0, description="最低相关性阈值（默认 0.5）")
    categories: list[str] | None = Field(None, description="过滤类别")
    limit_per_source: int = Field(5, ge=1, le=20, description="每源最多条数")


@router.get("/tech-radar")
async def get_tech_radar(
    category: str = Query(None, description="过滤类别: paper|blog|opensource|ai_vendor|whitehat|cn_community"),
    min_relevance: float = Query(0.0, description="最低相关性 0~1"),
    limit: int = Query(5, ge=1, le=20, description="每源最多条数"),
    _user: User = Depends(get_current_super_admin),
):
    """获取 GEO/SEO 技术雷达最新发现"""
    from app.services.geo.tech_radar_fetch import fetch_tech_radar
    categories = [category] if category else None
    result = fetch_tech_radar(categories=categories, limit_per_source=limit, min_relevance=min_relevance)
    return success_response(result)


@router.get("/tech-radar/latest-techniques")
async def get_latest_techniques(
    _user: User = Depends(get_current_super_admin),
):
    """获取高相关性的最新 GEO 技术发现"""
    from app.services.geo.tech_radar_fetch import fetch_latest_geo_techniques
    result = fetch_latest_geo_techniques()
    return success_response(result)


@router.get("/tech-radar/sources")
async def list_sources(
    _user: User = Depends(get_current_super_admin),
):
    """列出所有配置的技术雷达源"""
    from app.services.geo.tech_radar_fetch import RADAR_SOURCES
    sources = [
        {
            "name": s.name,
            "url": s.url,
            "kind": s.kind,
            "category": s.category,
            "description": s.description,
        }
        for s in RADAR_SOURCES
    ]
    return success_response({"sources": sources, "total": len(sources)})


# ── Connection ⑤: Tech Radar → Writing Policy 自动更新 ──

@router.post("/apply-findings")
async def apply_tech_radar_findings(
    request: ApplyFindingsRequest,
    _user: User = Depends(get_current_super_admin),
):
    """抓取 Tech Radar 高相关性发现，自动更新 GEO 写作策略 changelog。

    流程：fetch_tech_radar(min_relevance>=min_score) → update_tactics_from_radar()
    """
    from app.services.geo.tech_radar_fetch import fetch_tech_radar, update_tactics_from_radar
    # 1. 抓取技术雷达
    radar_result = fetch_tech_radar(
        categories=request.categories,
        limit_per_source=request.limit_per_source,
        min_relevance=request.min_score,
    )
    # 2. 将高相关性发现写入 tactics changelog
    update_result = update_tactics_from_radar(
        radar_result.get("items", []),
        min_score=request.min_score,
    )
    return success_response({
        "radar_summary": {
            "items_fetched": radar_result.get("total", 0),
            "sources_ok": radar_result.get("sources_ok", 0),
            "sources_total": radar_result.get("sources_total", 0),
        },
        "tactics_update": update_result,
    })
