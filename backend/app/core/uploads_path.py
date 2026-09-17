# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""本地上传目录 — files API 与 StaticFiles 挂载须共用同一路径。"""

from pathlib import Path

# backend/app/core/uploads_path.py → backend/
BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
UPLOADS_DIR = BACKEND_ROOT / "uploads"
LEGACY_UPLOADS_DIR = BACKEND_ROOT / "app" / "uploads"


def uploads_dir() -> str:
    """uploads_dir。
    :return: 返回处理结果。
    """
    return str(UPLOADS_DIR)


def ensure_uploads_dir() -> Path:
    """ensure_uploads_dir。
    :return: 返回处理结果。
    """
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOADS_DIR


def migrate_legacy_uploads() -> None:
    """一次性：将误写入 backend/app/uploads 的文件迁到 backend/uploads。"""
    if not LEGACY_UPLOADS_DIR.is_dir():
        return
    ensure_uploads_dir()
    for entry in LEGACY_UPLOADS_DIR.iterdir():
        target = UPLOADS_DIR / entry.name
        if target.exists():
            continue
        entry.rename(target)
    try:
        LEGACY_UPLOADS_DIR.rmdir()
    except OSError:
        pass
