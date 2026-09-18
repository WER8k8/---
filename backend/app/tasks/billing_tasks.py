# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
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


@shared_task(name="app.tasks.billing_tasks.billing_reconcile_patrol", ignore_result=False)
def billing_reconcile_patrol() -> dict:
    """对账巡检（P4 验收：计量 vs 账本误差 0）。

    一次巡检 = 先汇总未入账计量事件，再全库对账并返回结论。
    error_free=False 时会经 meter_event.reconcile 主动打 error 级日志告警。
    供 Celery beat 周期调用；也可直接命令行调用以手动触发巡检。
    """
    from app.core.database import SessionLocal
    from app.services.billing.meter_event import MeterEventService

    try:
        with SessionLocal() as db:
            svc = MeterEventService(db)
            agg = svc.aggregate_to_billing()
            rep = svc.reconcile()
            return {
                "aggregated": {
                    "token_events": agg["token_events"],
                    "token_delta": agg["token_delta"],
                    "finance_events": agg["finance_events"],
                    "finance_cents": agg["finance_cents"],
                },
                "window_start": rep["window_start"],
                "window_end": rep["window_end"],
                "ai_generation": rep["ai_generation"],
                "revenue": rep["revenue"],
                "pending_events": rep["pending_events"],
                "discrepancies": rep["discrepancies"],
                "error_free": rep["error_free"],
            }
    except Exception as exc:  # noqa: BLE001
        logger.exception("billing_reconcile_patrol failed")
        return {"error": str(exc), "error_free": False}


def run_billing_reconcile_patrol_sync() -> dict:
    """同步执行一次对账巡检（Celery 之外直接调用，供自检/运维手动触发）。"""
    return billing_reconcile_patrol.run()
