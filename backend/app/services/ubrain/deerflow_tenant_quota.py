# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""DeerFlow 租户套餐/配额 — 定时市场研究仅对符合条件的租户。"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.cache import redis_available, redis_client
from app.core.config import settings
from app.models.tenant import Tenant

logger = logging.getLogger("uj-admin.deerflow_tenant_quota")

MONTHLY_PREFIX = "deerflow:schedule:month:"


def _plan_codes_allowed() -> frozenset[str]:
    """_plan_codes_allowed。
    :return: 返回处理结果。
    """
    raw = (getattr(settings, "DEERFLOW_SCHEDULE_PLAN_CODES", "") or "").strip()
    if not raw:
        return frozenset({"pro", "enterprise", "flagship"})
    return frozenset(x.strip().lower() for x in raw.split(",") if x.strip())


def _tenant_settings(tenant: Tenant) -> dict[str, Any]:
    """_tenant_settings。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    try:
        return json.loads(tenant.settings or "{}")
    except (json.JSONDecodeError, TypeError):
        return {}


def monthly_limit() -> int:
    """monthly_limit。
    :return: 返回处理结果。
    """
    return int(getattr(settings, "DEERFLOW_SCHEDULE_MONTHLY_LIMIT_PER_TENANT", 4) or 4)


def _monthly_count(tenant_id: str) -> int:
    """_monthly_count。

    参数说明：
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    if not redis_available():
        return 0
    month = datetime.now(timezone.utc).strftime("%Y%m")
    try:
        raw = redis_client.get(f"{MONTHLY_PREFIX}{tenant_id}:{month}")
    except Exception as exc:
        logger.warning("deerflow monthly count redis get failed: %s", exc)
        return 0
    try:
        return int(raw or 0)
    except (TypeError, ValueError):
        return 0


def increment_monthly_count(tenant_id: str) -> int:
    """increment_monthly_count。

    参数说明：
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    if not redis_client:
        return 1
    month = datetime.now(timezone.utc).strftime("%Y%m")
    key = f"{MONTHLY_PREFIX}{tenant_id}:{month}"
    n = redis_client.incr(key)
    redis_client.expire(key, 86400 * 45)
    return int(n)


def check_tenant_schedule_eligibility(
    db: Session,
    tenant_id: str,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """返回 eligible / reason；force 跳过套餐与月配额（超管手动仍受显式租户列表约束）。"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant or not tenant.is_active:
        return {"eligible": False, "reason": "tenant_inactive"}
    if tenant.status not in ("active", "trial"):
        return {"eligible": False, "reason": f"status_{tenant.status}"}

    settings_json = _tenant_settings(tenant)
    if settings_json.get("flywheel_scheduled") is False:
        return {"eligible": False, "reason": "tenant_opt_out"}

    plan_code = (tenant.plan.code if tenant.plan else "").lower()
    allowed_plans = _plan_codes_allowed()
    plan_ok = plan_code in allowed_plans
    override = settings_json.get("flywheel_scheduled") is True
    if not force and not plan_ok and not override:
        return {
            "eligible": False,
            "reason": "plan_not_eligible",
            "plan_code": plan_code,
            "allowed_plans": sorted(allowed_plans),
        }

    if not force:
        used = _monthly_count(str(tenant_id))
        limit = monthly_limit()
        if used >= limit:
            return {
                "eligible": False,
                "reason": "monthly_quota_exceeded",
                "used": used,
                "limit": limit,
            }

    return {
        "eligible": True,
        "plan_code": plan_code,
        "monthly_used": _monthly_count(str(tenant_id)),
        "monthly_limit": monthly_limit(),
    }


def resolve_eligible_schedule_tenant_ids(db: Session, *, force: bool = False) -> tuple[list[str], list[dict[str, Any]]]:
    """候选租户 ∩ 套餐/配额过滤。"""
    raw = (getattr(settings, "DEERFLOW_SCHEDULE_TENANT_IDS", "") or "").strip()
    if raw:
        candidate_ids = [x.strip() for x in raw.split(",") if x.strip()]
    else:
        max_n = int(getattr(settings, "DEERFLOW_SCHEDULE_MAX_TENANTS", 50) or 50)
        rows = (
            db.query(Tenant.id)
            .filter(
                Tenant.is_active.is_(True),
                Tenant.status.in_(("active", "trial")),
            )
            .order_by(Tenant.created_at.asc())
            .limit(max_n)
            .all()
        )
        candidate_ids = [str(r[0]) for r in rows]

    eligible: list[str] = []
    skipped: list[dict[str, Any]] = []
    for tid in candidate_ids:
        gate = check_tenant_schedule_eligibility(db, tid, force=force)
        if gate.get("eligible"):
            eligible.append(tid)
        else:
            skipped.append({"tenant_id": tid, **gate})
    return eligible, skipped
