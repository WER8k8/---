# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""国内轨 · 企业微信线索自动接入路由（Path A · Stage A4）。

- POST /wecom-leads/ingest: 接收源雀企微侧车回流的客户线索（带桥接令牌鉴权）；
- 核心约束：
  1. 服务端强制 source_channel="wecom_ingress"；
  2. 自动注入 UJ inquiries 主链，直接流入外贸 7 步履约漏斗；
  3. 双向鉴权保障：验证 x-bridge-token 或 Bearer 桥接令牌。
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.response import success_response
from app.db.session import get_db
from app.services import wecom_lead_ingress_service as svc
from app.services.wecom_lead_ingress_service import WeComIngressError

# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(tags=["企业微信线索接入"])


def _extract_token(request: Request, x_bridge_token: Optional[str] = None) -> Optional[str]:
    """提取请求中的桥接令牌。"""
    if x_bridge_token:
        return x_bridge_token.strip()
    auth = request.headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return None


@router.post("/wecom-leads/ingest")
async def ingest_wecom_lead(
    request: Request,
    db: Session = Depends(get_db),
    x_bridge_token: Optional[str] = Header(None, alias="x-bridge-token"),
):
    """企微侧车新客户线索回流接入端点。"""
    token = _extract_token(request, x_bridge_token)
    if not svc.verify_bridge_token(token):
        return JSONResponse(
            status_code=401,
            content={
                "code": 401,
                "message": "wecom lead ingress rejected: unauthorized bridge token",
                "data": {"reason": "invalid_bridge_token"},
            },
        )

    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={
                "code": 400,
                "message": "invalid JSON body",
                "data": {"reason": "invalid_json"},
            },
        )

    try:
        inquiry = svc.ingest_wecom_lead(db, payload)
    except WeComIngressError as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "code": e.status_code,
                "message": str(e),
                "data": {"reason": e.reason},
            },
        )

    return success_response(
        data={
            "inquiry_id": str(inquiry.id),
            "name": inquiry.name,
            "status": inquiry.status,
            "source_channel": inquiry.source_channel,
            "wechat": inquiry.wechat,
            "phone": inquiry.phone,
        },
        message="wecom lead ingested successfully",
    )


@router.get("/wecom-leads/status")
def get_wecom_status():
    """获取企业微信侧车与国内轨状态。"""
    import urllib.request
    sidecar_online = False
    try:
        req = urllib.request.Request("http://127.0.0.1:8085/iYqueSys/login", method="POST")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, data=b"{}", timeout=1.0) as resp:
            sidecar_online = True
    except Exception:
        sidecar_online = False

    return success_response(
        data={
            "sidecar_online": sidecar_online,
            "sidecar_backend_url": "http://127.0.0.1:8085",
            "sidecar_frontend_url": "http://127.0.0.1:2024/tools/",
            "source_channel": "wecom_ingress",
            "golden_path": "GP-C",
            "golden_path_name": "企微私域与线索回流（国内轨 SCRM）",
            "supported_capabilities": [
                "wecom.create_live_code",
                "wecom.lead_ingress",
                "wecom.customer_seas",
                "wecom.chat_audit",
                "wecom.send_group_msg",
            ],
        },
        message="ok",
    )
