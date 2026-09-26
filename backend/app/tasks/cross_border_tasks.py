# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""跨境语言桥 Celery 任务。"""

from __future__ import annotations

import logging
import os

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="cross_border.run_job",
    max_retries=2,
    default_retry_delay=60,
    queue="cross_border",
)
def cross_border_run_job(self, job_id: str):
    """cross_border_run_job。

    参数说明：
    :param self: 参数 self
    :param job_id: 参数 job_id
    :return: 返回处理结果。
    """
    from app.core.database import SessionLocal
    from app.services.cross_border.cross_border_worker import run_cross_border_job
    db = SessionLocal()
    try:
        return run_cross_border_job(db, job_id)
    except Exception as exc:
        logger.exception("cross_border_run_job failed %s", job_id)
        raise self.retry(exc=exc) from exc
    finally:
        db.close()


def dispatch_by_job_id(job_id: str) -> bool:
    """尝试 Celery 入队；成功返回 True。"""
    from app.core.config import settings
    if not settings.REDIS_ENABLED:
        return False
    broker = (settings.CELERY_BROKER_URL or "").strip()
    if not broker:
        return False
    cross_border_run_job.delay(job_id)
    return True


@shared_task(name="cross_border.imap_inquiry_poll", queue="cross_border")
def imap_inquiry_poll(max_messages: int = 10):
    """IMAP 只读收件箱定时收取 → 询盘（W3 · 邮件入站自动闭环）。

    设计要点：
    - **仅只读收取**，不自动回复、不发信（沿用 sidecar 语义）。
    - 需 sidecar 已配置（``IMAP_INQUIRY_URL``）且**显式声明允许自动收取的租户**
      （``IMAP_INQUIRY_TENANTS``，逗号分隔的租户 domain/id）。任一缺失即
      **诚实跳过**并返回原因，绝不静默空跑（避免绕过人工授权）。
    - 幂等：入库层按 message_id 去重（``_already_ingested``），重跑不重复建询盘。
    """
    sidecar = (os.getenv("IMAP_INQUIRY_URL") or "").strip()
    if not sidecar:
        return {"ok": False, "error_code": "IMAP_INQUIRY_NOT_CONFIGURED", "tenants": 0, "ingested": 0}

    allow = [x.strip() for x in (os.getenv("IMAP_INQUIRY_TENANTS") or "").split(",") if x.strip()]
    if not allow:
        return {"ok": False, "error_code": "IMAP_INQUIRY_NO_OPTED_TENANTS", "tenants": 0, "ingested": 0}

    from sqlalchemy import or_

    from app.core.database import SessionLocal
    from app.models.tenant import Tenant
    from app.services.cross_border.imap_inquiry_ingest_service import (
        poll_and_ingest_imap_inquiries,
    )

    db = SessionLocal()
    try:
        q = db.query(Tenant).filter(Tenant.is_active.is_(True))
        # 允许用 domain 或 name 声明（与 resolve_tenant_uuid 的别名口径一致）
        q = q.filter(or_(Tenant.domain.in_(allow), Tenant.name.in_(allow)))
        tenants = q.limit(200).all()
        agg = {"ok": True, "tenants": len(tenants), "ingested": 0, "skipped": 0, "errors": []}
        for t in tenants:
            try:
                r = poll_and_ingest_imap_inquiries(db, tenant=t, max_messages=int(max_messages or 10))
                agg["ingested"] += int(r.get("ingested") or 0)
                agg["skipped"] += int(r.get("skipped") or 0)
                if not r.get("ok"):
                    agg["errors"].append(f"{t.id}: {r.get('error_code') or r.get('note') or 'poll_failed'}")
            except Exception as exc:  # noqa: BLE001
                logger.warning("imap_inquiry_poll tenant=%s 失败: %s", getattr(t, "id", ""), exc)
                agg["errors"].append(f"{getattr(t, 'id', '')}: {str(exc)[:120]}")
        agg["errors"] = agg["errors"][:5]
        return agg
    finally:
        db.close()
