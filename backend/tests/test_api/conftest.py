"""pytest configuration for test_api"""

# Compatibility fix for httpx 0.28 + starlette 0.36.3
import httpx
_orig_client_init = httpx.Client.__init__


def _patched_client_init(self, *args, **kwargs):
    kwargs.pop("app", None)
    return _orig_client_init(self, *args, **kwargs)


httpx.Client.__init__ = _patched_client_init

from app.models.user import User
from app.models.product import Category, Product
from app.models.inquiry import Inquiry
from app.models.content import ContentPage, ContentVersion
from app.core.database import Base
from app.db import session as db_session_module
from app.core.config import settings
from app.core import database
import os
from contextlib import asynccontextmanager

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import String, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# Must set UUID_TYPE BEFORE importing models

database.UUID_TYPE = String(36)
database.get_uuid_column = lambda: String(36)

# Now import config

settings.DATABASE_URL = "sqlite:///:memory:"

# Also set for app.db.session

db_session_module.settings = settings

# Import models AFTER UUID_TYPE is configured

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def unwrap_api_response(response):
    """解包 APIResponse(code, data, message) 包装，返回实际 data 部分。

    如果响应不是 APIResponse 格式（没有 'code' 字段），直接返回 response.json()。
    对于列表响应，分页信息合并到 data 中作为 {"items": [...], "meta": {...}} 格式。
    对于错误响应（code != 0），保留原始响应。
    """
    body = response.json()
    if not isinstance(body, dict) or "code" not in body or "data" not in body:
        return body
    # 错误响应保留完整格式
    if body.get("code", 0) != 0:
        return body
    data = body["data"]
    # 合并分页信息
    meta = {}
    for key in ("total", "page", "page_size"):
        if body.get(key) is not None:
            meta[key] = body[key]
    if meta:
        if isinstance(data, list):
            return {"items": data, "meta": meta}
        elif isinstance(data, dict):
            return {**data, "meta": meta}
    return data


class _WrappedResponse:
    """包装 response，json() 自动解包 APIResponse。"""

    def __init__(self, response):
        self._response = response

    def json(self):
        return unwrap_api_response(self._response)

    @property
    def status_code(self):
        return self._response.status_code

    @property
    def text(self):
        return self._response.text

    @property
    def headers(self):
        return self._response.headers

    @property
    def cookies(self):
        return self._response.cookies

    def raise_for_status(self):
        return self._response.raise_for_status()

    def __repr__(self):
        return f"<WrappedResponse [{self.status_code}]>"


class _AutoUnwrapClient(TestClient):
    """自动解包 APIResponse 的 TestClient。"""

    def request(self, *args, **kwargs):
        resp = super().request(*args, **kwargs)
        return _WrappedResponse(resp)


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Replace lifespan with noop to skip init_db
    @asynccontextmanager
    async def noop_lifespan(app: FastAPI):
        yield

    from app.main import app

    app.router.lifespan_context = noop_lifespan

    # Remove problematic middleware
    app.user_middleware = [
        mw for mw in app.user_middleware if mw.cls.__name__ not in [
            "CsrfProtectionMiddleware",
            "RateLimitMiddleware"]]

    # Override get_db from app.db.session (used by routes)
    from app.db.session import get_db as session_get_db

    app.dependency_overrides[session_get_db] = override_get_db

    with _AutoUnwrapClient(app, base_url="http://localhost") as test_client:
        yield test_client

    app.dependency_overrides.clear()
