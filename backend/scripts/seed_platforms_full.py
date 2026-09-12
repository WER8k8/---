#!/usr/bin/env python3
"""正式 40 平台主数据（国内 20 + 海外 20）。"""

import os
import logging

logger = logging.getLogger(__name__)

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("JWT_SECRET_KEY", "seed-script-" + "x" * 32)

import app.models  # noqa: F401

from sqlalchemy import inspect, text

from app.core.config import settings
from app.core import database as db_mod
from app.models.content import Platform
from app.services.platform_catalog import all_catalog_rows, catalog_summary, upsert_platforms

from app.core.sqlite_paths import resolve_sqlite_database_url

_db_url = resolve_sqlite_database_url(
    os.environ.get("DATABASE_URL", "sqlite:///./youding_dev.db")
)
settings.DATABASE_URL = _db_url
os.environ["DATABASE_URL"] = _db_url
db_mod.rebind_engine(_db_url)
engine = db_mod.engine
SessionLocal = db_mod.SessionLocal
Base = db_mod.Base


def _ensure_platform_schema() -> None:
    """旧库 platforms 表缺 region 等列时重建（仅 platforms，开发/SQLite 常用）。"""
    insp = inspect(engine)
    if "platforms" not in insp.get_table_names():
        Base.metadata.create_all(bind=engine, tables=[Platform.__table__])
        return
    col_names = {c["name"] for c in insp.get_columns("platforms")}
    required = {"region", "content_type", "has_api", "base_url", "is_active"}
    if required.issubset(col_names):
        return
    with engine.begin() as conn:
        if engine.dialect.name == "sqlite":
            conn.execute(text("PRAGMA foreign_keys=OFF"))
        for tbl in ("platform_accounts", "platform_configs", "platforms"):
            if tbl in insp.get_table_names():
                conn.execute(text(f"DROP TABLE IF EXISTS {tbl}"))
        if engine.dialect.name == "sqlite":
            conn.execute(text("PRAGMA foreign_keys=ON"))
    Base.metadata.create_all(bind=engine, tables=[Platform.__table__])


def main() -> int:
    _ensure_platform_schema()
    db = SessionLocal()
    try:
        stats = upsert_platforms(db, all_catalog_rows())
        summary = catalog_summary(db)
        logger.info('OK: platforms seed {stats}, summary={summary}', stats, summary)
        return 0 if summary.get("ready") else 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
