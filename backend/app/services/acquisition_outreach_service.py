# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""获客邮件序列 — 复用 EmailOutreach，经 JobGateway 真发。"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.email_outreach import EmailOutreach, EmailStatus

logger = logging.getLogger(__name__)

JOB_TYPE_EMAIL_STEP = "outreach.email_step"


def _now() -> datetime:
    """_now。
    :return: 返回处理结果。
    """
    return datetime.now(timezone.utc)


def _from_email() -> str:
    """_from_email。
    :return: 返回处理结果。
    """
    return (
        (getattr(settings, "SMTP_FROM_EMAIL", None) or "").strip()
        or (getattr(settings, "FROM_EMAIL", None) or "").strip()
        or "noreply@localhost"
    )


def _serialize_row(row: EmailOutreach) -> dict[str, Any]:
    """_serialize_row。

    参数说明：
    :param row: 参数 row
    :return: 返回处理结果。
    """
    status = row.status.value if hasattr(row.status, "value") else str(row.status)
    return {
        "id": str(row.id),
        "sequence_id": row.sequence_id,
        "sequence_step": row.sequence_step,
        "sequence_total_steps": row.sequence_total_steps,
        "to_email": row.to_email,
        "subject": row.subject,
        "status": status,
        "provider": row.provider,
        "provider_message_id": row.provider_message_id,
        "scheduled_at": row.scheduled_at.isoformat() if row.scheduled_at else None,
        "sent_at": row.sent_at.isoformat() if row.sent_at else None,
        "outreach_metadata": row.outreach_metadata or {},
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def create_sequence(
    db: Session,
    *,
    tenant_id: str | None,
    user_id: str | None,
    to_email: str,
    steps: list[dict[str, Any]],
    prospect_label: str = "",
) -> dict[str, Any]:
    """创建 draft 序列步骤（不发送）。steps: [{subject, html_body|body, delay_days?}]"""
    if not to_email or "@" not in to_email:
        raise ValueError("to_email_invalid")
    if not steps:
        raise ValueError("steps_required")
    if len(steps) > 10:
        raise ValueError("steps_max_10")

    sequence_id = str(uuid.uuid4())
    total = len(steps)
    base = _now()
    rows: list[EmailOutreach] = []
    for idx, step in enumerate(steps):
        subject = str(step.get("subject") or "").strip()
        html_body = str(step.get("html_body") or step.get("body") or "").strip()
        if not subject or not html_body:
            raise ValueError(f"step_{idx}_subject_or_body_required")
        delay_days = int(step.get("delay_days") or idx)
        scheduled = base + timedelta(days=max(0, delay_days))
        idem = hashlib.sha256(f"{sequence_id}:{idx}:{to_email}".encode()).hexdigest()[:64]
        row = EmailOutreach(
            id=str(uuid.uuid4()),
            idempotency_key=idem,
            tenant_id=tenant_id,
            user_id=user_id,
            from_email=_from_email(),
            from_name=getattr(settings, "SMTP_FROM_NAME", None) or "YouDing SaaS",
            to_email=to_email.strip().lower(),
            subject=subject[:500],
            html_body=html_body,
            text_body=str(step.get("text_body") or ""),
            status=EmailStatus.DRAFT,
            sequence_id=sequence_id,
            sequence_step=idx,
            sequence_total_steps=total,
            scheduled_at=scheduled,
            outreach_metadata={
                "prospect_label": prospect_label,
                "phase": "1B",
            },
        )
        db.add(row)
        rows.append(row)
    db.commit()
    for row in rows:
        db.refresh(row)
    return {
        "sequence_id": sequence_id,
        "to_email": to_email.strip().lower(),
        "total_steps": total,
        "status": "draft",
        "steps": [_serialize_row(r) for r in rows],
    }


def list_sequences(db: Session, *, tenant_id: str | None, limit: int = 50) -> dict[str, Any]:
    """list_sequences。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param limit: 参数 limit
    :return: 返回处理结果。
    """
    q = db.query(EmailOutreach).filter(EmailOutreach.sequence_id.isnot(None))
    if tenant_id:
        q = q.filter(EmailOutreach.tenant_id == tenant_id)
    rows = q.order_by(EmailOutreach.created_at.desc()).limit(max(1, min(limit, 200))).all()
    by_seq: dict[str, list[EmailOutreach]] = {}
    for row in rows:
        sid = str(row.sequence_id)
        by_seq.setdefault(sid, []).append(row)
    items = []
    for sid, seq_rows in by_seq.items():
        seq_rows = sorted(seq_rows, key=lambda r: int(r.sequence_step or 0))
        statuses = [
            (r.status.value if hasattr(r.status, "value") else str(r.status)) for r in seq_rows
        ]
        items.append(
            {
                "sequence_id": sid,
                "to_email": seq_rows[0].to_email,
                "total_steps": seq_rows[0].sequence_total_steps,
                "statuses": statuses,
                "steps": [_serialize_row(r) for r in seq_rows],
            }
        )
    return {"items": items, "total": len(items)}


def get_sequence(db: Session, *, sequence_id: str, tenant_id: str | None) -> dict[str, Any] | None:
    """get_sequence。

    参数说明：
    :param db: 参数 db
    :param sequence_id: 参数 sequence_id
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    q = db.query(EmailOutreach).filter(EmailOutreach.sequence_id == sequence_id)
    if tenant_id:
        q = q.filter(EmailOutreach.tenant_id == tenant_id)
    rows = q.order_by(EmailOutreach.sequence_step.asc()).all()
    if not rows:
        return None
    return {
        "sequence_id": sequence_id,
        "to_email": rows[0].to_email,
        "total_steps": rows[0].sequence_total_steps,
        "steps": [_serialize_row(r) for r in rows],
    }


def confirm_and_enqueue(
    db: Session,
    *,
    sequence_id: str,
    tenant_id: str | None,
    created_by: str | None = None,
    enqueue: bool = True,
) -> dict[str, Any]:
    """将到期/首步 draft → queued，并经 JobGateway 入队。"""
    from app.services.acquisition_capability_registry import _email_sequence_status
    email_cap = _email_sequence_status()
    if email_cap.get("status") != "ready":
        # 生产未配 → 禁止入队；开发可入队，worker 会 stamp_mock 且不标 delivered
        import os
        env = (os.getenv("ENVIRONMENT") or "development").strip().lower()
        if env == "production":
            raise ValueError("EMAIL_NOT_CONFIGURED")
    pack = get_sequence(db, sequence_id=sequence_id, tenant_id=tenant_id)
    if not pack:
        raise KeyError("sequence_not_found")

    rows = (
        db.query(EmailOutreach)
        .filter(
            EmailOutreach.sequence_id == sequence_id,
            EmailOutreach.status == EmailStatus.DRAFT,
        )
        .order_by(EmailOutreach.sequence_step.asc())
        .all()
    )
    if not rows:
        raise ValueError("no_draft_steps")

    now = _now()
    # 仅立即入队已到点的步骤；其余保持 draft 等 Beat 扫描
    due = [r for r in rows if r.scheduled_at is None or r.scheduled_at <= now]
    if not due:
        due = [rows[0]]  # 至少排队第一步（允许提前确认）

    job_ids: list[str] = []
    for row in due:
        row.status = EmailStatus.QUEUED
        db.add(row)
    db.commit()
    if enqueue:
        from app.services.job_gateway import JobGateway
        from app.tasks.ops_scheduler_tasks import run_platform_job
        gw = JobGateway(db)
        for row in due:
            jid = gw.submit(
                JOB_TYPE_EMAIL_STEP,
                tenant_id=tenant_id,
                payload={"outreach_id": str(row.id), "sequence_id": sequence_id},
                created_by=created_by,
                enqueue=True,
                celery_task=run_platform_job,
            )
            job_ids.append(jid)

    return {
        "sequence_id": sequence_id,
        "queued_step_ids": [str(r.id) for r in due],
        "job_ids": job_ids,
        "remaining_draft": max(0, len(rows) - len(due)),
        "email_capability": email_cap.get("status"),
        "mode": "live" if email_cap.get("status") == "ready" else "mock",
    }


def send_outreach_step(db: Session, *, outreach_id: str) -> dict[str, Any]:
    """执行单步发送（Celery/JobGateway worker 调用）。"""
    row = db.query(EmailOutreach).filter(EmailOutreach.id == outreach_id).first()
    if not row:
        raise KeyError("outreach_not_found")

    status = row.status.value if hasattr(row.status, "value") else str(row.status)
    if status in ("sent", "delivered", "opened", "clicked"):
        return {
            "ok": True,
            "idempotent": True,
            "outreach_id": outreach_id,
            "status": status,
            "provider_message_id": row.provider_message_id,
        }
    if status == "cancelled":
        return {"ok": False, "error_code": "OUTREACH_CANCELLED", "outreach_id": outreach_id}

    row.status = EmailStatus.SENDING
    db.add(row)
    db.commit()
    import asyncio
    from app.services.email_service import send_email
    try:
        result = asyncio.run(
            send_email(
                to=row.to_email,
                subject=row.subject,
                html_body=row.html_body,
                text_body=row.text_body or "",
            )
        )
    except Exception as exc:
        logger.exception("outreach send failed id=%s", outreach_id)
        row.status = EmailStatus.FAILED
        meta = dict(row.outreach_metadata or {})
        meta["last_error"] = str(exc)[:500]
        row.outreach_metadata = meta
        db.add(row)
        db.commit()
        return {"ok": False, "error_code": "EMAIL_SEND_FAILED", "error": str(exc)[:300]}

    if not result.get("success"):
        row.status = EmailStatus.FAILED
        meta = dict(row.outreach_metadata or {})
        meta["last_error"] = result.get("error") or result.get("error_code") or "send_failed"
        meta["last_result"] = {k: result.get(k) for k in ("error_code", "error", "mode", "method")}
        row.outreach_metadata = meta
        db.add(row)
        db.commit()
        return {
            "ok": False,
            "error_code": result.get("error_code") or "EMAIL_SEND_FAILED",
            "result": result,
        }

    # 开发 mock：禁止标「已送达」终态；仅标 sent + mode=mock
    mode = result.get("mode")
    row.provider = str(result.get("method") or "smtp")
    row.provider_message_id = str(
        result.get("message_id") or result.get("id") or f"local-{row.id}"
    )[:255]
    row.sent_at = _now()
    meta = dict(row.outreach_metadata or {})
    if mode == "mock":
        meta["mode"] = "mock"
        meta["mock_reason"] = result.get("mock_reason") or "email_not_configured_dev"
        # 不进入 delivered
        row.status = EmailStatus.SENT
    else:
        row.status = EmailStatus.SENT
    row.outreach_metadata = meta
    db.add(row)
    db.commit()
    return {
        "ok": True,
        "outreach_id": outreach_id,
        "status": row.status.value if hasattr(row.status, "value") else str(row.status),
        "provider": row.provider,
        "provider_message_id": row.provider_message_id,
        "mode": mode,
    }


def enqueue_due_steps(db: Session, *, limit: int = 50) -> dict[str, Any]:
    """Beat 扫描：到期 draft → queued + JobGateway。"""
    now = _now()
    rows = (
        db.query(EmailOutreach)
        .filter(
            EmailOutreach.status == EmailStatus.DRAFT,
            EmailOutreach.sequence_id.isnot(None),
            EmailOutreach.scheduled_at.isnot(None),
            EmailOutreach.scheduled_at <= now,
        )
        .order_by(EmailOutreach.scheduled_at.asc())
        .limit(max(1, min(limit, 200)))
        .all()
    )
    if not rows:
        return {"queued": 0, "job_ids": []}

    from app.services.job_gateway import JobGateway
    from app.tasks.ops_scheduler_tasks import run_platform_job
    gw = JobGateway(db)
    job_ids: list[str] = []
    for row in rows:
        row.status = EmailStatus.QUEUED
        db.add(row)
    db.commit()
    for row in rows:
        jid = gw.submit(
            JOB_TYPE_EMAIL_STEP,
            tenant_id=str(row.tenant_id) if row.tenant_id else None,
            payload={"outreach_id": str(row.id), "sequence_id": row.sequence_id},
            enqueue=True,
            celery_task=run_platform_job,
        )
        job_ids.append(jid)
    return {"queued": len(rows), "job_ids": job_ids}
