"""租户 IP 槽位配额与自助分配。"""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.models.egress import EgressEndpoint
from app.models.tenant import Tenant, TenantPlan

# 套餐默认出口 IP 槽位数（可被 tenant.settings.egress_ip_quota 覆盖）
PLAN_EGRESS_QUOTA: dict[str, int] = {
    "free": 0,
    "basic": 1,
    "pro": 2,
    "enterprise": 5,
    "flagship": 10,
    "pilot": 1,
}


def _read_settings(tenant: Tenant) -> dict:
    """_read_settings。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    raw = tenant.settings or "{}"
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def get_egress_quota(tenant: Tenant, plan: TenantPlan | None = None) -> int:
    """get_egress_quota。

    参数说明：
    :param tenant: 参数 tenant
    :param plan: 参数 plan
    :return: 返回处理结果。
    """
    cfg = _read_settings(tenant)
    if "egress_ip_quota" in cfg:
        try:
            return max(0, int(cfg["egress_ip_quota"]))
        except (TypeError, ValueError):
            pass
    code = (plan.code if plan else None) or ""
    return PLAN_EGRESS_QUOTA.get(code, 0)


def count_assigned_slots(db: Session, tenant_id: str) -> int:
    """已开通完成、占用配额的槽位。"""
    return (
        db.query(EgressEndpoint)
        .filter(
            EgressEndpoint.tenant_id == tenant_id,
            EgressEndpoint.slot_status == "assigned",
        )
        .count()
    )


def count_quota_consuming_slots(db: Session, tenant_id: str) -> int:
    """开通中 / 待运营 / 已分配 均占用配额（失败不占，可重试）。"""
    return (
        db.query(EgressEndpoint)
        .filter(
            EgressEndpoint.tenant_id == tenant_id,
            EgressEndpoint.slot_status.in_(
                ("provisioning", "assigned", "pending_manual")
            ),
        )
        .count()
    )


def tenant_egress_summary(db: Session, tenant: Tenant) -> dict:
    """tenant_egress_summary。

    参数说明：
    :param db: 参数 db
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    from app.services.egress_jit_provision_service import (
        _slot_payload,
        attach_latest_job,
    )
    plan = tenant.plan
    quota = get_egress_quota(tenant, plan)
    tid = str(tenant.id)
    assigned = count_assigned_slots(db, tid)
    consuming = count_quota_consuming_slots(db, tid)
    slots = (
        db.query(EgressEndpoint)
        .filter(EgressEndpoint.tenant_id == tenant.id)
        .order_by(EgressEndpoint.created_at.desc())
        .all()
    )
    provisioning = sum(1 for s in slots if s.slot_status == "provisioning")
    pending_manual = sum(1 for s in slots if s.slot_status == "pending_manual")
    from app.services.egress.provisioner import active_egress_provider, is_manual_egress_mode
    prov = active_egress_provider()
    return {
        "quota": quota,
        "assigned_count": assigned,
        "provisioning_count": provisioning,
        "pending_manual_count": pending_manual,
        "remaining": max(0, quota - consuming),
        "provision_mode": prov if not is_manual_egress_mode() else "manual",
        "upstream_pool": prov == "asocks",
        "slots": [
            _slot_payload(s, attach_latest_job(db, str(s.id)))
            for s in slots
        ],
    }


def auto_assign_slots_for_tenant(
    db: Session,
    tenant: Tenant,
    *,
    count: int | None = None,
) -> int:
    """按需采购：为租户排队最多 count 个开通任务（默认补满配额）。"""
    from app.services.egress_jit_provision_service import enqueue_jit_provision
    if count is None:
        count = get_egress_quota(tenant, tenant.plan) - count_quota_consuming_slots(
            db, str(tenant.id)
        )
    if count <= 0:
        return 0
    queued = 0
    job_ids: list[str] = []
    for _ in range(count):
        pair = enqueue_jit_provision(db, tenant)
        if not pair:
            break
        _endpoint, job = pair
        if job:
            job_ids.append(str(job.id))
        queued += 1
    from app.services.egress_jit_provision_service import schedule_provision_jobs
    schedule_provision_jobs(job_ids)
    return queued


def request_one_slot(db: Session, tenant: Tenant) -> tuple[EgressEndpoint, str | None] | None:
    """申请 1 个槽位：manual=待运营；mock=演示自动开通。返回 (endpoint, job_id|None)。"""
    from app.services.egress_jit_provision_service import enqueue_jit_provision
    if count_quota_consuming_slots(db, str(tenant.id)) >= get_egress_quota(
        tenant, tenant.plan
    ):
        return None
    pair = enqueue_jit_provision(db, tenant)
    if not pair:
        return None
    endpoint, job = pair
    return endpoint, str(job.id) if job else None


def platform_egress_overview(db: Session) -> dict:
    """超管静态 IP 池：槽位使用率与区域分布。"""
    total = db.query(EgressEndpoint).count()
    available = (
        db.query(EgressEndpoint)
        .filter(EgressEndpoint.slot_status == "available")
        .count()
    )
    provisioning = (
        db.query(EgressEndpoint)
        .filter(EgressEndpoint.slot_status == "provisioning")
        .count()
    )
    assigned = (
        db.query(EgressEndpoint)
        .filter(EgressEndpoint.slot_status == "assigned")
        .count()
    )
    failed = (
        db.query(EgressEndpoint)
        .filter(EgressEndpoint.slot_status == "failed")
        .count()
    )
    disabled = (
        db.query(EgressEndpoint)
        .filter(EgressEndpoint.slot_status == "disabled")
        .count()
    )
    assignable = max(0, total - disabled)
    usage_rate = round(100.0 * assigned / assignable, 1) if assignable else 0.0
    by_region: dict[str, dict] = {}
    for region in ("cn", "global"):
        base = db.query(EgressEndpoint).filter(EgressEndpoint.region == region)
        rt = base.count()
        ra = base.filter(EgressEndpoint.slot_status == "assigned").count()
        rv = base.filter(EgressEndpoint.slot_status == "available").count()
        rd = base.filter(EgressEndpoint.slot_status == "disabled").count()
        cap = max(0, rt - rd)
        by_region[region] = {
            "total": rt,
            "assigned": ra,
            "available": rv,
            "disabled": rd,
            "usage_rate": round(100.0 * ra / cap, 1) if cap else 0.0,
        }

    tenant_quota_total = 0
    for tenant in db.query(Tenant).filter(Tenant.is_active.is_(True)).all():
        tenant_quota_total += get_egress_quota(tenant, tenant.plan)

    return {
        "total": total,
        "available": available,
        "provisioning": provisioning,
        "assigned": assigned,
        "failed": failed,
        "upstream_pool": False,
        "disabled": disabled,
        "assignable": assignable,
        "usage_rate": usage_rate,
        "by_region": by_region,
        "tenant_quota_total": tenant_quota_total,
        "tenant_quota_used": assigned,
        "tenant_quota_usage_rate": round(
            100.0 * assigned / tenant_quota_total, 1
        )
        if tenant_quota_total
        else 0.0,
    }
