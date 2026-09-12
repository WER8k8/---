#!/usr/bin/env python3

"""QA-01 · 三壳 API 冒烟（无需浏览器 · 自举 in-memory DB）"""



from __future__ import annotations



import os

import sys



# 与 pytest conftest 对齐：内存库 + 测试密钥

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-testing-only-not-for-production-use")

os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-for-unit-testing-only-not-for-production-use")

os.environ.setdefault("ENVIRONMENT", "testing")

os.environ.setdefault("REDIS_ENABLED", "false")

os.environ.setdefault("LOGIN_BF_USE_REDIS", "false")



from contextlib import asynccontextmanager



from fastapi import FastAPI

from fastapi.testclient import TestClient

from sqlalchemy import create_engine, String

from sqlalchemy.orm import sessionmaker

from sqlalchemy.pool import StaticPool



from app.core import database

from app.core.database import Base, get_db

from app.main import app as main_app



database.UUID_TYPE = String(36)

database.get_uuid_column = lambda: String(36)



engine = create_engine(

    "sqlite:///:memory:",

    connect_args={"check_same_thread": False},

    poolclass=StaticPool,

)

TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)





def _override_get_db():

    db = TestingSession()

    try:

        yield db

    finally:

        db.close()





@asynccontextmanager

async def _noop_lifespan(_app: FastAPI):

    yield





main_app.router.lifespan_context = _noop_lifespan

main_app.dependency_overrides[get_db] = _override_get_db



client = TestClient(main_app)

BFF = "/api/v1/admin-bff"





def main() -> int:

    fails = 0

    checks = [

        ("captcha", lambda: client.get(f"{BFF}/auth/captcha").json()["code"] == 0),

        ("tenant_search", lambda: client.get(f"{BFF}/auth/tenant/search").json()["code"] == 0),

        ("plan_features", lambda: client.get(f"{BFF}/dict/plan_features").json()["code"] == 0),

        ("plan_check_requires_auth", _plan_check_requires_auth),

        ("menu_auth", lambda: client.get(f"{BFF}/menu/routes").status_code in (401, 403)),

        ("login_invalid", _login_invalid_rejected),

    ]

    for name, fn in checks:

        try:

            ok = fn()

            print(f"[{'PASS' if ok else 'FAIL'}] {name}")

            if not ok:

                fails += 1

        except Exception as exc:

            print(f"[FAIL] {name}: {exc}")

            fails += 1

    return 1 if fails else 0





def _plan_check_requires_auth() -> bool:

    r = client.get(f"{BFF}/plan/check", params={"feature": "egress_ip"})

    return r.status_code in (401, 403)





def _login_invalid_rejected() -> bool:

    r = client.post(

        f"{BFF}/auth/login",

        json={"username": "__no_such_user__", "password": "wrong"},

    )

    return r.status_code == 200 and r.json().get("code") != 0





if __name__ == "__main__":

    sys.exit(main())

