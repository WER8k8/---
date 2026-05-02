"""
Pytest配置文件 - 测试 fixtures
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.main import app
from app.models.user import User

# 测试数据库配置（使用SQLite内存数据库）
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """创建测试数据库会话"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # 清理所有表
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """创建测试客户端"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """测试用户数据"""
    return {
        "username": "test_admin",
        "email": "test@example.com",
        "password": "Test123456!",
        "role": "admin"
    }


@pytest.fixture
def authenticated_client(client, db_session, test_user_data):
    """已认证的测试客户端"""
    # 直接在数据库中创建测试用户
    from uuid import uuid4
    user = User(
        id=str(uuid4()),
        username=test_user_data["username"],
        email=test_user_data["email"],
        hashed_password=get_password_hash(test_user_data["password"]),
        role=test_user_data["role"],
        is_active=True
    )
    db_session.add(user)
    db_session.commit()

    # 登录获取token
    login_response = client.post(
        "/api/v1/system/login",
        json={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
    )

    if login_response.status_code == 200:
        token = login_response.json()["access_token"]
        client.headers["Authorization"] = f"Bearer {token}"

    return client
