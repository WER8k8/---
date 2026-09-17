# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""IndexNow API 路由与密钥验证端点。"""

from typing import List
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from app.core.response import success_response
from app.services.seo.indexnow_service import IndexNowService, DEFAULT_INDEXNOW_KEY

router = APIRouter(prefix="/indexnow", tags=["IndexNow极速收录"])


class IndexNowSubmitRequest(BaseModel):
    urls: List[str]
    host: str = ""


@router.post("/submit")
async def submit_indexnow_urls(req: IndexNowSubmitRequest, request: Request):
    """手动或异步调用 IndexNow 提交新 URL 列表。"""
    host = req.host or request.headers.get("x-forwarded-host") or request.headers.get("host") or "www.youdingjiancai.com"
    svc = IndexNowService()
    result = await svc.submit_urls(host, req.urls)
    return success_response(data=result, message="IndexNow 广播完成")


@router.get("/key.txt", response_class=Response)
@router.get("/indexnow-key.txt", response_class=Response)
async def get_indexnow_key():
    """返回 IndexNow 官方要求的验证密钥文件。"""
    return Response(
        content=DEFAULT_INDEXNOW_KEY,
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "public, max-age=86400"},
    )
