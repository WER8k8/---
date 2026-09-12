"""一次性清除平台池中遗留的演示/占位 egress 数据。"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.core.database import SessionLocal
from app.db.seed import _purge_demo_egress_pool


def main() -> None:
    db = SessionLocal()
    try:
        removed = _purge_demo_egress_pool(db)
        db.commit()
        logger.info('purged_demo_endpoints={removed}', removed)
    finally:
        db.close()


if __name__ == "__main__":
    main()
