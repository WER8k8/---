# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""获客邮件序列 — 复用 EmailOutreach，经 JobGateway 真发。"""

from __future__ import annotations

import hashlib
import logging
import os
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


# ── 序列停机条件（模块7 · T7-b，docs/模块7-TradeAI序列停机条件收口契约-2026-09-28.md）──
# 判据：① suppressed（suppression 服务，全局合规闸）② manual/replied/unsubscribed/bounced
# （metadata.sequence_stopped）③ 同序列硬退 ④ 软退 ×2（可联性降级）。
# 红线：manual stop 后禁止任何路径自动重启（confirm/enqueue/send 三处均拦）。


def stop_sequence(
    db: Session,
    sequence_id: str,
    *,
    reason: str,
    stopped_by: str | None = None,
    source: str = "manual",
) -> dict[str, Any]:
    """停机写入：标记序列全部步骤 + 取消非终态步骤（幂等，不覆盖首个 stop 记录）。"""
    rows = (
        db.query(EmailOutreach)
        .filter(EmailOutreach.sequence_id == sequence_id)
        .all()
    )
    if not rows:
        return {
            "sequence_id": sequence_id, "exists": False,
            "cancelled_steps": 0, "marked_steps": 0, "reason": reason,
        }
    now_iso = _now().isoformat()
    cancelled = 0
    marked = 0
    for row in rows:
        meta = dict(row.outreach_metadata or {})
        if "sequence_stopped" in meta:
            continue
        meta["sequence_stopped"] = {
            "reason": reason,
            "stopped_by": stopped_by,
            "source": source,
            "at": now_iso,
        }
        row.outreach_metadata = meta
        marked += 1
        status = row.status.value if hasattr(row.status, "value") else str(row.status)
        if status in ("draft", "queued"):
            row.transition(EmailStatus.CANCELLED)
            cancelled += 1
        db.add(row)
    db.commit()
    return {
        "sequence_id": sequence_id,
        "exists": True,
        "cancelled_steps": cancelled,
        "marked_steps": marked,
        "reason": reason,
    }


def _sequence_stopped_reason(db: Session, row: EmailOutreach) -> str | None:
    """序列停止判定（契约 §2 判定序）。命中返回停机码；未命中返回 None。"""
    # ① 全局 suppression（tenant+email 粒度，复用既有服务，勿建第二套）
    try:
        from app.services.acquisition.suppression_list import suppression_store

        verdict = suppression_store.check_outreach(
            email=row.to_email,
            tenant_id=str(row.tenant_id) if row.tenant_id else "demo",
            channel="email",
            mode="send",
        )
        if not verdict.get("allowed", True):
            return "suppressed"
    except Exception as exc:  # noqa: BLE001 —— suppression 基础设施故障按 fail-closed 处理？
        # 不 fail-closed：基础设施故障不得静默吞掉全部发送能力；降级放行并留痕（P2 登记）
        logger.warning("suppression check failed（降级放行）id=%s: %s", getattr(row, "id", ""), exc)

    meta = dict(row.outreach_metadata or {})
    # ② 序列级停止标记（manual / replied_positive / unsubscribed / bounced_*）
    stopped = meta.get("sequence_stopped")
    if isinstance(stopped, dict) and stopped.get("reason"):
        return str(stopped.get("reason"))
    if row.sequence_id:
        # ③ 同序列存在硬退 → 停
        hard = (
            db.query(EmailOutreach.id)
            .filter(
                EmailOutreach.sequence_id == row.sequence_id,
                EmailOutreach.bounce_type == "hard",
            )
            .first()
        )
        if hard is not None:
            return "bounced_hard"
    # ④ 软退 ×2 → 可联性降级停
    if int(meta.get("soft_bounce_count") or 0) >= 2:
        return "bounced_soft"
    return None


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


def _email_capability_status() -> dict[str, Any]:
    """邮件序列能力状态。优先取能力注册表；该模块缺失时按 SMTP 配置诚实判定。

    （2026-09-28 实测：acquisition_capability_registry 模块在仓内不存在，
    既有 confirm_and_enqueue 一调即 ImportError——本防御分支修复该既有死路径。）
    """
    try:
        from app.services.acquisition_capability_registry import _email_sequence_status

        return _email_sequence_status()
    except Exception:  # noqa: BLE001 —— 模块缺失走本地判定
        smtp_host = (getattr(settings, "SMTP_HOST", None) or "").strip()
        env = (os.getenv("ENVIRONMENT") or "development").strip().lower()
        if smtp_host:
            return {"status": "ready", "source": "smtp_env"}
        if env == "production":
            return {"status": "not_configured", "source": "fallback"}
        return {"status": "mock", "source": "fallback"}


def confirm_and_enqueue(
    db: Session,
    *,
    sequence_id: str,
    tenant_id: str | None,
    created_by: str | None = None,
    enqueue: bool = True,
) -> dict[str, Any]:
    """将到期/首步 draft → queued，并经 JobGateway 入队。"""
    email_cap = _email_capability_status()
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

    # 红线（模块7 T7-b）：stopped 序列不可经确认通道重启
    keep: list[EmailOutreach] = []
    stop_codes: list[str] = []
    for r in rows:
        code = _sequence_stopped_reason(db, r)
        if code:
            stop_codes.append(code)
            if r.status == EmailStatus.DRAFT:
                r.transition(EmailStatus.CANCELLED)
                db.add(r)
        else:
            keep.append(r)
    if stop_codes:
        db.commit()
    if not keep:
        raise ValueError("sequence_stopped")

    now = _now()
    # 仅立即入队已到点的步骤；其余保持 draft 等 Beat 扫描
    due = [r for r in keep if r.scheduled_at is None or r.scheduled_at <= now]
    if not due:
        due = [keep[0]]  # 至少排队第一步（允许提前确认）

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
        "remaining_draft": max(0, len(keep) - len(due)),
        "email_capability": email_cap.get("status"),
        "mode": "live" if email_cap.get("status") == "ready" else "mock",
        "stopped_skipped": len(stop_codes),
    }


def _record_outreach_touch(
    db: Session,
    row: EmailOutreach,
    *,
    ok: bool,
    detail: dict[str, Any] | None = None,
) -> None:
    """W3：邮件外发触达统一留痕 ``contact_events``；失败必写原因与证据（不静默）。

    best-effort：留痕失败不影响发送主链（但会记 logger 告警）。
    """
    try:
        from app.services.acquisition.inbound_bridge import record_contact_event

        detail = detail or {}
        summary = (
            f"邮件外发成功 → {row.to_email}: {row.subject}"
            if ok
            else f"邮件外发失败 → {row.to_email}: {detail.get('error_code') or detail.get('error') or 'unknown'}"
        )
        record_contact_event(
            db,
            tenant_id=str(row.tenant_id) if row.tenant_id else "",
            channel="email",
            event_type="message",
            direction="outbound",
            lead_id=str(row.prospect_id) if getattr(row, "prospect_id", None) else "",
            summary=summary[:500],
            payload={"ok": ok, "sequence_id": row.sequence_id, "step": row.sequence_step, **detail},
            provenance_metadata={"bus": "acquisition_outreach", "outreach_id": str(row.id)},
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("outreach contact_event 留痕失败 id=%s: %s", getattr(row, "id", ""), exc)


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
        _record_outreach_touch(db, row, ok=False, detail={"error_code": "OUTREACH_CANCELLED", "stage": "cancelled"})
        return {"ok": False, "error_code": "OUTREACH_CANCELLED", "outreach_id": outreach_id}

    # 序列停机条件（模块7 T7-b）：命中即取消本步，零发送
    stop_code = _sequence_stopped_reason(db, row)
    if stop_code:
        if status in ("draft", "queued"):
            row.transition(EmailStatus.CANCELLED)
            db.add(row)
            db.commit()
        _record_outreach_touch(
            db, row, ok=False,
            detail={"error_code": "SEQUENCE_STOPPED", "stop_reason": stop_code, "stage": "stop_check"},
        )
        return {
            "ok": False,
            "error_code": "SEQUENCE_STOPPED",
            "stop_reason": stop_code,
            "outreach_id": outreach_id,
        }

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
        _record_outreach_touch(db, row, ok=False, detail={"error": str(exc)[:300], "stage": "send_exception"})
        return {"ok": False, "error_code": "EMAIL_SEND_FAILED", "error": str(exc)[:300]}

    if not result.get("success"):
        row.status = EmailStatus.FAILED
        meta = dict(row.outreach_metadata or {})
        meta["last_error"] = result.get("error") or result.get("error_code") or "send_failed"
        meta["last_result"] = {k: result.get(k) for k in ("error_code", "error", "mode", "method")}
        row.outreach_metadata = meta
        db.add(row)
        db.commit()
        _record_outreach_touch(
            db, row, ok=False,
            detail={
                "error_code": result.get("error_code"),
                "error": result.get("error"),
                "mode": result.get("mode"),
                "stage": "send_result_not_success",
            },
        )
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
    _record_outreach_touch(
        db, row, ok=True,
        detail={"mode": mode, "provider": row.provider, "provider_message_id": row.provider_message_id},
    )
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
    skipped_stopped: list[str] = []
    stopped_sequences: set[str] = set()
    for row in rows:
        # 序列停机条件（模块7 T7-b）：命中即整序列标记停机（防每轮重扫），步子不入队
        stop_code = _sequence_stopped_reason(db, row)
        if stop_code:
            skipped_stopped.append(str(row.id))
            if row.sequence_id and row.sequence_id not in stopped_sequences:
                stopped_sequences.add(row.sequence_id)
                stop_sequence(
                    db, row.sequence_id, reason=stop_code, source="enqueue_scan"
                )
            continue
        row.status = EmailStatus.QUEUED
        db.add(row)
    db.commit()
    enqueueable = [r for r in rows if str(r.id) not in skipped_stopped]
    for row in enqueueable:
        jid = gw.submit(
            JOB_TYPE_EMAIL_STEP,
            tenant_id=str(row.tenant_id) if row.tenant_id else None,
            payload={"outreach_id": str(row.id), "sequence_id": row.sequence_id},
            enqueue=True,
            celery_task=run_platform_job,
        )
        job_ids.append(jid)
    return {
        "queued": len(enqueueable),
        "job_ids": job_ids,
        "skipped_stopped": skipped_stopped,
        "stopped_sequences": sorted(stopped_sequences),
    }
