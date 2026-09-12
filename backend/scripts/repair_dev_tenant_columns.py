"""Dev-only: 为存量 SQLite 开发库补 products/orders/quotes 的 tenant_id 列（ADR-001 租户归一）。

何时用：开发库（youding_dev.db）alembic 版本落后、且不打算全链 upgrade 时，
与 repair_dev_inquiry_columns.py 同一套路的条件化补列（缺才加，幂等）。
PG 生产库请直接 `alembic upgrade head`（迁移 102，勿用本脚本）。
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import inspect, text

from app.db.session import SessionLocal


def repair_tenant_columns() -> list[str]:
    db = SessionLocal()
    added: list[str] = []
    try:
        insp = inspect(db.bind)
        for table in ("products", "orders", "quotes"):
            if table not in insp.get_table_names():
                logger.warning("表 %s 不存在，跳过", table)
                continue
            cols = {c["name"] for c in insp.get_columns(table)}
            if "tenant_id" not in cols:
                db.execute(text(f"ALTER TABLE {table} ADD COLUMN tenant_id VARCHAR(36)"))
                db.execute(
                    text(f"CREATE INDEX IF NOT EXISTS ix_{table}_tenant_id ON {table} (tenant_id)")
                )
                added.append(f"{table}.tenant_id")
                logger.info("已补列 %s.tenant_id", table)
        db.commit()
    finally:
        db.close()
    return added


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = repair_tenant_columns()
    print("修复完成:", result or "无缺失（幂等 no-op）")
