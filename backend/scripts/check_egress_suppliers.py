import sqlite3
import logging

logger = logging.getLogger(__name__)

from pathlib import Path

backend = Path(__file__).resolve().parents[1]
candidates = [
    backend / "youding_dev.db",
    backend / "data" / "dev.db",
    backend.parent / "youding_dev.db",
]

for db in candidates:
    if not db.exists():
        logger.info('{db}: MISSING', db)
        continue
    c = sqlite3.connect(db)
    tables = c.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'egress%'"
    ).fetchall()
    logger.info('\\n{db} ({db.stat().st_size} bytes)', db, db.stat().st_size)
    logger.info('"  egress tables:", [t[0] for t in tables]')
    if any(t[0] == "egress_suppliers" for t in tables):
        for row in c.execute(
            "SELECT code, name, is_active, enabled FROM egress_suppliers"
        ).fetchall():
            logger.info('" ", row')
    else:
        logger.info('  egress_suppliers: MISSING')
