#!/usr/bin/env python3
"""生产环境迁移与种子数据（Sprint H）。

import logging

logger = logging.getLogger(__name__)

用法:
  cd backend
  set DATABASE_URL=postgresql+psycopg2://...
  python scripts/migrate_production.py
  python scripts/migrate_production.py --seed-full
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]


def _run(cmd: list[str]) -> int:
    logger.info('"+", " ".join(cmd)')
    return subprocess.call(cmd, cwd=str(BACKEND))


def main() -> int:
    parser = argparse.ArgumentParser(description="生产库 Alembic + 平台 seed")
    parser.add_argument("--seed-pilot", action="store_true", help="仅 5+5 试点")
    parser.add_argument("--seed-full", action="store_true", help="40 平台全量")
    parser.add_argument("--skip-alembic", action="store_true")
    args = parser.parse_args()

    if not os.getenv("DATABASE_URL"):
        logger.info('"WARN: DATABASE_URL 未设置，将使用 .env / 默认配置",')

    code = 0
    if not args.skip_alembic:
        code = _run([sys.executable, "-m", "alembic", "upgrade", "head"])
        if code != 0:
            return code

    if args.seed_full or (not args.seed_pilot and not args.seed_full):
        code = _run([sys.executable, str(BACKEND / "scripts" / "seed_platforms_full.py")])
    elif args.seed_pilot:
        code = _run([sys.executable, str(BACKEND / "scripts" / "seed_platforms_pilot.py")])

    return code


if __name__ == "__main__":
    raise SystemExit(main())
