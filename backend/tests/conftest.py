"""测试体系基础 — FIX-52

提供测试基础设施：
- pytest 配置
- 测试 fixtures
- API 测试客户端
- 覆盖率配置
- 测试数据工厂
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from typing import Any, AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# ============================================================
# pytest 配置 (pyproject.toml / pytest.ini 等效)
# ============================================================

PYTEST_CONFIG = """
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--strict-markers",
    "--tb=short",
    "--cov=backend/app",
    "--cov-report=term-missing",
    "--cov-report=html:coverage",
    "--cov-report=xml:coverage.xml",
    "--cov-fail-under=50",
]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "slow: Slow running tests",
    "api: API endpoint tests",
]
"""


# ============================================================
# 测试 Fixtures
# ============================================================

# 测试数据库 URL（使用内存 SQLite）
TEST_DATABASE_URL = "sqlite:///./test.db"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


@pytest.fixture(scope="session")
def db_engine():
    """创建测试数据库引擎。"""
    from app.models import Base
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """创建测试数据库会话（每个测试函数独立）。"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session) -> Generator[TestClient, None, None]:
    """创建 FastAPI 测试客户端。"""
    from app.main import app
    from app.core.database import get_db

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
def auth_headers(client) -> dict[str, str]:
    """获取认证请求头（测试用户）。"""
    response = client.post("/api/v1/auth/login", json={
        "username": "test_user",
        "password": "test_password",
    })
    if response.status_code == 200:
        token = response.json().get("data", {}).get("access_token", "")
        return {"Authorization": f"Bearer {token}"}
    return {}


# ============================================================
# 测试数据工厂
# ============================================================

class LeadFactory:
    """线索测试数据工厂。"""

    @staticmethod
    def build(**overrides) -> dict:
        """构建测试线索数据。"""
        return {
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "company": "Test Company",
            "title": "CEO",
            "industry": "Construction",
            "country": "US",
            "source": "test",
            **overrides,
        }

    @staticmethod
    def create(db: Session, **overrides) -> Any:
        """创建并持久化测试线索。"""
        from app.models.prospect_lead import ProspectLead
        import uuid

        data = LeadFactory.build(**overrides)
        lead = ProspectLead(
            id=str(uuid.uuid4()),
            **data,
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return lead

    @staticmethod
    def create_batch(db: Session, count: int = 10, **overrides) -> list[Any]:
        """批量创建测试线索。"""
        return [LeadFactory.create(db, **overrides) for _ in range(count)]


class EmailOutreachFactory:
    """邮件外展测试数据工厂。"""

    @staticmethod
    def build(**overrides) -> dict:
        return {
            "prospect_id": "test-prospect-id",
            "subject": "Test Subject",
            "body": "Test Body",
            "status": "draft",
            **overrides,
        }

    @staticmethod
    def create(db: Session, **overrides) -> Any:
        from app.models.email_outreach import EmailOutreach
        import uuid

        data = EmailOutreachFactory.build(**overrides)
        outreach = EmailOutreach(
            id=str(uuid.uuid4()),
            **data,
        )
        db.add(outreach)
        db.commit()
        db.refresh(outreach)
        return outreach


# ============================================================
# 测试辅助函数
# ============================================================

def assert_response_ok(response, status_code: int = 200):
    """断言响应成功。"""
    assert response.status_code == status_code, (
        f"Expected {status_code}, got {response.status_code}: {response.text}"
    )


def assert_response_error(response, status_code: int = 400):
    """断言响应错误。"""
    assert response.status_code == status_code


def assert_paginated(response_json: dict):
    """断言分页响应格式。"""
    data = response_json.get("data", response_json)
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "items" in data


# ============================================================
# 示例测试
# ============================================================

class TestHealthEndpoint:
    """健康检查端点测试。"""

    def test_health_check(self, client):
        """测试健康检查端点。"""
        response = client.get("/api/v1/health")
        assert_response_ok(response)
        data = response.json()
        assert data["data"]["status"] == "ok"


class TestLeadScoring:
    """线索评分测试。"""

    @pytest.mark.asyncio
    async def test_score_hot_lead(self):
        """测试高价值线索评分。"""
        from app.services.ubrain.lead_scoring_engine import score_lead

        result = await score_lead({
            "email": "ceo@bigcompany.com",
            "first_name": "John",
            "last_name": "Doe",
            "company": "Big Construction Co",
            "website": "https://bigconstruction.com",
            "industry": "Construction",
            "title": "CEO",
            "country": "US",
            "source": "linkedin",
            "linkedin_url": "https://linkedin.com/in/johndoe",
            "phone": "+1234567890",
        })

        assert result["score"] >= 80
        assert result["grade"] == "hot"


class TestDripSequence:
    """邮件序列测试。"""

    def test_get_next_step(self):
        """测试序列步骤推进。"""
        from app.services.ubrain.drip_sequence_service import DripSequenceService

        service = DripSequenceService()
        seq = service.get_sequence("seq-3-step")

        assert seq is not None
        assert len(seq.steps) == 3

        # 第一步
        step1 = service.get_next_step("seq-3-step", 0)
        assert step1 is not None
        assert step1.step == 1

        # 第二步（未回复触发）
        step2 = service.get_next_step("seq-3-step", 1, "no_reply")
        assert step2 is not None
        assert step2.step == 2

        # 序列结束
        step4 = service.get_next_step("seq-3-step", 3)
        assert step4 is None


class TestEventBus:
    """事件总线测试。"""

    @pytest.mark.asyncio
    async def test_emit_and_handle(self):
        """测试事件发布和订阅。"""
        from app.core.event_bus import event_bus, Event

        received = []

        @event_bus.on("test.event")
        async def handler(event: Event):
            received.append(event.data)

        await event_bus.emit(Event("test.event", {"key": "value"}))

        assert len(received) == 1
        assert received[0]["key"] == "value"


class TestPipeline:
    """线索处理 Pipeline 测试。"""

    @pytest.mark.asyncio
    async def test_normalize_handler(self):
        """测试标准化处理器。"""
        from app.services.ubrain.lead_processing_pipeline import (
            NormalizeHandler, LeadContext,
        )

        handler = NormalizeHandler()
        ctx = LeadContext(raw_data={
            "email": " Test@Example.COM ",
            "name": "John",
            "company": "Test Co",
        })

        result = await handler.process(ctx)
        assert result.normalized["email"] == "test@example.com"
        assert result.normalized["first_name"] == "John"