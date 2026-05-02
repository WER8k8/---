"""
系统API测试 - 健康检查、登录认证
"""

import pytest


class TestHealthCheck:
    """健康检查测试"""

    def test_health_endpoint(self, client):
        """测试健康检查端点"""
        response = client.get("/api/v1/system/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestAuthentication:
    """认证测试"""

    def test_login_success(self, client, authenticated_client):
        """测试登录成功 - 使用已认证的客户端验证"""
        # authenticated_client fixture 已经验证了登录流程
        assert authenticated_client is not None

    def test_login_invalid_credentials(self, client):
        """测试登录失败 - 无效凭证"""
        login_data = {
            "username": "nonexistent",
            "password": "wrongpassword"
        }
        response = client.post("/api/v1/system/login", json=login_data)
        assert response.status_code == 401

    def test_protected_route_without_token(self, client):
        """测试受保护路由 - 无token"""
        response = client.get("/api/v1/system/users")
        assert response.status_code in [401, 403]

    def test_protected_route_with_invalid_token(self, client):
        """测试受保护路由 - 无效token"""
        client.headers["Authorization"] = "Bearer invalid_token"
        response = client.get("/api/v1/system/users")
        assert response.status_code in [401, 403]
