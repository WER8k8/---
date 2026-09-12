#!/usr/bin/env python3
"""为已有租户补全 SEO 矩阵 platform_accounts 占位行。

用法（仓库根目录）:
  python scripts/backfill_tenant_platform_accounts.py
  python scripts/backfill_tenant_platform_accounts.py --dry-run
"""

from __future__ import annotations

import argparse
import os
import sys

_ROOT = os.path.join(os.path.dirname(__file__), "..")
_BACKEND = os.path.join(_ROOT, "backend")
sys.path.insert(0, _BACKEND)

# 与 start-dev-admin.ps1 一致：脚本默认使用 backend 下 SQLite
if not os.environ.get("DATABASE_URL"):
    os.chdir(_BACKEND)
    os.environ["DATABASE_URL"] = "sqlite:///./youding_dev.db"
    os.environ.setdefault("ENVIRONMENT", "development")
    os.environ["PYTHONPATH"] = _BACKEND

from app.core.database import SessionLocal, rebind_engine
from app.db.session import _ensure_platform_account_columns, init_db
from app.services.tenant_onboarding_service import backfill_tenant_platform_stubs


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill tenant platform account stubs")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅统计将创建的行数，不写入数据库",
    )
    args = parser.parse_args()

    rebind_engine(os.environ.get("DATABASE_URL"))
    init_db()
    _ensure_platform_account_columns()
    db = SessionLocal()
    try:
        result = backfill_tenant_platform_stubs(db, dry_run=args.dry_run)
        mode = "预检" if args.dry_run else "完成"
        print(
            f"[{mode}] 扫描租户 {result['tenants_scanned']} 个，"
            f"涉及更新 {result['tenants_updated']} 个，"
            f"新建账号占位 {result['accounts_created']} 条",
        )
        return 0
    except Exception as exc:
        print(f"失败: {exc}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
