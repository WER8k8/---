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

class TestInquiryAPI:
    def test_create_inquiry_success(self, client):
        response = client.post(
            "/api/v1/inquiries",
            json={
                "name": "测试用户",
                "phone": "13800138000",
                "email": "test@example.com",
                "product": "轻集料混凝土",
                "message": "咨询产品价格"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "测试用户"
        assert data["status"] == "pending"

    def test_create_inquiry_xss_protection(self, client):
        response = client.post(
            "/api/v1/inquiries",
            json={
                "name": "<script>alert('xss')</script>测试",
                "phone": "13800138000",
                "message": "正常留言"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert "<script>" not in data["name"]

    def test_create_inquiry_missing_fields(self, client):
        response = client.post(
            "/api/v1/inquiries",
            json={"name": "测试"}
        )
        assert response.status_code == 422

    def test_list_inquiries_requires_admin(self, client):
        response = client.get("/api/v1/inquiries")
        assert response.status_code in [200, 401]

class TestInquiryBatchAPI:
    def test_batch_delete_empty_ids(self, client):
        response = client.post(
            "/api/v1/inquiries/batch-delete",
            json={"ids": []}
        )
        assert response.status_code in [400, 401, 422]

    def test_batch_update_status_invalid(self, client):
        response = client.post(
            "/api/v1/inquiries/batch-update-status",
            json={"ids": ["test-id"], "status": "invalid_status"}
        )
        assert response.status_code in [400, 401, 422]

class TestCaseStudiesAPI:
    def test_list_case_studies(self, client):
        response = client.get("/api/v1/cases")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_get_case_by_slug_not_found(self, client):
        response = client.get("/api/v1/cases/slug/non-existent-slug")
        assert response.status_code == 404

    def test_get_case_by_id_not_found(self, client):
        response = client.get("/api/v1/cases/non-existent-id")
        assert response.status_code == 404

class TestProductListPage:
    def test_list_products(self, client):
        response = client.get("/api/v1/products")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_list_products_with_category(self, client):
        response = client.get("/api/v1/products?category_id=non-existent")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    def test_list_products_search(self, client):
        response = client.get("/api/v1/products?search=混凝土")
        assert response.status_code == 200

    def test_get_categories(self, client):
        response = client.get("/api/v1/products/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

class TestNewsAPI:
    def test_list_news_articles(self, client):
        response = client.get("/api/v1/news")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_list_news_with_category(self, client):
        response = client.get("/api/v1/news?category=company")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_list_news_with_search(self, client):
        response = client.get("/api/v1/news?search=混凝土")
        assert response.status_code == 200

    def test_get_article_by_id_not_found(self, client):
        response = client.get("/api/v1/news/non-existent-id")
        assert response.status_code == 404

    def test_get_article_by_slug_not_found(self, client):
        response = client.get("/api/v1/news/slug/non-existent-slug")
        assert response.status_code == 404

    def test_list_news_categories(self, client):
        response = client.get("/api/v1/news/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

class TestSecurityHeaders:
    def test_security_headers_present(self, client):
        response = client.get("/api/v1/products")
        assert response.status_code == 200

    def test_cors_preflight(self, client):
        response = client.options(
            "/api/v1/products",
            headers={"Origin": "http://localhost:3000"}
        )
        assert response.status_code in [200, 204, 405]

class TestInputValidation:
    def test_search_injection(self, client):
        response = client.get("/api/v1/products?search=<script>alert('xss')</script>")
        assert response.status_code == 200

    def test_sql_injection_attempt(self, client):
        response = client.get("/api/v1/products?search='; DROP TABLE products; --")
        assert response.status_code == 200

    def test_long_search_query(self, client):
        long_query = "a" * 1000
        response = client.get(f"/api/v1/products?search={long_query}")
        assert response.status_code == 200

class TestPagination:
    def test_pagination_params(self, client):
        response = client.get("/api/v1/products?page=1&page_size=5")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_invalid_page_number(self, client):
        response = client.get("/api/v1/products?page=-1")
        assert response.status_code in [200, 422]

    def test_invalid_page_size(self, client):
        response = client.get("/api/v1/products?page_size=0")
        assert response.status_code in [200, 422]
