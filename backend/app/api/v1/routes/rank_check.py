"""关键词排名查询 API 路由 — 对接 rank_checker.py 真实爬虫"""
from typing import List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.core.response import success_response
from app.services.rank_checker import RankChecker


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""
ROUTE_TAGS = ["关键词排名"]

router = APIRouter(tags=["关键词排名"])


class RankCheckResponse(BaseModel):
    keyword: str
    engine: str
    domain: str
    best_rank: Optional[int] = None
    total_results: int = 0
    is_simulated: bool = False
    checked_at: Optional[str] = None
    error: Optional[str] = None
    results: List[dict] = []


class BatchRankCheckRequest(BaseModel):
    keywords: List[str] = Field(..., min_length=1, max_length=50, description="关键词列表")
    domain: str = Field(default="youding.com", description="目标域名")
    engines: Optional[List[str]] = Field(default=None, description="搜索引擎列表")
    max_pages: int = Field(default=5, ge=1, le=10, description="最大查询页数")


@router.get("/rank/check", response_model=RankCheckResponse)
async def check_rank(
    keyword: str = Query(..., description="搜索关键词"),
    domain: str = Query("youding.com", description="目标域名"),
    engine: str = Query("baidu", description="搜索引擎 (baidu/google/bing)"),
    max_pages: int = Query(5, ge=1, le=10, description="最大查询页数"),
):
    """查询单个关键词在指定搜索引擎的排名（真实爬取，失败则降级模拟数据）"""
    result = RankChecker.check(keyword, domain, engine, max_pages)
    return success_response(data=result.to_dict())


@router.post("/rank/batch-check")
async def batch_check_rank(request: BatchRankCheckRequest):
    """批量查询关键词排名"""
    results = RankChecker.batch_check(
        keywords=request.keywords,
        domain=request.domain,
        engines=request.engines,
        max_pages=request.max_pages,
    )
    return success_response(
        data=[r.to_dict() for r in results],
        total=len(results),
    )
