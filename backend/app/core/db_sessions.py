# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""E-2 读写分离会话助手。

- get_write_session(): 必须写库时用（flush 路由也会走主库）
- get_read_session(): 报表/列表只读查询；未配置 DATABASE_READ_URL 时自动回落主库
- mark_write(session): 在 info 上打 write 标记，RoutingSession 会绑主库
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from app.core.config import settings
from app.core.database import SessionLocal, engine, read_engine


def read_engine_configured() -> bool:
    return bool(getattr(settings, "DATABASE_READ_URL", None))


def mark_write(session: Any) -> Any:
    if session is not None and hasattr(session, "info"):
        session.info["write"] = True
    return session


@contextmanager
def get_read_session() -> Iterator[Any]:
    """只读查询会话。无读库配置时等同主库。"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def get_write_session() -> Iterator[Any]:
    """写路径会话（显式 write 标记）。"""
    session = SessionLocal()
    mark_write(session)
    try:
        yield session
    finally:
        session.close()


def db_topology() -> dict:
    """拓扑体检（运维/自检用）。"""
    primary = str(getattr(settings, "DATABASE_URL", "") or "")
    read = str(getattr(settings, "DATABASE_READ_URL", "") or "")
    def _mask(u: str) -> str:
        if "@" in u and "://" in u:
            scheme, rest = u.split("://", 1)
            host = rest.split("@", 1)[-1]
            return f"{scheme}://***@{host}"
        return "sqlite/local" if u.startswith("sqlite") else (u[:20] + "…" if u else "")
    return {
        "primary_configured": bool(primary),
        "primary_masked": _mask(primary),
        "read_configured": read_engine_configured(),
        "read_masked": _mask(read) if read else "",
        "read_falls_back_to_primary": (not read_engine_configured()) or (read_engine is engine),
        "plain_summary": (
            "已配置读写分离：读库独立，写走主库。"
            if read_engine_configured()
            else "未配置 DATABASE_READ_URL — 读写均走主库（开发默认，可接受）。"
        ),
        "hint": "生产可设 DATABASE_READ_URL 只读副本；未配置时不报错、不假装已分离。",
    }
