# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""SEO-10：矩阵词/收录关键词 → DeerFlow research_hints。"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.content import InclusionStatus, PlatformAccount, PublishTask
from app.models.seo import Keyword
from app.services.ubrain.tenant_memory_service import get_memory, merge_memory


def _tenant_task_ids(db: Session, tenant_id: str, *, limit: int = 100) -> list[str]:
    """实现 租户任务ID 的功能。
    
    :param db: 参数 db（类型: Session）
    :param tenant_id: 参数 tenant_id（类型: str）
    :param limit: 参数 limit（类型: int）
    :return: 返回 list[str] 结果
    """
    accounts = (
        db.query(PlatformAccount.id)
        .filter(PlatformAccount.tenant_id == tenant_id, PlatformAccount.is_active.is_(True))
        .all()
    )
    if not accounts:
        return []
    aids = [str(a[0]) for a in accounts]
    rows = (
        db.query(PublishTask.id)
        .filter(PublishTask.account_id.in_(aids))
        .order_by(PublishTask.updated_at.desc())
        .limit(limit)
        .all()
    )
    return [str(r[0]) for r in rows]


def collect_seo_hints(db: Session, tenant_id: str, *, limit: int = 12) -> list[str]:
    """实现 收集seohints 的功能。
    
    :param db: 参数 db（类型: Session）
    :param tenant_id: 参数 tenant_id（类型: str）
    :param limit: 参数 limit（类型: int）
    :return: 返回 list[str] 结果
    """
    hints: list[str] = []
    task_ids = _tenant_task_ids(db, tenant_id)
    if task_ids:
        rows = (
            db.query(InclusionStatus)
            .filter(InclusionStatus.task_id.in_(task_ids), InclusionStatus.is_included.is_(True))
            .order_by(InclusionStatus.last_checked_at.desc())
            .limit(limit)
            .all()
        )
        for r in rows:
            kw = (r.keyword or "").strip()
            if kw and kw not in hints:
                hints.append(f"已收录词「{kw[:40]}」可加深区域研究")

    global_kw = (
        db.query(Keyword)
        .filter(Keyword.is_active.is_(True))
        .order_by(Keyword.search_volume.desc())
        .limit(8)
        .all()
    )
    for k in global_kw:
        text = f"矩阵热词：{k.keyword}"
        if text not in hints:
            hints.append(text)

    not_included = 0
    if task_ids:
        not_included = (
            db.query(InclusionStatus)
            .filter(InclusionStatus.task_id.in_(task_ids), InclusionStatus.is_included.is_(False))
            .count()
        )
    if not_included >= 3:
        hints.append(f"有 {not_included} 条未收录 URL，建议优化落地页与矩阵标题")

    return hints[:limit]


def sync_seo_research_hints(db: Session, tenant_id: str) -> dict[str, Any]:
    """实现 同步seoresearchhints 的功能。
    
    :param db: 参数 db（类型: Session）
    :param tenant_id: 参数 tenant_id（类型: str）
    :return: 返回 dict[str, Any] 结果
    """
    hints = collect_seo_hints(db, tenant_id)
    if not hints:
        return {"tenant_id": tenant_id, "updated": False, "hints": []}
    mem = get_memory(db, tenant_id) or {}
    existing = list(mem.get("research_hints") or [])
    merged = list(dict.fromkeys([*hints, *existing]))[:20]
    merge_memory(db, tenant_id, {"research_hints": merged, "seo_hints_synced_at": True})
    return {"tenant_id": tenant_id, "updated": True, "hints": hints}


def sync_all_active_tenants(db: Session, *, max_tenants: int = 100) -> dict[str, Any]:
    """实现 同步allactivetenants 的功能。
    
    :param db: 参数 db（类型: Session）
    :param max_tenants: 参数 max_tenants（类型: int）
    :return: 返回 dict[str, Any] 结果
    """
    from app.models.tenant import Tenant
    tenants = db.query(Tenant).filter(Tenant.is_active.is_(True)).limit(max_tenants).all()
    updated = 0
    for t in tenants:
        out = sync_seo_research_hints(db, str(t.id))
        if out.get("updated"):
            updated += 1
    return {"tenants": len(tenants), "updated": updated}
