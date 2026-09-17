# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""SEO-09：独立 SEO 矩阵库连通性探针（司令部健康）。"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text

from app.core.config import settings
from app.services.matrix_admin_bridge import _mysql_engine_url, matrix_credentials_source_configured


def seo_matrix_db_health() -> dict[str, Any]:
    """实现 seomatrix数据库health 的功能。
    
    :return: 返回 dict[str, Any] 结果
    """
    configured = matrix_credentials_source_configured(settings)
    if not configured:
        return {
            "configured": False,
            "reachable": False,
            "mode": "none",
            "hint": "设置 SEO_MATRIX_DATABASE_URL 或 SEO_MATRIX_DB_* / SEO_MATRIX_SQLITE_PATH",
        }

    mysql_url = _mysql_engine_url(settings)
    if mysql_url:
        try:
            engine = create_engine(mysql_url, pool_pre_ping=True, pool_recycle=3600)
            with engine.connect() as conn:
                row = conn.execute(text("SELECT 1 AS ok")).mappings().first()
                admin_count = conn.execute(
                    text("SELECT COUNT(*) AS c FROM admin_users")
                ).scalar()
            engine.dispose()
            return {
                "configured": True,
                "reachable": bool(row),
                "mode": "mysql",
                "admin_users_count": int(admin_count or 0),
            }
        except Exception as exc:
            return {
                "configured": True,
                "reachable": False,
                "mode": "mysql",
                "error": str(exc)[:300],
            }

    sqlite_path = (settings.SEO_MATRIX_SQLITE_PATH or "").strip()
    try:
        path = Path(sqlite_path)
        if not path.is_file():
            return {
                "configured": True,
                "reachable": False,
                "mode": "sqlite",
                "error": "file_missing",
            }
        conn = sqlite3.connect(str(path.resolve()))
        try:
            conn.execute("SELECT 1")
            count = conn.execute("SELECT COUNT(*) FROM admin_users").fetchone()[0]
        finally:
            conn.close()
        return {
            "configured": True,
            "reachable": True,
            "mode": "sqlite",
            "path": str(path),
            "admin_users_count": int(count),
        }
    except Exception as exc:
        return {
            "configured": True,
            "reachable": False,
            "mode": "sqlite",
            "error": str(exc)[:300],
        }
