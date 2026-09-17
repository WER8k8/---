# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""数据库 Schema 自动修复 — 启动时检测并补全缺失列

解决 SoftDeleteMixin 等 mixin 定义了 deleted_at 但旧数据库表缺少该列的问题。
仅在 SQLite 开发模式下自动执行；生产环境 PostgreSQL 使用 Alembic 迁移。
"""

import logging
import sqlite3
from typing import Dict, List, Set

logger = logging.getLogger("uj-admin.schema_healer")

# SoftDeleteMixin 注入的列，所有继承该 mixin 的表都需要
SOFT_DELETE_COLUMNS = {
    "deleted_at": "DATETIME",
}

# 其他常见 mixin 列（按需扩展）
MIXIN_COLUMNS: Dict[str, str] = {
    **SOFT_DELETE_COLUMNS,
    "created_at": "DATETIME",
    "updated_at": "DATETIME",
}

# 多租户隔离列：模型已声明 tenant_id（SQLite 下 UUID_TYPE 编译为 VARCHAR(36)），
# 但旧库建表早于该列，启动时按表定向补列。NULL 表示平台级公共数据，无需回填。
# 仅补这些表，避免给所有表盲目加列。
TENANT_ISOLATION_TABLES: Dict[str, str] = {
    "products": "VARCHAR(36)",
    "categories": "VARCHAR(36)",
    "case_studies": "VARCHAR(36)",
    "content_pages": "VARCHAR(36)",
    "keywords": "VARCHAR(36)",
    "llms_config": "VARCHAR(36)",
    "product_categories": "VARCHAR(36)",
}

# 定向补列（BUG-05 修复）：opportunities 表新增 CRM 管线落库所需列。
# 模型已声明，旧 SQLite 库缺列时启动自动 ALTER TABLE 补齐（Postgres 走 alembic 082）。
EXTRA_COLUMNS: Dict[str, Dict[str, str]] = {
    "opportunities": {
        "company_id": "VARCHAR(36)",
        "contact_id": "VARCHAR(36)",
        "created_by": "VARCHAR(36)",
    },
}

# 不需要自动修复的表（系统表、关联表等）
SKIP_TABLES = {
    "sqlite_sequence",
    "alembic_version",
}


def _get_existing_columns(conn: sqlite3.Connection, table: str) -> Set[str]:
    """获取表的现有列名集合。"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cursor.fetchall()}


def _get_all_tables(conn: sqlite3.Connection) -> List[str]:
    """获取数据库中所有用户表。"""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    return [row[0] for row in cursor.fetchall()]


def heal_sqlite_schema(db_path: str) -> int:
    """扫描 SQLite 数据库，为缺失的 mixin 列自动添加 ALTER TABLE。

    Returns:
        修复的列数
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("BEGIN")
        fixed = 0
        tables = _get_all_tables(conn)
        for table in tables:
            if table in SKIP_TABLES:
                continue

            existing = _get_existing_columns(conn, table)
            for col_name, col_type in MIXIN_COLUMNS.items():
                if col_name not in existing:
                    try:
                        conn.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                        logger.info("Schema heal: added %s.%s (%s)", table, col_name, col_type)
                        fixed += 1
                    except sqlite3.OperationalError as e:
                        # 列已存在或其他并发问题，忽略
                        logger.debug("Skip %s.%s: %s", table, col_name, e)

            tenant_col = TENANT_ISOLATION_TABLES.get(table)
            if tenant_col and "tenant_id" not in existing:
                try:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN tenant_id {tenant_col}")
                    logger.info("Schema heal: added %s.tenant_id (%s)", table, tenant_col)
                    fixed += 1
                except sqlite3.OperationalError as e:
                    logger.debug("Skip %s.tenant_id: %s", table, e)

            for col_name, col_type in EXTRA_COLUMNS.get(table, {}).items():
                if col_name not in existing:
                    try:
                        conn.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                        logger.info("Schema heal: added %s.%s (%s)", table, col_name, col_type)
                        fixed += 1
                    except sqlite3.OperationalError as e:
                        logger.debug("Skip %s.%s: %s", table, col_name, e)

        conn.commit()
        conn.close()
        if fixed > 0:
            logger.info("Schema healer: fixed %d missing columns", fixed)
        return fixed

    except Exception as exc:
        logger.error("Schema healer failed: %s", exc)
        return 0


def auto_heal_if_sqlite(db_url: str) -> None:
    """如果是 SQLite 数据库，自动执行 schema 修复。"""
    if not db_url.startswith("sqlite"):
        return

    # 提取数据库文件路径
    # sqlite:///./youding_dev.db -> youding_dev.db
    db_path = db_url.replace("sqlite:///", "").replace("sqlite://", "")
    if db_path.startswith("./"):
        db_path = db_path[2:]

    import os
    if not os.path.exists(db_path):
        logger.debug("Database file not found, skip healing: %s", db_path)
        return

    heal_sqlite_schema(db_path)
