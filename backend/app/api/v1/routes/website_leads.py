# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""网站线索 HMAC 接入路由（GJ-U4）。

- POST /website-leads：公开端点（HMAC 验签防重放，无登录态）；租户由密钥属主决定；
- /website-lead-ingress/keys：租户管理员签发/列举/吊销接入密钥（secret 明文仅签发响应一次）。
反欺骗：source_channel 服务端强制 website_ingress，忽略客户端声明。
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.response import success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services import website_lead_ingress_service as svc
from app.services.website_lead_ingress_service import IngressError

router = APIRouter(tags=["网站线索接入"])

_STATUS_TO_HTTP = {"unconfigured": 401, "invalid": 401, "expired": 401, "replay": 409}


def _user_tenant_ids(db: Session, user: User) -> list[str]:
    from app.models.tenant import UserTenant

    return [
        ut.tenant_id
        for ut in db.query(UserTenant)
        .filter(UserTenant.user_id == user.id, UserTenant.is_active)
        .all()
    ]


@router.post("/website-leads")
async def receive_website_lead(request: Request, db: Session = Depends(get_db)):
    """HMAC 签名网站线索入口（上游 /api/website-leads 同构）。

    签名头：x-goodjob-key-id / x-goodjob-timestamp / x-goodjob-nonce /
    x-goodjob-signature（v1=<hmac-sha256 hex>，canonical 含 sha256(raw body)）。
    """
    raw_body = await request.body()
    headers = {k.lower(): v for k, v in request.headers.items()}
    path = request.url.path
    try:
        key_meta = svc.verify_signature(
            db, method="POST", path=path, headers=headers, raw_body=raw_body
        )
    except IngressError as e:
        return JSONResponse(
            status_code=_STATUS_TO_HTTP.get(e.status, 401),
            content={"code": _STATUS_TO_HTTP.get(e.status, 401), "message": f"website lead rejected: {e.status}", "data": {"reason": e.status}},
        )
    import json as _json

    try:
        payload = _json.loads(raw_body.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("payload must be object")
        inquiry = svc.create_inquiry(
            db,
            tenant_id=key_meta["tenant_id"],
            payload=payload,
            key_meta=key_meta,
            external_id=str(payload.get("externalId") or "") or None,
        )
    except ValueError as e:
        return JSONResponse(
            status_code=422,
            content={"code": 422, "message": f"website lead payload invalid: {e}", "data": {"reason": str(e)}},
        )
    return success_response(
        data={
            "inquiry_id": str(inquiry.id),
            "tenant_id": str(inquiry.tenant_id),
            "source_channel": inquiry.source_channel,
            "key_id": key_meta["key_id"],
        }
    )


@router.post("/website-lead-ingress/keys")
def issue_ingress_key(
    label: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """签发本租户接入密钥（secret 明文仅此一次）。"""
    tenant_ids = _user_tenant_ids(db, current_user)
    if not tenant_ids:
        return JSONResponse(status_code=403, content={"code": 403, "message": "当前用户无活跃租户", "data": {}})
    result = svc.issue_key(db, tenant_id=tenant_ids[0], label=label)
    return success_response(data=result)


@router.get("/website-lead-ingress/keys")
def list_ingress_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """本租户接入密钥列表（零明文）。"""
    tenant_ids = _user_tenant_ids(db, current_user)
    if not tenant_ids:
        return success_response(data={"items": []})
    return success_response(data={"items": svc.list_keys(db, tenant_id=tenant_ids[0])})


@router.delete("/website-lead-ingress/keys/{key_id}")
def revoke_ingress_key(
    key_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """吊销接入密钥（幂等；吊销后验签自然失效）。"""
    tenant_ids = _user_tenant_ids(db, current_user)
    if not tenant_ids:
        return JSONResponse(status_code=403, content={"code": 403, "message": "当前用户无活跃租户", "data": {}})
    revoked = svc.revoke_key(db, tenant_id=tenant_ids[0], key_id=key_id)
    return success_response(data={"key_id": key_id, "revoked": revoked})
