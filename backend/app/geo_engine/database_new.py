# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
# mypy: ignore-errors
"""
GEO Engine Database Module - Using databases library

Independent database module for the GEO engine.
Uses the `databases` library to provide async interface compatible with both
PostgreSQL (asyncpg) and SQLite (aiosqlite).
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from databases import Database
logger = logging.getLogger(__name__)

# Import UJ project settings
try:
    from app.core.config import settings
except ImportError:
    settings = None

# Database URL - use SQLite by default (same as UJ project)
# Can be overridden via environment variable or settings
if settings:
    DB_URL = getattr(settings, 'GEO_DATABASE_URL', 'sqlite+aiosqlite:///youding_dev.db')
else:
    DB_URL = 'sqlite+aiosqlite:///youding_dev.db'


class GeoDatabase:
    """
    Database wrapper for GEO engine.
    
    Uses `databases` library which provides unified async interface
    for PostgreSQL, MySQL, and SQLite.
    """
    def __init__(self, url: str = DB_URL) -> None:
        """__init__。

        参数说明：
        :param self: 参数 self
        :param url: 参数 url
        :return: 返回处理结果。
        """
        self.url = url
        self.database = Database(url)
        self.enabled = True
    
    async def connect(self) -> None:
        """Initialize database connection"""
        try:
            await self.database.connect()
        except Exception as e:
            logger.warning("Failed to connect to GEO database: %s", e)
            self.enabled = False
        return
    
    async def close(self) -> None:
        """Close database connection"""
        if self.database.is_connected:
            await self.database.disconnect()
        return
    
    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[Connection]:
        """
        Acquire a database connection.
        
        Yields a databases Database connection object.
        For PostgreSQL, this is an asyncpg connection.
        For SQLite, this is an aiosqlite connection wrapper.
        """
        if not self.enabled:
            raise RuntimeError("geo_database_disabled")
        
        # databases library handles connection pooling automatically
        # Just yield the database object (it acts as a connection context manager)
        async with self.database.connection() as connection:
            yield connection
    
    def get_raw_connection(self):
        """
        Get raw database connection for asyncpg-style API access.
        
        This allows repositories.py to use asyncpg-style API
        (fetchval, fetch, fetchrow) when using PostgreSQL.
        For SQLite, the API is different, so this may not work.
        """
        return self.database


# Global database instance
geo_db = GeoDatabase()
