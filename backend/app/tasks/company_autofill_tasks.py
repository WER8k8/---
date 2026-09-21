# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P1-8 收尾：询盘域名 → 公司档案 每日兜底回填。

为什么需要兜底：
    询盘创建时的自动建档钩子是 **best-effort**（try/except 吞异常，绝不影响询盘创建），
    一旦因故失败不会报错、只会静默漏档。本任务每日扫一遍存量询盘补齐，
    保证 companies 档案与询盘域名最终一致（幂等，可重复跑）。
"""
from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="app.tasks.company_autofill_tasks.company_autofill_backfill_daily", ignore_result=False)
def company_autofill_backfill_daily(tenant_id: str = "", limit: int = 5000) -> dict:
    """每日回填：把尚未建档案的询盘域名补成 companies 记录。"""
    from app.core.database import SessionLocal
    from app.services.acquisition.company_autofill import backfill_from_inquiries

    try:
        with SessionLocal() as db:
            summary = backfill_from_inquiries(db, tenant_id=tenant_id, limit=limit, dry_run=False)
        summary["error"] = False
        return summary
    except Exception:  # noqa: BLE001
        logger.exception("company_autofill_backfill_daily failed")
        return {"error": True, "created": 0}
