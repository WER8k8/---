# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""SEO Backend 反向代理 — 统一 API 网关

将 seo-backend (Express/Node.js :3000) 的请求代理到 FastAPI，
前端只需访问一个后端地址。
"""

import os

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from app.core.admin_auth import get_current_super_admin
from app.core.response import success_response

router = APIRouter()

SEO_BACKEND_URL = os.getenv("SEO_BACKEND_URL", "http://localhost:3000")


@router.get("/health")
def seo_backend_health(user=Depends(get_current_super_admin)):
    """检查 SEO Backend 连通性"""
    import httpx
    try:
        with httpx.Client(timeout=5) as client:
            resp = client.get(f"{SEO_BACKEND_URL}/api/v1/health")
            return success_response(data={
                "status": "connected" if resp.status_code == 200 else "error",
                "code": resp.status_code,
            })
    except Exception as e:
        return success_response(data={"status": "unreachable", "error": str(e)})


async def _proxy_seo_request(
    path: str,
    request: Request,
):
    """_proxy_seo_request。

    参数说明：
    :param path: 参数 path
    :param request: 参数 request
    :return: 返回处理结果。
    """
    import httpx
    target_url = f"{SEO_BACKEND_URL}/api/v1/{path}"
    body = None
    if request.method in ("POST", "PUT", "PATCH"):
        body = await request.body()

    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                params=dict(request.query_params),
            )
            return JSONResponse(
                content=resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {"data": resp.text},
                status_code=resp.status_code,
            )
    except httpx.ConnectError:
        raise HTTPException(status_code=502, detail="SEO Backend 服务不可用")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="SEO Backend 请求超时")


@router.get("/{path:path}", operation_id="seo_proxy_get")
async def proxy_seo_get(
    path: str,
    request: Request,
    user=Depends(get_current_super_admin),
):
    """代理 SEO Backend GET 请求"""
    return await _proxy_seo_request(path, request)


@router.post("/{path:path}", operation_id="seo_proxy_post")
async def proxy_seo_post(
    path: str,
    request: Request,
    user=Depends(get_current_super_admin),
):
    """代理 SEO Backend POST 请求"""
    return await _proxy_seo_request(path, request)


@router.put("/{path:path}", operation_id="seo_proxy_put")
async def proxy_seo_put(
    path: str,
    request: Request,
    user=Depends(get_current_super_admin),
):
    """代理 SEO Backend PUT 请求"""
    return await _proxy_seo_request(path, request)


@router.delete("/{path:path}", operation_id="seo_proxy_delete")
async def proxy_seo_delete(
    path: str,
    request: Request,
    user=Depends(get_current_super_admin),
):
    """代理 SEO Backend DELETE 请求"""
    return await _proxy_seo_request(path, request)


@router.patch("/{path:path}", operation_id="seo_proxy_patch")
async def proxy_seo_patch(
    path: str,
    request: Request,
    user=Depends(get_current_super_admin),
):
    """代理 SEO Backend PATCH 请求"""
    return await _proxy_seo_request(path, request)
