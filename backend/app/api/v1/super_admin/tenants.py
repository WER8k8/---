# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""超级管理员 - 租户管理接口"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.admin_auth import get_current_super_admin
from app.core.database import get_db
from app.core.response import success_response
from app.models.user import User
from app.schemas.tenant import TenantResponse
from app.services.tenant_service import TenantService

router = APIRouter()

VALID_TENANT_STATUSES = frozenset({"trial", "active", "suspended", "cancelled"})


class TenantStatusUpdate(BaseModel):
    status: str
    is_active: Optional[bool] = None


@router.get("/")
def list_tenants(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    """租户列表（超级管理员）"""
    service = TenantService(db)
    items, total = service.list_tenants(
        page=page,
        page_size=page_size,
        search=search,
        status=status,
    )
    rows = [TenantResponse.model_validate(t).model_dump(mode="json") for t in items]
    return success_response(data={
        "items": rows,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.get("/{tenant_id}")
def get_tenant_detail(
    tenant_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """租户详情"""
    service = TenantService(db)
    tenant = service.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    return success_response(data=TenantResponse.model_validate(tenant).model_dump(mode="json"))


@router.put("/{tenant_id}/status")
def update_tenant_status(
    tenant_id: str,
    body: TenantStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """更新租户状态（trial/active/suspended/cancelled）"""
    if body.status not in VALID_TENANT_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"非法状态: {body.status}，可选: {', '.join(sorted(VALID_TENANT_STATUSES))}",
        )
    service = TenantService(db)
    update = {"status": body.status}
    if body.is_active is not None:
        update["is_active"] = body.is_active
    try:
        from app.schemas.tenant import TenantUpdate
        tenant = service.update_tenant(tenant_id, TenantUpdate(**update))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    return success_response(
        data=TenantResponse.model_validate(tenant).model_dump(mode="json"),
        message="租户状态已更新",
    )
