"""运维备份（SQLite 文件 + 元数据快照）。"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.services.auto_backup import BACKUP_DIR, backup_service


def _resolve_db_file() -> Path | None:
    """_resolve_db_file。
    :return: 返回处理结果。
    """
    url = settings.DATABASE_URL or ""
    if url.startswith("sqlite:///"):
        raw = url.replace("sqlite:///", "", 1)
        p = Path(raw)
        if not p.is_absolute():
            backend = Path(__file__).resolve().parents[2]
            p = backend / raw
        return p if p.is_file() else None
    return None


def run_manual_backup() -> dict[str, Any]:
    """立即执行备份（优先走 AutoBackup，并补充 DATABASE_URL 说明）。"""
    result = backup_service.run_backup()
    db_file = _resolve_db_file()
    meta = {
        "database_url": settings.DATABASE_URL,
        "db_file_backed_up": bool(db_file and db_file.exists()),
        "postgres_hint": "生产 PostgreSQL 请使用 pg_dump / 云厂商快照",
    }
    if db_file and db_file.exists():
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        manual_dir = Path(BACKUP_DIR) / f"manual_{ts}"
        manual_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(db_file, manual_dir / "database.db")
        with open(manual_dir / "meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        result["manual_copy"] = str(manual_dir)
    result["meta"] = meta
    return result


def backup_status() -> dict[str, Any]:
    """backup_status。
    :return: 返回处理结果。
    """
    status = backup_service.get_status()
    status["postgres_hint"] = "PostgreSQL 生产环境请配置定时 pg_dump"
    return status
