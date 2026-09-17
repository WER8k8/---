# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Resolve SQLite DATABASE_URL to a real file (backend vs repo root)."""

from __future__ import annotations

import os
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = _BACKEND_ROOT.parent
_DEFAULT_NAME = "youding_dev.db"


def sqlite_candidate_paths() -> list[Path]:
    """开发环境 SQLite 候选路径（优先级：环境变量、backend 目录、项目根目录、当前目录）。"""
    extra = os.environ.get("YOUDING_SQLITE_PATH", "").strip()
    paths: list[Path] = []
    if extra:
        paths.append(Path(extra))
    paths.extend(
        [
            _BACKEND_ROOT / _DEFAULT_NAME,
            _REPO_ROOT / _DEFAULT_NAME,
            Path.cwd() / _DEFAULT_NAME,
        ]
    )
    seen: set[Path] = set()
    out: list[Path] = []
    for p in paths:
        key = p.resolve()
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def pick_sqlite_file() -> Path | None:
    """从候选中选择最大的非空数据库文件（避免 0 字节占位文件）。"""
    existing = [p for p in sqlite_candidate_paths() if p.is_file()]
    if not existing:
        return None
    non_empty = [p for p in existing if p.stat().st_size > 0]
    pool = non_empty or existing
    return max(pool, key=lambda p: p.stat().st_size)


def resolve_sqlite_database_url(url: str | None = None) -> str:
    """
    Turn relative sqlite:///./youding_dev.db into absolute path to the best file.
    Leaves Postgres and absolute sqlite URLs unchanged.
    """
    raw = (url or os.environ.get("DATABASE_URL") or "sqlite:///./youding_dev.db").strip()
    if not raw.startswith("sqlite"):
        return raw

    path_part = raw.replace("sqlite:///", "", 1)
    if len(path_part) > 2 and path_part[1] == ":":
        return raw
    if path_part and not path_part.startswith(("./", ".\\")):
        p = Path(path_part)
        if p.is_file() or p.is_absolute():
            return raw

    picked = pick_sqlite_file()
    if picked is None:
        return raw
    return f"sqlite:///{picked.resolve().as_posix()}"
