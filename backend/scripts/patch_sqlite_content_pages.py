"""
import logging

logger = logging.getLogger(__name__)

为已存在的 SQLite 库补齐 content_pages 表字段（与 ORM 一致）。
用法: 在项目根目录执行  python backend/scripts/patch_sqlite_content_pages.py
"""

import os
import sqlite3

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_CANDIDATES = [
    os.path.join(ROOT, "backend", "app.db"),
    os.path.join(ROOT, "backend", "data.db"),
    os.path.join(ROOT, "backend", "dev.db"),
]


def column_exists(cur: sqlite3.Cursor, table: str, col: str) -> bool:
    cur.execute(f"PRAGMA table_info({table})")
    return any(row[1] == col for row in cur.fetchall())


def main() -> None:
    db_path = None
    for p in DB_CANDIDATES:
        if os.path.isfile(p):
            db_path = p
            break
    if not db_path:
        logger.info('未找到 SQLite 文件，跳过（可手动指定路径修改脚本）。')
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    alters = [
        ("page_type", "ALTER TABLE content_pages ADD COLUMN page_type VARCHAR(50) DEFAULT 'page'"),
        ("view_count", "ALTER TABLE content_pages ADD COLUMN view_count INTEGER DEFAULT 0 NOT NULL"),
        ("is_active", "ALTER TABLE content_pages ADD COLUMN is_active BOOLEAN DEFAULT 1 NOT NULL"),
        ("published_at", "ALTER TABLE content_pages ADD COLUMN published_at TIMESTAMP"),
    ]
    for col, sql in alters:
        if not column_exists(cur, "content_pages", col):
            cur.execute(sql)
            logger.info('OK: {db_path} + {col}', db_path, col)
        else:
            logger.info('skip: {col} already exists', col)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
