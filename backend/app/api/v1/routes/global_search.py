# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""工作区全局搜索（UX-2c）— 菜单 + 询盘 + 母版 + 订单。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.response import success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.content_master import ContentMaster
from app.models.order import Order
from app.models.tenant import Tenant, UserTenant
from app.models.user import User
from app.services.inquiries_unified_service import InquiriesUnifiedService


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/search", tags=["全局搜索"])


def _tenant_ids_for_user(user: User, db: Session) -> list[str] | None:
    """
    处理 _tenant_ids_for_user 相关业务逻辑。

    :param user: 入参 (User)。
    :param db: 入参 (Session)。

    :return: 返回 list[str] | None 类型的结果。
    """
    if user.role in ("admin", "super_admin"):
        return None
    return [
        ut.tenant_id
        for ut in db.query(UserTenant)
        .filter(UserTenant.user_id == user.id, UserTenant.is_active.is_(True))
        .all()
    ]


@router.get("/workspace")
def workspace_search(
    q: str = Query(..., min_length=1, max_length=80),
    limit: int = Query(12, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ctrl+K：跨询盘、内容母版、订单、租户检索。"""
    term = q.strip()
    if not term:
        return success_response(data={"items": []})

    like = f"%{term}%"
    items: list[dict] = []
    tenant_ids = _tenant_ids_for_user(current_user, db)
    # 询盘（手机号 / 姓名）
    inq_svc = InquiriesUnifiedService(db)
    tid = tenant_ids[0] if tenant_ids and len(tenant_ids) == 1 else None
    inq_page = inq_svc.list_page(
        page=1,
        page_size=limit,
        search=term,
        tenant_id=tid,
    )
    for row in inq_page.get("items") or []:
        items.append({
            "type": "inquiry",
            "title": row.get("name") or "询盘",
            "subtitle": row.get("phone") or row.get("status"),
            "path": "/inquiries",
            "icon": "MessageOutlined",
        })

    if len(items) < limit:
        cm_q = db.query(ContentMaster).filter(
            or_(ContentMaster.title.contains(term), ContentMaster.body.contains(term))
        )
        if tenant_ids is not None:
            if not tenant_ids:
                cm_q = cm_q.filter(False)
            else:
                cm_q = cm_q.filter(ContentMaster.tenant_id.in_(tenant_ids))
        for row in cm_q.order_by(ContentMaster.updated_at.desc()).limit(5).all():
            items.append({
                "type": "content_master",
                "title": row.title[:80],
                "subtitle": row.status,
                "path": "/publish/unified",
                "icon": "FileOutlined",
            })

    if len(items) < limit and current_user.role in ("admin", "super_admin", "tenant_admin"):
        oq = db.query(Order).filter(
            or_(Order.order_number.contains(term), Order.tracking_number.contains(term))
        )
        for row in oq.order_by(Order.updated_at.desc()).limit(5).all():
            items.append({
                "type": "order",
                "title": row.order_number,
                "subtitle": row.tracking_number or row.status,
                "path": "/orders",
                "icon": "ShoppingOutlined",
            })

    if len(items) < limit and current_user.role in ("admin", "super_admin"):
        for row in (
            db.query(Tenant)
            .filter(or_(Tenant.name.contains(term), Tenant.domain.contains(term)))
            .limit(5)
            .all()
        ):
            items.append({
                "type": "tenant",
                "title": row.name,
                "subtitle": row.domain,
                "path": "/tenants",
                "icon": "TeamOutlined",
            })

    if len(items) < limit:
        items.append({
            "type": "copilot",
            "title": "卖货飞轮",
            "subtitle": "按您公司名展示的卖货智能助手",
            "path": "/client/copilot",
            "icon": "RobotOutlined",
        })

    return success_response(data={"items": items[:limit], "q": term})
