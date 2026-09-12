"""百度站长工具 API 路由"""
from typing import Optional

from fastapi import APIRouter, Query

from app.core.response import error_response, success_response
from app.services.baidu_webmaster_service import BaiduWebmasterService


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""
ROUTE_TAGS = ["百度站长工具"]

router = APIRouter()


@router.post("/baidu/sitemap/submit")
async def submit_sitemap(
    site_url: str = Query(..., description="站点URL"),
    sitemap_url: str = Query(..., description="Sitemap完整URL"),
    token: Optional[str] = Query(None, description="百度站长平台site_token"),
):
    """提交 sitemap 到百度站长平台"""
    result = await BaiduWebmasterService.submit_sitemap(site_url, sitemap_url, token)
    if not result["success"]:
        return error_response(503, result.get("message", "提交失败"))
    return success_response(data=result["data"], message=result.get("message"))


@router.get("/baidu/index-count")
async def get_index_count(
    site_url: str = Query(..., description="站点URL"),
    token: Optional[str] = Query(None, description="百度站长平台site_token"),
):
    """查询百度索引量"""
    result = await BaiduWebmasterService.get_index_count(site_url, token)
    if not result["success"]:
        return error_response(503, result.get("message", "查询失败"))
    return success_response(data=result["data"], message=result.get("message"))


@router.get("/baidu/search-queries")
async def get_search_queries(
    site_url: str = Query(..., description="站点URL"),
    token: Optional[str] = Query(None, description="百度站长平台site_token"),
    days: int = Query(30, ge=1, le=90, description="统计天数"),
):
    """获取百度搜索词数据（流量与关键词）"""
    result = await BaiduWebmasterService.get_search_queries(site_url, token, days)
    if not result["success"]:
        return error_response(503, result.get("message", "查询失败"))
    return success_response(data=result["data"], message=result.get("message"))
