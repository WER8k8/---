"""Dev-only: add missing inquiry columns when alembic chain is behind (SQLite)."""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import inspect, text

from app.db.session import SessionLocal


def repair_inquiry_columns() -> list[str]:
    db = SessionLocal()
    added: list[str] = []
    try:
        insp = inspect(db.bind)
        cols = {c["name"] for c in insp.get_columns("inquiries")}
        for col, typ in (
            ("source_utm", "TEXT"),
            ("publish_task_id", "VARCHAR(36)"),
            ("meddpicc_json", "TEXT"),
        ):
            if col not in cols:
                db.execute(text(f"ALTER TABLE inquiries ADD COLUMN {col} {typ}"))
                added.append(col)
        if added:
            db.commit()
    finally:
        db.close()
    return added


if __name__ == "__main__":
    repaired = repair_inquiry_columns()
    if repaired:
        logger.info('"Added columns:", ", ".join(repaired)')
    else:
        logger.info('inquiries columns OK')
