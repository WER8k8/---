"""QA 三壳 BFF 冒烟 — 共享 TestClient 自举（in-memory DB）"""

from __future__ import annotations

import os
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import String, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import database
from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.main import app as main_app
from app.models.tenant import Tenant, TenantPlan, UserTenant
from app.models.user import User

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-testing-only-not-for-production-use")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-for-unit-testing-only-not-for-production-use")
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("REDIS_ENABLED", "false")
os.environ.setdefault("LOGIN_BF_USE_REDIS", "false")

database.UUID_TYPE = String(36)
database.get_uuid_column = lambda: String(36)

_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_Session = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
Base.metadata.create_all(bind=_engine)

QA_USERS: tuple[tuple[str, str, str], ...] = (
    ("admin", "admin123", "super_admin"),
    ("editor", "editor123", "editor"),
    ("partner", "partner123", "l2"),
    ("sales", "sales123", "sales"),
)

EXPECTED_SHELL: dict[str, str] = {
    "admin": "platform",
    "editor": "client",
    "partner": "partner",
    "sales": "agent",
}


def _seed_users() -> None:
    db = _Session()
    try:
        for username, password, role in QA_USERS:
            if db.query(User).filter(User.username == username).first():
                continue
            db.add(
                User(
                    id=str(uuid.uuid4()),
                    username=username,
                    email=f"{username}@qa.test",
                    hashed_password=get_password_hash(password),
                    role=role,
                    is_active=True,
                )
            )
        db.commit()

        plan = db.query(TenantPlan).filter(TenantPlan.code == "qa-plan").first()
        if not plan:
            plan = TenantPlan(
                id=str(uuid.uuid4()),
                name="QA套餐",
                code="qa-plan",
                price_monthly=0,
                price_yearly=0,
                features="[]",
                is_active=True,
            )
            db.add(plan)
            db.flush()
        tenant = db.query(Tenant).filter(Tenant.domain == "qa.test.local").first()
        if not tenant:
            tenant = Tenant(
                id=str(uuid.uuid4()),
                name="QA租户",
                domain="qa.test.local",
                plan_id=plan.id,
                status="active",
                is_active=True,
            )
            db.add(tenant)
            db.flush()
        editor = db.query(User).filter(User.username == "editor").first()
        if editor and not db.query(UserTenant).filter(
            UserTenant.user_id == editor.id, UserTenant.tenant_id == tenant.id
        ).first():
            db.add(
                UserTenant(
                    user_id=editor.id,
                    tenant_id=tenant.id,
                    role="editor",
                    is_active=True,
                )
            )
        db.commit()
    finally:
        db.close()


def _override_get_db():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


@asynccontextmanager
async def _noop_lifespan(_app: FastAPI):
    yield


def build_qa_client() -> TestClient:
    _seed_users()
    main_app.router.lifespan_context = _noop_lifespan
    main_app.dependency_overrides[get_db] = _override_get_db
    return TestClient(main_app)


def bff_login(client: TestClient, username: str, password: str) -> str | None:
    r = client.post(
        "/api/v1/admin-bff/auth/login",
        json={"username": username, "password": password},
    )
    body = r.json()
    if body.get("code") != 0:
        return None
    return body.get("data", {}).get("accessToken")


def bff_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
