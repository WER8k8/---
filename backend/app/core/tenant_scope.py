# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""共享租户作用域助手（ADR-002 应用层隔离第一道防线）。

复用既有的 `resolve_tenant_id_for_user`（经 `user_tenants` 关联表解析用户归属；
super_admin/admin 返回 None = 平台级跨租户）。本模块只提供查询/详情两个统一入口，
供各租户域端点（rfq/quotes/opportunity/campaign/company/lead …）复用，避免逐点手写过滤漂移。
"""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Query, Session

from app.models.user import User
from app.services.tenant_scenario_service import resolve_tenant_id_for_user


def scope_tenant_id(db: Session, user: User) -> Optional[str]:
    """当前用户应限定的租户 id；None = 平台级（看全部）。"""
    return resolve_tenant_id_for_user(db, user)


def scope_tenant_query(query: Query, model: Any, db: Session, user: User) -> Query:
    """给查询加租户边界：租户用户限定本租户，平台级用户（tenant_id=None）放行全量。

    model 需有 `tenant_id` 列。平台级返回原 query（不追加过滤）。
    """
    tid = resolve_tenant_id_for_user(db, user)
    if tid:
        query = query.filter(model.tenant_id == tid)
    return query


def tenant_can_access(
    db: Session, user: User, obj_tenant_id: Optional[str]
) -> bool:
    """单对象可读判定：平台级放行；租户用户仅本租户。

    obj_tenant_id 为空（历史无归属行）：租户用户不可见（避免漏判跨租户），
    平台级可见。
    """
    tid = resolve_tenant_id_for_user(db, user)
    if tid is None:
        return True  # 平台级
    return bool(obj_tenant_id) and str(obj_tenant_id) == str(tid)
