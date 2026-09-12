"""租户登录页搜索 — 只读查询，不含认证逻辑"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.tenant import Tenant

TENANT_SEARCH_LIMIT = 10


def search_tenants_for_login(db: Session, code: str = "") -> list[dict[str, str]]:
    """search_tenants_for_login。

    参数说明：
    :param db: 参数 db
    :param code: 参数 code
    :return: 返回处理结果。
    """
    q = db.query(Tenant).filter(Tenant.is_active.is_(True))
    term = code.strip()
    if term:
        like = f"%{term}%"
        q = q.filter((Tenant.domain.ilike(like)) | (Tenant.name.ilike(like)))
    rows = q.order_by(Tenant.name.asc()).limit(TENANT_SEARCH_LIMIT).all()
    return [
        {
            "tenantId": str(t.id),
            "tenantCode": t.domain,
            "tenantName": t.name,
        }
        for t in rows
    ]
