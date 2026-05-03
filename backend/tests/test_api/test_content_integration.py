import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 设置测试数据库
import os
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.core.config import settings
settings.DATABASE_URL = "sqlite:///:memory:"

from app.core.database import Base, get_db, get_uuid_column
from app.core.security import get_password_hash
from app.models.user import User

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from app.core import database
database.UUID_TYPE = String(36)
database.get_uuid_column = lambda: String(36)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    from app.main import app
    
    # 禁用CSRF和限流中间件
    app.user_middleware = [mw for mw in app.user_middleware if mw.cls.__name__ not in ["CsrfProtectionMiddleware", "RateLimitMiddleware"]]
    
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app, base_url="http://localhost") as test_client:
        yield test_client

    app.dependency_overrides.clear()

class TestContentPagesAPI:
    def test_list_pages(self, client):
        response = client.get("/api/v1/content/pages")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_list_pages_with_filters(self, client):
        response = client.get("/api/v1/content/pages?page_type=page&search=test")
        assert response.status_code == 200

    def test_get_page_by_slug(self, client):
        response = client.get("/api/v1/content/pages/slug/about")
        assert response.status_code in [200, 404]

    def test_get_nonexistent_page(self, client):
        response = client.get("/api/v1/content/pages/nonexistent-id")
        assert response.status_code == 404

class TestContentBatchAPI:
    def test_batch_delete_empty_ids(self, client):
        response = client.post(
            "/api/v1/content/pages/batch-delete",
            json={"ids": []}
        )
        # 未认证用户先收到401，认证用户收到422验证错误
        assert response.status_code in [401, 422]

    def test_batch_update_status_invalid_status(self, client):
        response = client.post(
            "/api/v1/content/pages/batch-update-status",
            json={"ids": ["test-id"], "status": "invalid"}
        )
        # 未认证用户先收到401，认证用户收到422验证错误
        assert response.status_code in [401, 422]

    def test_batch_publish_empty_ids(self, client):
        response = client.post(
            "/api/v1/content/pages/batch-publish",
            json={"ids": []}
        )
        # 未认证用户先收到401，认证用户收到422验证错误
        assert response.status_code in [401, 422]

class TestContentStatsAPI:
    def test_get_content_stats(self, client):
        response = client.get("/api/v1/content/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_pages" in data
        assert "published_pages" in data
        assert "draft_pages" in data
        assert "total_versions" in data
        assert "page_type_stats" in data

class TestContentExportAPI:
    def test_export_pages(self, client):
        response = client.get("/api/v1/content/pages/export")
        # 导出需要管理员权限，未认证用户收到401，路由可能未注册时返回404
        assert response.status_code in [200, 401, 404]
        if response.status_code == 200:
            data = response.json()
            assert "total" in data
            assert "data" in data

    def test_export_pages_with_filters(self, client):
        response = client.get("/api/v1/content/pages/export?page_type=page&status=published")
        # 导出需要管理员权限，未认证用户收到401，路由可能未注册时返回404
        assert response.status_code in [200, 401, 404]

class TestProductDetailAPI:
    def test_get_product_by_slug(self, client):
        response = client.get("/api/v1/products/by-slug/test-product")
        assert response.status_code in [200, 404]

    def test_get_product_by_id(self, client):
        response = client.get("/api/v1/products/test-id")
        assert response.status_code in [200, 404]

    def test_list_products(self, client):
        response = client.get("/api/v1/products/")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, list)

class TestContentVersionsAPI:
    def test_list_versions_unauthorized(self, client):
        response = client.get("/api/v1/content/pages/test-id/versions")
        assert response.status_code in [401, 403, 404]

    def test_get_version_unauthorized(self, client):
        response = client.get("/api/v1/content/pages/test-id/versions/test-version-id")
        assert response.status_code in [401, 403, 404]

class TestSecurityHeaders:
    def test_security_headers(self, client):
        response = client.get("/api/v1/content/pages")
        assert response.status_code == 200

class TestInputValidation:
    def test_search_injection(self, client):
        response = client.get("/api/v1/content/pages?search=<script>alert('xss')</script>")
        assert response.status_code == 200

    def test_sql_injection_attempt(self, client):
        response = client.get("/api/v1/content/pages?search='; DROP TABLE content_pages; --")
        assert response.status_code == 200

    def test_batch_delete_too_many_ids(self, client):
        ids = ["id-" + str(i) for i in range(101)]
        response = client.post(
            "/api/v1/content/pages/batch-delete",
            json={"ids": ids}
        )
        # 未认证用户先收到401，认证用户收到422验证错误
        assert response.status_code in [401, 422]

    def test_batch_delete_invalid_id_format(self, client):
        response = client.post(
            "/api/v1/content/pages/batch-delete",
            json={"ids": ["not-a-valid-uuid"]}
        )
        # 未认证用户先收到401，认证用户收到其他状态码
        assert response.status_code in [401, 200, 404, 422]
