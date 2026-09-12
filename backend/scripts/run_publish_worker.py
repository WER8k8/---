#!/usr/bin/env python3
"""CLI: 消费发布队列。用法: python scripts/run_publish_worker.py --once [--limit 10]"""
import argparse
import logging

logger = logging.getLogger(__name__)

import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("JWT_SECRET_KEY", os.environ.get("JWT_SECRET_KEY", "worker-" + "x" * 32))

from app.db.session import SessionLocal
from app.workers.publish_worker import run_process_pending_tasks


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--once", action="store_true", help="处理一批后退出")
    p.add_argument("--limit", type=int, default=10)
    args = p.parse_args()
    if not args.once:
        logger.info('仅支持 --once；循环模式后续接入 supervisor')
        return 1
    db = SessionLocal()
    try:
        stats = run_process_pending_tasks(db, limit=args.limit)
        logger.info(stats)
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
