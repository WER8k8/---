# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""出口 IP 槽位：manual 运营录入 / mock 演示 / asocks JIT 采购 / iproyal 长期养号。"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.egress import EgressEndpoint, EgressProvisionJob
from app.models.tenant import Tenant
from app.services.egress.provisioner import (
    EgressProvisionerError,
    active_egress_provider,
    get_egress_provisioner,
    is_manual_egress_mode,
    run_egress_qc,
)
from app.services.egress_quota_service import (
    count_quota_consuming_slots,
    get_egress_quota,
)

logger = logging.getLogger(__name__)

TERMINAL_JOB_STATUSES = ("succeeded", "failed")
QUOTA_SLOT_STATUSES = ("provisioning", "assigned", "pending_manual")


def _slot_payload(row: EgressEndpoint, job: EgressProvisionJob | None = None) -> dict[str, Any]:
    """_slot_payload。

    参数说明：
    :param row: 参数 row
    :param job: 参数 job
    :return: 返回处理结果。
    """
    show_addr = row.slot_status == "assigned"
    data: dict[str, Any] = {
        "id": row.id,
        "region": row.region,
        "host": row.host if show_addr else None,
        "port": row.port if show_addr else None,
        "slot_status": row.slot_status,
        "provider": row.provider,
        "label": row.label,
        "provision_error": row.provision_error,
        "has_credentials": bool(row.proxy_username and row.proxy_password),
    }
    if job:
        data["provision_job"] = {
            "id": job.id,
            "status": job.status,
            "error_message": job.error_message,
        }
    return data


def enqueue_jit_provision(
    db: Session,
    tenant: Tenant,
    *,
    region: str = "global",
    country: str | None = None,
) -> tuple[EgressEndpoint, EgressProvisionJob | None] | None:
    """占用配额：manual=待运营；mock/asocks=排队自动开通。"""
    quota = get_egress_quota(tenant, tenant.plan)
    used = count_quota_consuming_slots(db, str(tenant.id))
    if used >= quota:
        return None

    cc = (country or settings.EGRESS_JIT_COUNTRY or "US").upper()
    if is_manual_egress_mode():
        endpoint = EgressEndpoint(
            region=region,
            host="(待运营配置)",
            port=0,
            provider="manual",
            slot_status="pending_manual",
            tenant_id=tenant.id,
            label=f"{cc} 静态 ISP · 待运营开通",
            provision_error=None,
        )
        db.add(endpoint)
        db.commit()
        db.refresh(endpoint)
        return endpoint, None

    provider = active_egress_provider()
    label_map = {
        "mock": f"{cc} 演示线路开通中",
        "asocks": f"{cc} ASocks 代理开通中",
        "iproyal": f"{cc} IPRoyal 住宅ISP分配中",
    }
    endpoint = EgressEndpoint(
        region=region,
        host="(开通中)",
        port=0,
        provider=provider,
        slot_status="provisioning",
        tenant_id=tenant.id,
        label=label_map.get(provider, f"{cc} 线路开通中"),
    )
    db.add(endpoint)
    db.flush()
    job = EgressProvisionJob(
        tenant_id=tenant.id,
        endpoint_id=endpoint.id,
        provider=provider,
        region=region,
        country=cc,
        status="queued",
    )
    db.add(job)
    db.commit()
    db.refresh(endpoint)
    db.refresh(job)
    return endpoint, job


def fulfill_manual_endpoint(
    db: Session,
    endpoint_id: str,
    *,
    host: str,
    port: int,
    proxy_username: str,
    proxy_password: str,
    label: str | None = None,
    upstream_ref: str | None = None,
) -> EgressEndpoint | None:
    """超管录入真实代理（替代第三方 API 采购）。"""
    row = db.query(EgressEndpoint).filter(EgressEndpoint.id == endpoint_id).first()
    if not row:
        return None
    if row.slot_status not in ("pending_manual", "failed", "provisioning"):
        raise ValueError("仅待配置/失败/开通中槽位可录入")

    qc = {}
    if settings.EGRESS_QC_ENABLED:
        qc = run_egress_qc(host)

    row.host = host.strip()
    row.port = int(port)
    row.proxy_username = proxy_username.strip()
    row.proxy_password = proxy_password.strip()
    row.upstream_ref = upstream_ref
    row.provider = "manual"
    row.label = label or row.label or "静态 ISP"
    row.qc_meta = qc
    row.provision_error = None
    row.slot_status = "assigned"
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return row


def serialize_provision_job(job: EgressProvisionJob) -> dict[str, Any]:
    """serialize_provision_job。

    参数说明：
    :param job: 参数 job
    :return: 返回处理结果。
    """
    return {
        "id": job.id,
        "tenant_id": job.tenant_id,
        "endpoint_id": job.endpoint_id,
        "status": job.status,
        "provider": job.provider,
        "country": job.country,
        "attempts": job.attempts,
        "error_message": job.error_message,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
    }


def process_provision_job(db: Session, job_id: str) -> dict[str, Any]:
    """process_provision_job。

    参数说明：
    :param db: 参数 db
    :param job_id: 参数 job_id
    :return: 返回处理结果。
    """
    job = db.query(EgressProvisionJob).filter(EgressProvisionJob.id == job_id).first()
    if not job:
        return {"ok": False, "reason": "job_not_found"}
    if job.status in TERMINAL_JOB_STATUSES:
        return {"ok": True, "skipped": True, "status": job.status}

    endpoint = (
        db.query(EgressEndpoint).filter(EgressEndpoint.id == job.endpoint_id).first()
    )
    if not endpoint:
        job.status = "failed"
        job.error_message = "endpoint_missing"
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
        return {"ok": False, "reason": "endpoint_missing"}

    now = datetime.now(timezone.utc)
    job.status = "running"
    job.attempts = (job.attempts or 0) + 1
    job.started_at = job.started_at or now
    job.updated_at = now
    db.commit()
    try:
        provisioner = get_egress_provisioner()
        purchased = provisioner.purchase_one(country=job.country, region=job.region)
        qc = {}
        if settings.EGRESS_QC_ENABLED:
            qc = run_egress_qc(purchased.host, provider=purchased.provider)
            if qc.get("ok") is False and not qc.get("skipped"):
                raise EgressProvisionerError(
                    f"IP 质检未通过: hosting={qc.get('hosting')} proxy={qc.get('proxy')}"
                )

        endpoint.host = purchased.host
        endpoint.port = purchased.port
        endpoint.proxy_username = purchased.proxy_username
        endpoint.proxy_password = purchased.proxy_password
        endpoint.upstream_ref = purchased.upstream_ref
        endpoint.provider = purchased.provider
        endpoint.label = purchased.label or f"{job.country} ISP"
        endpoint.qc_meta = qc
        endpoint.provision_error = None
        endpoint.slot_status = "assigned"
        endpoint.updated_at = datetime.now(timezone.utc)
        # IPRoyal: 传递 expire_date 和 iproyal_order_id
        if purchased.provider == "iproyal" and purchased.raw:
            endpoint.iproyal_order_id = purchased.raw.get("iproyal_order_id")
            expire_str = purchased.raw.get("expire_date")
            if expire_str:
                try:
                    from datetime import datetime as dt
                    endpoint.expire_date = dt.fromisoformat(expire_str)
                except (ValueError, TypeError):
                    pass

        job.status = "succeeded"
        job.upstream_ref = purchased.upstream_ref
        job.error_message = None
        job.finished_at = datetime.now(timezone.utc)
        job.updated_at = job.finished_at
        db.commit()
        return {"ok": True, "status": "succeeded", "endpoint_id": endpoint.id}

    except Exception as exc:
        logger.warning("egress provision job %s failed: %s", job_id, exc)
        err = str(exc)[:480]
        endpoint.slot_status = "failed"
        endpoint.provision_error = err
        endpoint.updated_at = datetime.now(timezone.utc)
        job.status = "failed"
        job.error_message = err
        job.finished_at = datetime.now(timezone.utc)
        job.updated_at = job.finished_at
        db.commit()
        return {"ok": False, "status": "failed", "error": err}


def process_pending_provision_jobs(db: Session, *, limit: int = 20) -> dict[str, Any]:
    """process_pending_provision_jobs。

    参数说明：
    :param db: 参数 db
    :param limit: 参数 limit
    :return: 返回处理结果。
    """
    rows = (
        db.query(EgressProvisionJob)
        .filter(EgressProvisionJob.status == "queued")
        .order_by(EgressProvisionJob.created_at.asc())
        .limit(limit)
        .all()
    )
    results = []
    for job in rows:
        results.append(process_provision_job(db, str(job.id)))
    return {"processed": len(results), "results": results}


def retry_failed_slot(db: Session, tenant: Tenant, endpoint_id: str) -> dict[str, Any]:
    """retry_failed_slot。

    参数说明：
    :param db: 参数 db
    :param tenant: 参数 tenant
    :param endpoint_id: 参数 endpoint_id
    :return: 返回处理结果。
    """
    endpoint = (
        db.query(EgressEndpoint)
        .filter(
            EgressEndpoint.id == endpoint_id,
            EgressEndpoint.tenant_id == tenant.id,
        )
        .first()
    )
    if not endpoint:
        return {"ok": False, "reason": "not_found"}
    if endpoint.slot_status != "failed":
        return {"ok": False, "reason": "not_failed"}

    if is_manual_egress_mode():
        endpoint.slot_status = "pending_manual"
        endpoint.host = "(待运营配置)"
        endpoint.port = 0
        endpoint.provision_error = None
        endpoint.updated_at = datetime.now(timezone.utc)
        db.commit()
        return {"ok": True, "endpoint_id": endpoint.id, "manual": True}

    endpoint.slot_status = "provisioning"
    endpoint.host = "(开通中)"
    endpoint.port = 0
    endpoint.provision_error = None
    endpoint.updated_at = datetime.now(timezone.utc)
    job = EgressProvisionJob(
        tenant_id=tenant.id,
        endpoint_id=endpoint.id,
        provider=active_egress_provider(),
        region=endpoint.region,
        country=(settings.EGRESS_JIT_COUNTRY or "US").upper(),
        status="queued",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return {"ok": True, "job_id": job.id, "endpoint_id": endpoint.id}


def run_provision_job_background(job_id: str) -> None:
    """run_provision_job_background。

    参数说明：
    :param job_id: 参数 job_id
    :return: 返回处理结果。
    """
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        process_provision_job(db, job_id)
    except Exception as exc:
        logger.exception("Background egress provision failed %s: %s", job_id, exc)
    finally:
        db.close()


def schedule_provision_jobs(job_ids: list[str]) -> None:
    """schedule_provision_jobs。

    参数说明：
    :param job_ids: 参数 job_ids
    :return: 返回处理结果。
    """
    for jid in job_ids:
        if not jid:
            continue
        threading.Thread(
            target=run_provision_job_background,
            args=(jid,),
            daemon=True,
        ).start()


def attach_latest_job(db: Session, endpoint_id: str) -> EgressProvisionJob | None:
    """attach_latest_job。

    参数说明：
    :param db: 参数 db
    :param endpoint_id: 参数 endpoint_id
    :return: 返回处理结果。
    """
    return (
        db.query(EgressProvisionJob)
        .filter(EgressProvisionJob.endpoint_id == endpoint_id)
        .order_by(EgressProvisionJob.created_at.desc())
        .first()
    )
