#!/usr/bin/env python3
"""租户生命周期定时任务 — 到期冻结 + 续费提醒。

import logging

logger = logging.getLogger(__name__)

用法:
  python scripts/run_tenant_lifecycle.py
  python scripts/run_tenant_lifecycle.py --dry-run
  python scripts/run_tenant_lifecycle.py --notify-only
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("JWT_SECRET_KEY", "lifecycle-cron-" + "x" * 24)

from app.db.session import SessionLocal
from app.services.tenant_lifecycle_service import TenantLifecycleService
from app.services.tenant_renewal_notify_service import TenantRenewalNotifyService


def main() -> int:
    parser = argparse.ArgumentParser(description="租户订阅/试用到期处理 + 续费提醒")
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不写入/不发送")
    parser.add_argument("--notify-only", action="store_true", help="仅发送续费提醒，不冻结")
    parser.add_argument("--within-days", type=int, default=7, help="续费提醒窗口（天）")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        result: dict = {}
        if not args.notify_only:
            result["lifecycle"] = TenantLifecycleService(db).run_all(dry_run=args.dry_run)
        result["renewal_notify"] = TenantRenewalNotifyService(db).notify_expiring(
            within_days=args.within_days,
            dry_run=args.dry_run,
        )
        logger.info(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
