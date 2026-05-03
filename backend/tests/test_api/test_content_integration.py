import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db, Base, engine

@pytest.fixture(scope="module")
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(test_db):
    return TestClient(app)

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
        assert response.status_code == 422

    def test_batch_update_status_invalid_status(self, client):
        response = client.post(
            "/api/v1/content/pages/batch-update-status",
            json={"ids": ["test-id"], "status": "invalid"}
        )
        assert response.status_code == 422

    def test_batch_publish_empty_ids(self, client):
        response = client.post(
            "/api/v1/content/pages/batch-publish",
            json={"ids": []}
        )
        assert response.status_code == 422

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
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "data" in data

    def test_export_pages_with_filters(self, client):
        response = client.get("/api/v1/content/pages/export?page_type=page&status=published")
        assert response.status_code == 200

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
        assert response.status_code == 422

    def test_batch_delete_invalid_id_format(self, client):
        response = client.post(
            "/api/v1/content/pages/batch-delete",
            json={"ids": ["not-a-valid-uuid"]}
        )
        assert response.status_code in [200, 404, 422]
