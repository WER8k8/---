# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""轨7 API 市场路由（模块13 / T13）。

- 产品/订阅/Key 管理面：登录用户鉴权（get_current_user），租户归属校验；
- /echo：示例受保护端点，X-API-Key 鉴权 + api.request 计量（fail-closed）。
契约：docs/模块13-轨7API市场收口契约-2026-09-28.md
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.response import success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.api_marketplace import (
    LEGAL_PRODUCT_TRANSITIONS,
    LEGAL_SUBSCRIPTION_TRANSITIONS,
    ApiKey,
    ApiProduct,
    ApiSubscription,
)
from app.models.user import User
from app.services import api_marketplace_service as svc
from app.services.api_marketplace_service import (
    ApiKeyExpired,
    ApiKeyRevoked,
    ApiMarketError,
    IllegalTransition,
    InvalidApiKey,
    ProductNotCallable,
    QuotaExceeded,
    ScopeDenied,
    SubscriptionInactive,
)

router = APIRouter(prefix="/api-market", tags=["API市场"])

_STATUS_TO_HTTP = {
    InvalidApiKey: 401,
    ApiKeyRevoked: 401,
    ApiKeyExpired: 401,
    ScopeDenied: 403,
    ProductNotCallable: 403,
    SubscriptionInactive: 403,
    QuotaExceeded: 429,
    IllegalTransition: 409,
}


def _http_status(err: ApiMarketError) -> int:
    return _STATUS_TO_HTTP.get(type(err), 400)


class ProductCreate(BaseModel):
    name: str
    version: str = "v1"
    scope: str = ""
    rate_limit_per_day: Optional[int] = None
    description: Optional[str] = None
    pricing_rule_id: Optional[str] = None


class TransitionBody(BaseModel):
    to_status: str


class KeyCreate(BaseModel):
    label: Optional[str] = None
    scopes: str = ""
    expires_at: Optional[datetime] = None


class SubscriptionCreate(BaseModel):
    product_id: str
    plan: str = "free"
    quota_per_day: Optional[int] = None


class EchoBody(BaseModel):
    product_name: str
    scope_required: Optional[str] = None
    payload: Optional[dict] = None


def _user_tenant_ids(db: Session, user: User) -> list[str]:
    from app.models.tenant import UserTenant

    return [
        ut.tenant_id
        for ut in db.query(UserTenant)
        .filter(UserTenant.user_id == user.id, UserTenant.is_active)
        .all()
    ]


def _require_product_ownership(db: Session, product: ApiProduct, user: User) -> None:
    """非平台自营产品的生命周期操作须为属主租户成员。"""
    if product.owner_tenant_id is None:
        return  # 平台自营产品：管理面收敛到 super_admin 才可动
    if str(product.owner_tenant_id) in _user_tenant_ids(db, user):
        return
    if getattr(user, "role", "") == "super_admin":
        return
    raise HTTPException(status_code=403, detail="无权操作该产品")


@router.post("/products")
def create_product(
    body: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_ids = _user_tenant_ids(db, current_user)
    try:
        product = svc.create_product(
            db,
            name=body.name,
            version=body.version,
            owner_tenant_id=tenant_ids[0] if tenant_ids else None,
            scope=body.scope,
            rate_limit_per_day=body.rate_limit_per_day,
            description=body.description,
            pricing_rule_id=body.pricing_rule_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return success_response(data={"id": str(product.id), "status": product.status})


@router.get("/products")
def list_products(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(ApiProduct)
    if status:
        q = q.filter(ApiProduct.status == status)
    rows = q.order_by(ApiProduct.created_at.desc()).limit(200).all()
    return success_response(
        data={
            "items": [
                {
                    "id": str(p.id),
                    "name": p.name,
                    "version": p.version,
                    "status": p.status,
                    "scope": p.scope,
                    "rate_limit_per_day": p.rate_limit_per_day,
                }
                for p in rows
            ],
            "allowed_transitions": {k: list(v) for k, v in LEGAL_PRODUCT_TRANSITIONS.items()},
        }
    )


@router.post("/products/{product_id}/transition")
def transition_product(
    product_id: str,
    body: TransitionBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = db.query(ApiProduct).filter(ApiProduct.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="产品不存在")
    _require_product_ownership(db, product, current_user)
    try:
        updated = svc.transition_product(db, product, body.to_status)
    except IllegalTransition as e:
        raise HTTPException(status_code=409, detail=str(e))
    return success_response(data={"id": str(updated.id), "status": updated.status})


@router.post("/keys")
def issue_key(
    body: KeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_ids = _user_tenant_ids(db, current_user)
    if not tenant_ids:
        raise HTTPException(status_code=403, detail="当前用户无活跃租户，不能签发 API Key")
    # 明文仅在本响应返回一次；服务端只落 sha256
    result = svc.issue_key(
        db, tenant_id=tenant_ids[0], label=body.label, scopes=body.scopes,
        expires_at=body.expires_at,
    )
    return success_response(data=result)


@router.get("/keys")
def list_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_ids = _user_tenant_ids(db, current_user)
    rows = svc.list_keys(db, tenant_ids[0]) if tenant_ids else []
    return success_response(
        data={
            "items": [
                {
                    "id": str(k.id),
                    "key_prefix": k.key_prefix,
                    "label": k.label,
                    "scopes": k.scopes,
                    "revoked": k.revoked_at is not None,
                    "expires_at": k.expires_at.isoformat() if k.expires_at else None,
                    "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
                }
                for k in rows
            ]
        }
    )


@router.delete("/keys/{key_id}")
def revoke_key(
    key_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_ids = _user_tenant_ids(db, current_user)
    try:
        row = svc.revoke_key(db, key_id, tenant_id=tenant_ids[0] if tenant_ids else None)
    except (InvalidApiKey, ApiKeyRevoked) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ScopeDenied as e:
        raise HTTPException(status_code=403, detail=str(e))
    return success_response(data={"id": str(row.id), "revoked": row.revoked_at is not None})


@router.post("/subscriptions")
def create_subscription(
    body: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_ids = _user_tenant_ids(db, current_user)
    if not tenant_ids:
        raise HTTPException(status_code=403, detail="当前用户无活跃租户，不能订阅")
    product = db.query(ApiProduct).filter(ApiProduct.id == body.product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="产品不存在")
    try:
        sub = svc.subscribe(
            db, consumer_tenant_id=tenant_ids[0], api_product=product,
            plan=body.plan, quota_per_day=body.quota_per_day,
        )
    except (ProductNotCallable, IllegalTransition) as e:
        raise HTTPException(status_code=409, detail=str(e))
    return success_response(data={"id": str(sub.id), "status": sub.status})


@router.get("/subscriptions")
def list_subscriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_ids = _user_tenant_ids(db, current_user)
    rows = (
        db.query(ApiSubscription)
        .filter(ApiSubscription.consumer_tenant_id.in_(tenant_ids))
        .all()
        if tenant_ids
        else []
    )
    return success_response(
        data={
            "items": [
                {
                    "id": str(s.id),
                    "product_id": str(s.api_product_id),
                    "plan": s.plan,
                    "quota_per_day": s.quota_per_day,
                    "status": s.status,
                }
                for s in rows
            ],
            "allowed_transitions": {
                k: list(v) for k, v in LEGAL_SUBSCRIPTION_TRANSITIONS.items()
            },
        }
    )


@router.post("/subscriptions/{subscription_id}/transition")
def transition_subscription(
    subscription_id: str,
    body: TransitionBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_ids = _user_tenant_ids(db, current_user)
    sub = db.query(ApiSubscription).filter(ApiSubscription.id == subscription_id).first()
    if sub is None:
        raise HTTPException(status_code=404, detail="订阅不存在")
    if not tenant_ids or str(sub.consumer_tenant_id) not in tenant_ids:
        if getattr(current_user, "role", "") != "super_admin":
            raise HTTPException(status_code=403, detail="无权操作该订阅")
    try:
        updated = svc.transition_subscription(db, sub, body.to_status)
    except IllegalTransition as e:
        raise HTTPException(status_code=409, detail=str(e))
    return success_response(data={"id": str(updated.id), "status": updated.status})


@router.post("/echo")
def echo(
    body: EchoBody,
    db: Session = Depends(get_db),
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
):
    """示例受保护端点：X-API-Key → 鉴权 + 配额 + api.request 计量（fail-closed）。"""
    try:
        key = svc.meter_request(
            db, raw_key=x_api_key or "", product_name=body.product_name,
            scope_required=body.scope_required,
        )
    except ApiMarketError as e:
        raise HTTPException(status_code=_http_status(e), detail=str(e))
    return success_response(
        data={
            "echoed": body.payload,
            "key_prefix": key.key_prefix,
            "billed": "api.request",
        }
    )
