# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""物流模块 — 租户成员订单可见性。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.user import User


def tenant_member_user_ids(db: Session, user: User) -> list[str] | None:
    """超管返回 None（全量）；其余返回同租户成员 user id 列表。"""
    if user.role in ("admin", "super_admin"):
        return None
    from app.models.tenant import UserTenant
    uid = str(user.id)
    tenant_rows = (
        db.query(UserTenant.tenant_id)
        .filter(UserTenant.user_id == uid, UserTenant.is_active.is_(True))
        .all()
    )
    tenant_ids = [str(r[0]) for r in tenant_rows]
    if not tenant_ids:
        return [uid]
    member_rows = (
        db.query(UserTenant.user_id)
        .filter(UserTenant.tenant_id.in_(tenant_ids), UserTenant.is_active.is_(True))
        .all()
    )
    return list({uid, *[str(r[0]) for r in member_rows]})
