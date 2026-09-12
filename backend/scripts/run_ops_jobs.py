#!/usr/bin/env python3
"""运维批处理：租户到期冻结 + AI 成本归集（供 cron / 手动）。"""

import argparse
import logging

logger = logging.getLogger(__name__)

import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("JWT_SECRET_KEY", "ops-job-" + "x" * 32)

from app.db.session import SessionLocal
from app.services.finance_service import FinanceService
from app.services.tenant_lifecycle_service import TenantLifecycleService
from app.workers.publish_worker import run_process_pending_tasks


def main() -> int:
    parser = argparse.ArgumentParser(description="Run ops batch jobs")
    parser.add_argument(
        "--job",
        choices=["tenant-expiry", "ai-costs", "publish-worker", "nvidia-probe", "hermes-patrol", "hermes-ops", "deerflow-schedule", "trade-intel-refresh", "all"],
        default="all",
    )
    parser.add_argument("--publish-limit", type=int, default=20)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.job in ("tenant-expiry", "all"):
            out = TenantLifecycleService(db).run_all(dry_run=args.dry_run)
            logger.info('"tenant-expiry:", out')
        if args.job in ("ai-costs", "all"):
            out = FinanceService(db).sync_ai_model_costs(dry_run=args.dry_run)
            logger.info('"ai-costs:", out')
        if args.job in ("publish-worker", "all"):
            if args.dry_run:
                logger.info('"publish-worker:", {"skipped": True, "dry_run": True}', "skipped": True, "dry_run": True)
            else:
                out = run_process_pending_tasks(db, limit=args.publish_limit)
                logger.info('"publish-worker:", out')
        if args.job in ("nvidia-probe", "all"):
            if args.dry_run:
                logger.info('"nvidia-probe:", {"skipped": True, "dry_run": True}', "skipped": True, "dry_run": True)
            else:
                from app.services.nvidia_customer_probe_service import (
                    run_nvidia_customer_model_probe,
                )

                out = run_nvidia_customer_model_probe(db, trigger="ops_cli")
                logger.info(
                    "nvidia-probe: %s",
                    {
                        "healthy": out.get("healthy_count"),
                        "total": out.get("total"),
                        "saved_at": out.get("saved_at"),
                    },
                )
        if args.job in ("hermes-patrol", "all"):
            if args.dry_run:
                logger.info('"hermes-patrol:", {"skipped": True, "dry_run": True}', "skipped": True, "dry_run": True)
            else:
                from app.services.hermes.site_patrol_service import run_site_patrol

                out = run_site_patrol(db, trigger="ops_cli")
                logger.info(
                    "hermes-patrol: %s",
                    {
                        "overall": out.get("overall_status"),
                        "pass": out.get("pass_count"),
                        "fail": out.get("fail_count"),
                        "saved_at": out.get("saved_at"),
                    },
                )
        if args.job in ("hermes-ops", "all"):
            if args.dry_run:
                logger.info('"hermes-ops:", {"skipped": True, "dry_run": True}', "skipped": True, "dry_run": True)
            else:
                from app.core.config import settings
                from app.services.hermes.ops_autopilot import run_full_ops_cycle

                if args.job == "all" and not settings.hermes_ops_autopilot_active:
                    logger.info('"hermes-ops:", {"skipped": True, "reason": "autopilot_disabled"}', "skipped": True, "reason": "autopilot_disabled")
                else:
                    out = run_full_ops_cycle(db, trigger="ops_cli")
                    patrol = out.get("patrol") or {}
                    logger.info(
                        "hermes-ops: %s",
                        {
                            "overall": patrol.get("overall_status"),
                            "pass": patrol.get("pass_count"),
                            "fail": patrol.get("fail_count"),
                            "tech_high": (out.get("tech_radar") or {}).get("high_impact_count"),
                            "saved_at": out.get("saved_at"),
                        },
                    )
        if args.job in ("deerflow-schedule", "all"):
            if args.dry_run:
                logger.info('"deerflow-schedule:", {"skipped": True, "dry_run": True}', "skipped": True, "dry_run": True)
            else:
                from app.services.ubrain.deerflow_scheduled_service import run_scheduled_deerflow_update

                out = run_scheduled_deerflow_update(db, trigger="ops_cli", force=True)
                logger.info(
                    "deerflow-schedule: %s",
                    {
                        "tenants": out.get("tenant_count"),
                        "enqueued": out.get("enqueued_count"),
                        "errors": len(out.get("errors") or []),
                        "saved_at": out.get("saved_at"),
                    },
                )
        if args.job in ("trade-intel-refresh", "all"):
            if args.dry_run:
                logger.info('"trade-intel-refresh:", {"skipped": True, "dry_run": True}', "skipped": True, "dry_run": True)
            else:
                from app.services.trade_intel_scheduler import trade_intel_scheduler

                out = trade_intel_scheduler.run_once(trigger="ops_cli")
                logger.info(
                    "trade-intel-refresh: %s",
                    {
                        "rows_updated": out.get("rows_updated"),
                        "rows_fallback": out.get("rows_fallback"),
                        "years": out.get("years"),
                        "errors": len(out.get("errors") or []),
                        "saved_at": out.get("saved_at"),
                    },
                )
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
