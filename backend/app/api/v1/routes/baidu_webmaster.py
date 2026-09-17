# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""百度站长工具 API 路由"""
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.models.user import User
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
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
):
    """获取百度搜索词数据（流量与关键词）"""
    result = await BaiduWebmasterService.get_search_queries(site_url, token, days)
    if not result["success"]:
        return error_response(503, result.get("message", "查询失败"))
    return success_response(data=result["data"], message=result.get("message"))


@router.post("/baidu/url-push")
async def push_urls(
    site_url: str = Query(..., description="站点URL"),
    urls: str = Query(..., description="待推送URL，多个用英文逗号分隔"),
    token: Optional[str] = Query(None, description="百度站长平台site_token"),
    batch_size: int = Query(10, ge=1, le=20, description="单批上限"),
    current_user: User = Depends(get_current_user),
):
    """URL 级增量推送（新页面秒级送审，不止 sitemap）"""
    url_list = [u.strip() for u in urls.split(",") if u.strip()]
    result = await BaiduWebmasterService.push_urls(site_url, url_list, token, batch_size)
    if not result["success"]:
        return error_response(503, result.get("message", "推送失败"))
    return success_response(data=result["data"], message=result.get("message"))
