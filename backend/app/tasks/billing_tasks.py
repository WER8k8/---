"""轮22：计量周期汇总任务（总纲 §4.6-8：Celery beat 汇总进现有计费）。

仅将 meter_events 中未汇总事件并入既有计费账本（token_ledger / finance_ledger），
幂等（aggregated_at 去重）；红线 R3 不新建任何计费账本。
"""

from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="app.tasks.billing_tasks.aggregate_meter_events", ignore_result=False)
def aggregate_meter_events() -> dict:
    """汇总所有租户未入账的计量事件（平台级批量，Celery beat 周期调用）。"""
    from app.core.database import SessionLocal
    from app.services.billing.meter_event import MeterEventService

    try:
        with SessionLocal() as db:
            svc = MeterEventService(db)
            return svc.aggregate_to_billing()
    except Exception:  # noqa: BLE001
        logger.exception("aggregate_meter_events failed")
        return {"token_events": 0, "token_delta": 0,
                "finance_events": 0, "finance_cents": 0}
