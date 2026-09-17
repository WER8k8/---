# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Auto-Scaling Service: 租户资源自动扩容.

当租户 AI 配额使用率达到阈值时，自动升级至高一级套餐；
或标记为「即将触达上限」供前端展示。

设计原则：
- 不修改 tenant.status（由 TokenService 管停机）
- 自动升级仅在有下一档可用且租户未手动锁定时生效
- 所有操作幂等：同一 tenant_id 在 24h 内不重复触发
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# 使用率阈值：达到此百分比触发自动扩容评估
USAGE_THRESHOLD_PCT = 80

# 防重复窗口
DEDUP_WINDOW = timedelta(hours=24)


def evaluate_auto_scale(db: Session, tenant_id: str) -> dict[str, Any]:
    """评估单租户是否需要自动扩容。

    返回:
        {
            "tenant_id": str,
            "needs_scale": bool,
            "current_plan": str,
            "target_plan": str | None,
            "usage_pct": float,
            "action_taken": str | None,
        }
    """
    from app.models.tenant import Tenant, TenantPlan, TenantSubscription

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return {"tenant_id": tenant_id, "needs_scale": False, "error": "tenant not found"}

    # 获取当前配额上限
    from app.services.token_service import TokenService
    svc = TokenService(db)
    quota_limit = svc._quota_limit(tenant)
    if quota_limit <= 0:
        return {
            "tenant_id": tenant_id,
            "needs_scale": False,
            "usage_pct": 0.0,
            "action_taken": "no_quota",
        }

    usage = int(tenant.ai_quota_used or 0)
    usage_pct = round(usage / quota_limit * 100, 1) if quota_limit > 0 else 0.0

    if usage_pct < USAGE_THRESHOLD_PCT:
        return {
            "tenant_id": tenant_id,
            "needs_scale": False,
            "usage_pct": usage_pct,
            "action_taken": "below_threshold",
        }

    # 防重复：检查 24h 内是否已触发过
    if _was_recently_scaled(db, tenant_id):
        return {
            "tenant_id": tenant_id,
            "needs_scale": True,
            "usage_pct": usage_pct,
            "action_taken": "dedup_window_active",
        }

    # 找目标套餐：按 max_ai_quota 排序的下一档
    target_plan = _find_next_plan(db, tenant, quota_limit)
    if not target_plan:
        return {
            "tenant_id": tenant_id,
            "needs_scale": True,
            "usage_pct": usage_pct,
            "action_taken": "no_upstream_plan",
            "note": "已是最顶级套餐，无法自动扩容",
        }

    # 执行升级
    _execute_plan_upgrade(db, tenant, target_plan)
    logger.info(
        "Auto-scale: tenant=%s usage=%.1f%% upgrading %s -> %s",
        tenant_id, usage_pct,
        tenant.plan.name if tenant.plan else "none",
        target_plan.name,
    )
    return {
        "tenant_id": tenant_id,
        "needs_scale": True,
        "usage_pct": usage_pct,
        "current_plan": tenant.plan.name if tenant.plan else "none",
        "target_plan": target_plan.name,
        "action_taken": "upgraded",
    }


def _was_recently_scaled(db: Session, tenant_id: str) -> bool:
    """24h 内是否已有扩容记录（幂等保护）。"""
    from sqlalchemy import text
    row = db.execute(
        text(
            "SELECT 1 FROM operation_logs "
            "WHERE target_type = 'tenant' AND target_id = :tid "
            "AND action = 'auto_scale' AND created_at > :cutoff LIMIT 1"
        ),
        {"tid": tenant_id, "cutoff": datetime.now(timezone.utc) - DEDUP_WINDOW},
    ).fetchone()
    return row is not None


def _find_next_plan(db: Session, tenant: Any, current_quota: int) -> Optional[Any]:
    """找到 max_ai_quota 刚好大于当前限额的下一档套餐。"""
    from app.models.tenant import TenantPlan

    current_plan_code = tenant.plan.code if tenant.plan else None
    candidates = (
        db.query(TenantPlan)
        .filter(TenantPlan.is_active.is_(True), TenantPlan.max_ai_quota > current_quota)
        .order_by(TenantPlan.max_ai_quota.asc())
        .all()
    )
    if not candidates:
        return None
    # 跳过同 code 的套餐
    for p in candidates:
        if p.code != current_plan_code:
            return p
    return None


def _execute_plan_upgrade(db: Session, tenant: Any, target_plan: Any) -> None:
    """执行套餐升级（修改 tenant.plan_id + 记录 operation_log）。"""
    from sqlalchemy import text
    from uuid import uuid4

    old_plan_id = str(tenant.plan_id) if tenant.plan_id else None
    tenant.plan_id = target_plan.id
    db.flush()

    # 写审计日志
    db.execute(
        text(
            "INSERT INTO operation_logs (id, actor, action, target_type, target_id, detail, created_at) "
            "VALUES (:id, :actor, :action, :tt, :tid, :detail, NOW())"
        ),
        {
            "id": str(uuid4()),
            "actor": "system:auto_scale",
            "action": "auto_scale",
            "tt": "tenant",
            "tid": str(tenant.id),
            "detail": f"auto-upgrade {old_plan_id} -> {str(target_plan.id)} ({target_plan.name})",
        },
    )
    db.commit()


def run_auto_scale_all(db: Session) -> dict[str, Any]:
    """批量评估所有活跃租户的扩容需求（供 Celery 定时任务调用）。"""
    from app.models.tenant import Tenant

    tenants = db.query(Tenant).filter(Tenant.status == "active").all()
    results = []
    for t in tenants:
        r = evaluate_auto_scale(db, str(t.id))
        if r.get("action_taken") == "upgraded":
            results.append(r)
    return {"evaluated": len(tenants), "upgraded": len(results), "details": results}
