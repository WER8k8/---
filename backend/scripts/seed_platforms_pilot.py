#!/usr/bin/env python3
"""试点 5+10 平台主数据（cn 5 + 海外十大社交/IM）。"""

import os
import logging

logger = logging.getLogger(__name__)

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("JWT_SECRET_KEY", "seed-script-" + "x" * 32)

if os.getenv("DEMO_USE_PRODUCTION_DB") != "1":
    demo_db = BACKEND / "data" / "demo_acceptance.db"
    demo_db.parent.mkdir(parents=True, exist_ok=True)
    os.environ["DATABASE_URL"] = f"sqlite:///{demo_db.as_posix()}"

import app.models  # noqa: F401 — 注册全部 ORM 映射

from app.core.database import SessionLocal, engine, Base
from app.models.content import Platform
from app.services.platform_catalog import (
    CORE_GLOBAL_SOCIAL_10,
    PILOT_CN_NAMES,
    all_catalog_rows,
    upsert_platforms,
)


def main() -> None:
    Base.metadata.create_all(bind=engine, tables=[Platform.__table__])
    db = SessionLocal()
    try:
        pilot_rows = [
            row
            for row in all_catalog_rows()
            if row[0] in set(PILOT_CN_NAMES) | set(CORE_GLOBAL_SOCIAL_10)
        ]
        stats = upsert_platforms(db, pilot_rows)
        logger.info(
            f"OK: pilot platforms upserted "
            f"(cn={len(PILOT_CN_NAMES)} global={len(CORE_GLOBAL_SOCIAL_10)} stats={stats})"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
