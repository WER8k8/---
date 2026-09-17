# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""超管：客户新增/自填平台来源审计（只读）。"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.admin_auth import get_current_super_admin
from app.core.database import get_db
from app.core.response import success_response
from app.models.content import Platform
from app.models.platform_registry import PlatformTenantOrigin
from app.models.tenant import Tenant
from app.models.user import User

router = APIRouter()


@router.get("/platform-origins")
def list_platform_origins(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    tenant_id: Optional[str] = Query(None),
    platform_id: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
):
    """list_platform_origins。

    参数说明：
    :param db: 参数 db
    :param admin: 参数 admin
    :param page: 参数 page
    :param page_size: 参数 page_size
    :param tenant_id: 参数 tenant_id
    :param platform_id: 参数 platform_id
    :param source: 参数 source
    :return: 返回处理结果。
    """
    _ = admin
    q = db.query(PlatformTenantOrigin).order_by(desc(PlatformTenantOrigin.created_at))
    if tenant_id:
        q = q.filter(PlatformTenantOrigin.tenant_id == tenant_id)
    if platform_id:
        q = q.filter(PlatformTenantOrigin.platform_id == platform_id)
    if source:
        q = q.filter(PlatformTenantOrigin.source == source)

    total = q.count()
    rows = q.offset((page - 1) * page_size).limit(page_size).all()
    tenant_ids = {r.tenant_id for r in rows}
    platform_ids = {r.platform_id for r in rows}
    tenants = {
        str(t.id): t.name
        for t in db.query(Tenant).filter(Tenant.id.in_(tenant_ids)).all()
    } if tenant_ids else {}
    platforms = {
        str(p.id): {
            "name": p.name,
            "platform_type": p.platform_type,
            "region": p.region,
        }
        for p in db.query(Platform).filter(Platform.id.in_(platform_ids)).all()
    } if platform_ids else {}
    items = []
    for r in rows:
        pid = str(r.platform_id)
        plat = platforms.get(pid, {})
        items.append(
            {
                "id": str(r.id),
                "tenant_id": str(r.tenant_id),
                "tenant_name": r.tenant_name or tenants.get(str(r.tenant_id)),
                "platform_id": pid,
                "platform_name": r.platform_name or plat.get("name"),
                "platform_type": plat.get("platform_type"),
                "region": plat.get("region"),
                "source": r.source,
                "is_new_platform": r.is_new_platform,
                "nurture_rules": r.nurture_rules,
                "browser_profile_id": str(r.browser_profile_id)
                if r.browser_profile_id
                else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
        )

    return success_response(
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )
