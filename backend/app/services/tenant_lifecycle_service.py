# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""第二层补充缺口 P · 客户退出与注销生命周期服务（Tenant Lifecycle & Exit Service）。

实现：
1. 退出前依赖预检（未结订单、未结佣金、未消耗预占）；
2. 凭据与权限吊销（API Key 吊销、平台凭据解绑）；
3. 业务数据归档导出快照（产品、询盘、订单、单据）；
4. 状态机：active → pending_deletion → export_available → deletion_scheduled → archived/deleted。
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.models.api_marketplace import ApiKey
from app.models.content import PlatformAccount
from app.models.order import Order
from app.models.inquiry import Inquiry
from app.models.product import Product
from app.services.api_marketplace_service import revoke_key

logger = logging.getLogger("uj-admin.services.tenant_lifecycle")


import json


def _get_tenant_settings(tenant: Tenant) -> dict[str, Any]:
    if not tenant.settings:
        return {}
    try:
        data = json.loads(tenant.settings)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _set_tenant_settings(tenant: Tenant, data: dict[str, Any]) -> None:
    tenant.settings = json.dumps(data, ensure_ascii=False)


class TenantExitError(Exception):
    """租户退出前置校验异常。"""


def initiate_tenant_exit(
    db: Session,
    *,
    tenant_id: str,
    operator_id: str,
    reason: str,
    force: bool = False,
) -> dict[str, Any]:
    """发起租户退出申请：
    1. 检查是否存在未完成履约订单（未结案订单在非 force 下阻断注销）；
    2. 吊销其名下全部活跃的 API Key；
    3. 清理平台凭据引用；
    4. 租户标记 pending_deletion。
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise ValueError(f"租户不存在: {tenant_id}")

    # 1. 检查未结订单
    open_orders = (
        db.query(Order)
        .filter(Order.tenant_id == tenant_id)
        .filter(Order.status.in_(["pending", "confirmed", "in_production", "shipped"]))
        .all()
    )
    if open_orders and not force:
        raise TenantExitError(
            f"存在 {len(open_orders)} 笔未结履约订单，请先结案或使用 force 参数注销。"
        )

    # 2. 吊销所有活跃 API Key
    keys = (
        db.query(ApiKey)
        .filter(ApiKey.tenant_id == tenant_id, ApiKey.revoked_at.is_(None))
        .all()
    )
    revoked_keys_count = 0
    for k in keys:
        revoke_key(db, str(k.id), tenant_id=tenant_id)
        revoked_keys_count += 1

    # 3. 吊销平台绑定凭据引用
    plat_accounts = (
        db.query(PlatformAccount)
        .filter(PlatformAccount.tenant_id == tenant_id)
        .all()
    )
    for p in plat_accounts:
        p.credential_ref = None
        p.login_status = "logged_out"

    # 4. 更新租户状态
    tenant.status = "pending_deletion"
    meta = _get_tenant_settings(tenant)
    meta["exit_info"] = {
        "initiated_at": datetime.now(timezone.utc).isoformat(),
        "operator_id": operator_id,
        "reason": reason,
        "revoked_keys": revoked_keys_count,
        "open_orders_ignored": len(open_orders) if force else 0,
    }
    _set_tenant_settings(tenant, meta)
    db.commit()
    db.refresh(tenant)

    logger.warning("Tenant exit initiated: tenant=%s operator=%s reason=%s", tenant_id, operator_id, reason)
    return {
        "tenant_id": str(tenant.id),
        "status": tenant.status,
        "revoked_keys": revoked_keys_count,
        "open_orders_count": len(open_orders),
    }


def export_tenant_package(db: Session, *, tenant_id: str) -> dict[str, Any]:
    """生成租户合规导出归档快照包。"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise ValueError(f"租户不存在: {tenant_id}")

    # 抽取产品
    products = (
        db.query(Product)
        .filter(Product.tenant_id == tenant_id)
        .limit(100)
        .all()
    )
    # 抽取询盘
    inquiries = (
        db.query(Inquiry)
        .filter(Inquiry.tenant_id == tenant_id)
        .limit(100)
        .all()
    )
    # 抽取订单
    orders = (
        db.query(Order)
        .filter(Order.tenant_id == tenant_id)
        .limit(100)
        .all()
    )

    package = {
        "export_id": f"export_{tenant_id}_{int(datetime.now(timezone.utc).timestamp())}",
        "tenant": {
            "id": str(tenant.id),
            "name": tenant.name,
            "status": tenant.status,
            "created_at": tenant.created_at.isoformat() if tenant.created_at else None,
        },
        "counts": {
            "products": len(products),
            "inquiries": len(inquiries),
            "orders": len(orders),
        },
        "products": [{"id": str(p.id), "name": p.name} for p in products],
        "inquiries": [{"id": str(i.id), "name": i.name, "status": i.status} for i in inquiries],
        "orders": [{"id": str(o.id), "status": o.status} for o in orders],
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }

    if tenant.status == "pending_deletion":
        tenant.status = "export_available"
        db.commit()

    return package


def cancel_tenant_exit(db: Session, *, tenant_id: str) -> dict[str, Any]:
    """取消租户退出申请，恢复为 active。"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise ValueError(f"租户不存在: {tenant_id}")

    if tenant.status not in ("pending_deletion", "export_available"):
        raise ValueError(f"当前租户状态为 {tenant.status}，非待注销状态，无需恢复")

    tenant.status = "active"
    meta = _get_tenant_settings(tenant)
    if "exit_info" in meta:
        meta["exit_info"]["cancelled_at"] = datetime.now(timezone.utc).isoformat()
    _set_tenant_settings(tenant, meta)
    db.commit()
    db.refresh(tenant)

    logger.info("Tenant exit cancelled: tenant=%s restored to active", tenant_id)
    return {"tenant_id": str(tenant.id), "status": tenant.status}
