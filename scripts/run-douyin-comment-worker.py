#!/usr/bin/env python3
"""抖音评论采集 Worker — 读取批处理 JSON 并 POST 到 social-interactions Webhook。

用法（生产 cron 示例）::

  python scripts/run-douyin-comment-worker.py \\
    --batch-file /var/data/douyin-comments.json \\
    --api-base https://api.example.com

批处理 JSON 格式（数组或 JSONL）::

  [
    {
      "tenant_id": "<租户UUID>",
      "platform_post_id": "7123456789",
      "platform_comment_id": "cmt_unique_001",
      "content": "岩棉板多少钱？电话13800138000",
      "author_name": "王总"
    }
  ]

说明：评论数据须由 SAU / 抖音开放平台 / 人工导出工具产生；本脚本 **不生成假评论**。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))


def main() -> int:
    parser = argparse.ArgumentParser(description="Douyin comment batch → Webhook")
    parser.add_argument("--batch-file", default="", help="评论批处理 JSON/JSONL 文件")
    parser.add_argument("--api-base", default="http://127.0.0.1:8001", help="FastAPI 根地址")
    parser.add_argument("--secret", default="", help="Webhook 密钥（默认读环境变量）")
    parser.add_argument("--dry-run", action="store_true", help="仅校验文件，不发送")
    parser.add_argument("--pull-tenant", default="", help="从 AiToEarn/Inbox 拉取并入库（租户 UUID）")
    parser.add_argument("--pull-source", default="auto", choices=("auto", "aitoearn", "inbox"))
    args = parser.parse_args()

    if args.pull_tenant:
        import asyncio

        from app.db.session import SessionLocal
        from app.services.douyin_comment_pull_service import pull_and_ingest_for_tenant

        db = SessionLocal()
        try:
            out = asyncio.run(
                pull_and_ingest_for_tenant(db, args.pull_tenant.strip(), source=args.pull_source)
            )
            print(json.dumps(out, indent=2, ensure_ascii=False))
            return 0 if out.get("ingested", 0) > 0 or out.get("total", 0) == 0 else 1
        finally:
            db.close()

    if not args.batch_file:
        print(json.dumps({"error": "需要 --batch-file 或 --pull-tenant"}, ensure_ascii=False))
        return 2

    from app.services.douyin_comment_sync_service import load_batch_file, push_batch_via_webhook

    items = load_batch_file(args.batch_file)
    print(json.dumps({"validated": len(items), "dry_run": args.dry_run}, ensure_ascii=False))

    if args.dry_run:
        return 0

    if not items:
        print(json.dumps({"ok": True, "reason": "empty_batch"}, ensure_ascii=False))
        return 0

    out = push_batch_via_webhook(items, api_base=args.api_base, secret=args.secret or None)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if out.get("failed", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
