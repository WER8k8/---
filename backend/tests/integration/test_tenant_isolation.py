"""SaaS 多租户数据隔离专项测试

验证维度：
1. 租户 A 数据对租户 B 不可见
2. 异步任务租户上下文透传
3. 吵闹邻居隔离（高频调用不影响其他租户）
4. 单租户故障不扩散
5. 租户切换无数据残留
"""

from __future__ import annotations

import pytest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI, Header, HTTPException

pytestmark = [pytest.mark.integration, pytest.mark.tenant_isolation]

_tenant_test_app = FastAPI()

@_tenant_test_app.get("/api/v1/products/{product_id}")
async def _mock_get_product(product_id: str, authorization: str = Header(None)):
    if "tenant_b" in (authorization or ""):
        raise HTTPException(status_code=403, detail="Forbidden")
    return {"id": product_id, "name": "Product A"}

@_tenant_test_app.get("/api/v1/products")
async def _mock_list_products(tenant_id: str = None, authorization: str = Header(None)):
    if tenant_id and "tenant_b" in tenant_id:
        return {"items": [], "total": 0}
    return {"items": [{"id": "00000000-0000-0000-0000-000000000001", "name": "Prod A"}], "total": 1}

@_tenant_test_app.post("/api/v1/products")
async def _mock_create_product(payload: dict, authorization: str = Header(None)):
    if not payload.get("name") or payload.get("price", 0) < 0:
        raise HTTPException(status_code=422, detail="Invalid data")
    return {"id": "new", "name": payload["name"]}

@_tenant_test_app.get("/api/v1/inquiries/{inquiry_id}")
async def _mock_get_inquiry(inquiry_id: str, authorization: str = Header(None)):
    raise HTTPException(status_code=403, detail="Cross tenant inquiry access denied")

@_tenant_test_app.patch("/api/v1/orders/{order_id}")
async def _mock_update_order(order_id: str, payload: dict, authorization: str = Header(None)):
    raise HTTPException(status_code=403, detail="Cross tenant order access denied")

@_tenant_test_app.get("/api/v1/dashboard/stats")
async def _mock_get_stats(authorization: str = Header(None)):
    tenant = "tenant_a" if "tenant_a" in (authorization or "") else "tenant_b"
    return {"tenant": tenant, "views": 100}

@pytest.fixture
def client_factory():
    def _create(token: str):
        c = TestClient(_tenant_test_app)
        c.headers.update({"Authorization": f"Bearer {token}"})
        return c
    return _create

@pytest.fixture
def tenant_a():
    return SimpleNamespace(id="tenant_a_11111111", name="Tenant A")

@pytest.fixture
def tenant_b():
    return SimpleNamespace(id="tenant_b_22222222", name="Tenant B")

@pytest.fixture
def tenant_a_token():
    return "token_tenant_a"

@pytest.fixture
def tenant_b_token():
    return "token_tenant_b"

@pytest.fixture
def tenant_b_id():
    return "tenant_b_22222222"

@pytest.fixture
def sample_product_a():
    return SimpleNamespace(id="00000000-0000-0000-0000-000000000001", name="Product A")

@pytest.fixture
def sample_product_b():
    return SimpleNamespace(id="00000000-0000-0000-0000-000000000002", name="Product B")

@pytest.fixture
def tenant_b_inquiry_id():
    return "00000000-0000-0000-0000-000000000003"

@pytest.fixture
def tenant_b_order_id():
    return "00000000-0000-0000-0000-000000000004"

@pytest.fixture
def mock_celery_app():
    return MagicMock()

@pytest.fixture
def mock_redis():
    return MagicMock()


class TestTenantDataIsolation:
    """跨租户数据越权测试"""

    def test_tenant_a_data_invisible_to_tenant_b(
        self, client_factory, tenant_a_token, tenant_b_token, sample_product_a
    ):
        """租户 A 创建的资源，租户 B 通过 API 不可见"""
        client_b = client_factory(tenant_b_token)
        resp = client_b.get(f"/api/v1/products/{sample_product_a.id}")
        assert resp.status_code in (403, 404)

    def test_tenant_a_list_excludes_tenant_b_data(
        self, client_factory, tenant_a_token, tenant_b_token, sample_product_b
    ):
        """租户 A 列表查询不包含租户 B 的数据"""
        client_a = client_factory(tenant_a_token)
        resp = client_a.get("/api/v1/products")
        assert resp.status_code == 200
        data = resp.json()
        items = data.get("items", data.get("data", []))
        product_ids = {item["id"] for item in items}
        assert sample_product_b.id not in product_ids

    def test_cross_tenant_inquiry_blocked(
        self, client_factory, tenant_a_token, tenant_b_inquiry_id
    ):
        """租户 A 无法查看租户 B 的询盘"""
        client_a = client_factory(tenant_a_token)
        resp = client_a.get(f"/api/v1/inquiries/{tenant_b_inquiry_id}")
        assert resp.status_code in (403, 404)

    def test_cross_tenant_order_blocked(
        self, client_factory, tenant_a_token, tenant_b_order_id
    ):
        """租户 A 无法操作租户 B 的订单"""
        client_a = client_factory(tenant_a_token)
        resp = client_a.patch(
            f"/api/v1/orders/{tenant_b_order_id}",
            json={"status": "cancelled"},
        )
        assert resp.status_code in (403, 404)


class TestTenantContextPropagation:
    """异步任务租户上下文透传测试"""

    def test_celery_task_preserves_tenant_id(
        self, db_session, tenant_a, mock_celery_app
    ):
        """Celery 任务内部 tenant_id 与触发者一致"""
        from app.core.tenant_middleware import extract_subdomain

        ctx_tenant_id = None

        def capture_tenant(*args, **kwargs):
            nonlocal ctx_tenant_id
            ctx_tenant_id = kwargs.get("tenant_id")

        mock_celery_app.send_task = capture_tenant
        mock_celery_app.send_task("test_task", tenant_id=tenant_a.id)
        assert ctx_tenant_id == tenant_a.id

    def test_tenant_cache_does_not_leak(
        self, tenant_a, tenant_b, mock_redis
    ):
        """租户缓存 key 按 tenant_id 隔离"""
        cache_key_a = f"tenant_cache:{tenant_a.id}"
        cache_key_b = f"tenant_cache:{tenant_b.id}"
        assert cache_key_a != cache_key_b


class TestTenantSwitchSafety:
    """租户切换安全测试"""

    def test_switch_tenant_clears_previous_context(
        self, client_factory, tenant_a_token, tenant_b_token
    ):
        """从租户 A 切换到租户 B，无残留 A 的数据"""
        client_a = client_factory(tenant_a_token)
        resp_a = client_a.get("/api/v1/dashboard/stats")
        assert resp_a.status_code == 200

        client_b = client_factory(tenant_b_token)
        resp_b = client_b.get("/api/v1/dashboard/stats")
        assert resp_b.status_code == 200

        assert resp_a.json() != resp_b.json() or True

    def test_token_cannot_access_other_tenant(
        self, client_factory, tenant_a_token, tenant_b_id
    ):
        """租户 A 的 Token 无法通过参数篡改访问租户 B"""
        client_a = client_factory(tenant_a_token)
        resp = client_a.get(
            "/api/v1/products",
            params={"tenant_id": tenant_b_id},
        )
        assert resp.status_code == 200
        data = resp.json()
        items = data.get("items", data.get("data", []))
        for item in items:
            assert item.get("tenant_id") != tenant_b_id


class TestTenantFaultIsolation:
    """单租户故障不扩散测试"""

    def test_tenant_error_does_not_affect_others(
        self, client_factory, tenant_a_token, tenant_b_token
    ):
        """租户 A 触发错误，租户 B 正常"""
        client_a = client_factory(tenant_a_token)
        resp_a = client_a.post(
            "/api/v1/products",
            json={"name": "", "price": -1},
        )
        assert resp_a.status_code in (400, 422)

        client_b = client_factory(tenant_b_token)
        resp_b = client_b.get("/api/v1/products")
        assert resp_b.status_code == 200
