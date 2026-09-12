#!/usr/bin/env python3
"""为已有租户补全 site_content.i18n（模板 + 可选 Hermes AI 翻译）。

用法（仓库根目录）:
  python scripts/backfill-site-content-i18n.py --dry-run
  python scripts/backfill-site-content-i18n.py
  python scripts/backfill-site-content-i18n.py --ai
  python scripts/backfill-site-content-i18n.py --ai --overwrite
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_BACKEND = _ROOT / "backend"
sys.path.insert(0, str(_BACKEND))

if not os.environ.get("DATABASE_URL"):
    os.chdir(_BACKEND)
    os.environ["DATABASE_URL"] = "sqlite:///./youding_dev.db"
    os.environ.setdefault("ENVIRONMENT", "development")
    os.environ["PYTHONPATH"] = str(_BACKEND)

from app.core.database import SessionLocal, rebind_engine
from app.db.session import init_db
from app.services.site_content_i18n_ai_service import backfill_tenant_site_content_i18n_async
from app.services.site_content_i18n_service import backfill_tenant_site_content_i18n


async def _run(args: argparse.Namespace) -> dict:
    rebind_engine(os.environ.get("DATABASE_URL"))
    init_db()
    db = SessionLocal()
    try:
        if args.ai:
            return await backfill_tenant_site_content_i18n_async(
                db,
                dry_run=args.dry_run,
                overwrite=args.overwrite,
                use_ai=True,
            )
        return backfill_tenant_site_content_i18n(
            db,
            dry_run=args.dry_run,
            overwrite=args.overwrite,
        )
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill tenant site_content i18n blocks")
    parser.add_argument("--dry-run", action="store_true", help="仅统计，不写入数据库")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="覆盖已有 i18n 键（AI 模式默认覆盖 AI 批次结果）",
    )
    parser.add_argument(
        "--ai",
        action="store_true",
        help="对已有正文调用 Hermes LLM 定制翻译（需 API 密钥）",
    )
    args = parser.parse_args()

    try:
        result = asyncio.run(_run(args))
        mode = "预检" if args.dry_run else "完成"
        ai_note = f"，AI 租户 {result.get('ai_tenants', 0)}" if args.ai else ""
        print(
            f"[{mode}] 扫描 {result['tenants_scanned']} 租户，"
            f"更新 {result['tenants_updated']}，"
            f"补字段 {result['fields_added_total']}{ai_note}，"
            f"无 site_content {result['skipped_no_site']}",
        )
        report_path = _ROOT / "docs" / "site-content-i18n-backfill-latest.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(f"失败: {exc}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
