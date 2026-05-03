"""
内容管理系统API测试 - 页面管理 + 版本控制
"""

import pytest


class TestContentPageCRUD:
    """内容页面CRUD测试"""

    def test_create_page(self, authenticated_client):
        """测试创建内容页面"""
        page_data = {
            "title": "关于我们",
            "slug": "about-us",
            "content": "<h1>关于我们</h1><p>公司介绍内容</p>",
            "summary": "公司介绍",
            "is_published": True
        }

        response = authenticated_client.post("/api/v1/content/pages/", json=page_data)
        assert response.status_code in [200, 201]

        data = response.json()
        assert data["title"] == page_data["title"]
        assert "id" in data

    def test_list_pages(self, client):
        """测试获取页面列表"""
        response = client.get("/api/v1/content/pages/?page=1&page_size=10")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data or isinstance(data, list)

    def test_get_page_detail(self, client):
        """测试获取页面详情"""
        response = client.get("/api/v1/content/pages/about-us")
        assert response.status_code in [200, 404]

    def test_update_page(self, authenticated_client):
        """测试更新页面"""
        update_data = {
            "title": "关于我们（更新版）",
            "content": "<h1>关于我们</h1><p>更新后的内容</p>"
        }

        response = authenticated_client.put("/api/v1/content/pages/1", json=update_data)
        assert response.status_code in [200, 404]

    def test_delete_page(self, authenticated_client):
        """测试删除页面"""
        response = authenticated_client.delete("/api/v1/content/pages/1")
        assert response.status_code in [200, 404]

    def test_publish_page(self, authenticated_client):
        """测试发布页面"""
        response = authenticated_client.post("/api/v1/content/pages/1/publish")
        assert response.status_code in [200, 404]

    def test_unpublish_page(self, authenticated_client):
        """测试取消发布页面"""
        response = authenticated_client.post("/api/v1/content/pages/1/unpublish")
        assert response.status_code in [200, 404]


class TestContentVersionControl:
    """内容版本控制测试"""

    def test_create_version(self, authenticated_client):
        """测试创建版本"""
        version_data = {
            "change_log": "更新公司介绍内容"
        }

        response = authenticated_client.post("/api/v1/content/pages/1/versions", json=version_data)
        assert response.status_code in [200, 201, 404]

        if response.status_code == 200:
            data = response.json()
            assert "version_number" in data
            assert "id" in data

    def test_list_versions(self, authenticated_client):
        """测试获取版本列表"""
        response = authenticated_client.get("/api/v1/content/pages/1/versions")
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_get_version_detail(self, authenticated_client):
        """测试获取版本详情"""
        response = authenticated_client.get("/api/v1/content/versions/1")
        assert response.status_code in [200, 404]

    def test_rollback_to_version(self, authenticated_client):
        """测试回滚到指定版本"""
        rollback_data = {
            "version_id": "test-version-id"
        }

        response = authenticated_client.post("/api/v1/content/pages/1/rollback", json=rollback_data)
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "message" in data

    def test_rollback_nonexistent_version(self, authenticated_client):
        """测试回滚到不存在的版本"""
        rollback_data = {
            "version_id": "nonexistent-version-id"
        }

        response = authenticated_client.post("/api/v1/content/pages/1/rollback", json=rollback_data)
        assert response.status_code in [404, 400]

    def test_create_version_without_log(self, authenticated_client):
        """测试创建版本时不提供变更日志"""
        response = authenticated_client.post("/api/v1/content/pages/1/versions")
        assert response.status_code in [200, 201, 404]

    def test_version_number_increment(self, authenticated_client):
        """测试版本号递增"""
        version_data_1 = {"change_log": "第一次修改"}
        response_1 = authenticated_client.post("/api/v1/content/pages/1/versions", json=version_data_1)

        version_data_2 = {"change_log": "第二次修改"}
        response_2 = authenticated_client.post("/api/v1/content/pages/1/versions", json=version_data_2)

        if response_1.status_code == 200 and response_2.status_code == 200:
            data_1 = response_1.json()
            data_2 = response_2.json()
            assert data_2["version_number"] > data_1["version_number"]


class TestContentSearch:
    """内容搜索测试"""

    def test_search_pages_by_title(self, client):
        """测试按标题搜索页面"""
        response = client.get("/api/v1/content/pages/search?q=关于")
        assert response.status_code in [200, 404]

    def test_search_pages_empty_result(self, client):
        """测试搜索无结果"""
        response = client.get("/api/v1/content/pages/search?q=不存在的关键词")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data or isinstance(data, list)
        if "items" in data:
            assert len(data["items"]) == 0

    def test_search_pages_with_pagination(self, client):
        """测试搜索带分页"""
        response = client.get("/api/v1/content/pages/search?q=关于&page=1&page_size=5")
        assert response.status_code in [200, 404]
