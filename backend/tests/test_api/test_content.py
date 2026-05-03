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
            "status": "published"
        }

        response = authenticated_client.post("/api/v1/content/pages", json=page_data)
        assert response.status_code in [200, 201]

        data = response.json()
        assert data["title"] == page_data["title"]
        assert "id" in data

    def test_list_pages(self, client):
        """测试获取页面列表"""
        response = client.get("/api/v1/content/pages?page=1&page_size=10")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data

    def test_list_pages_with_filters(self, client):
        """测试带筛选条件的页面列表"""
        response = client.get("/api/v1/content/pages?page_type=page&is_published=true")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data

    def test_get_page_by_slug(self, client):
        """测试按slug获取页面"""
        response = client.get("/api/v1/content/pages/slug/about-us")
        assert response.status_code in [200, 404]

    def test_get_nonexistent_page(self, client):
        """测试获取不存在的页面"""
        response = client.get("/api/v1/content/pages/slug/nonexistent-page-xyz")
        assert response.status_code == 404

    def test_get_page_detail(self, authenticated_client):
        """测试获取页面详情"""
        # 先创建一个页面
        page_data = {
            "title": "测试页面",
            "slug": "test-page",
            "content": "<h1>测试页面内容</h1>",
            "summary": "测试页面摘要"
        }
        create_response = authenticated_client.post("/api/v1/content/pages", json=page_data)
        assert create_response.status_code in [200, 201]
        
        page_id = create_response.json()["id"]
        
        # 然后获取详情
        response = authenticated_client.get(f"/api/v1/content/pages/{page_id}")
        assert response.status_code == 200
        assert response.json()["title"] == "测试页面"

    def test_update_page(self, authenticated_client):
        """测试更新页面"""
        # 先创建一个页面
        page_data = {
            "title": "原始标题",
            "slug": "original-slug",
            "content": "<h1>原始内容</h1>",
            "summary": "原始摘要"
        }
        create_response = authenticated_client.post("/api/v1/content/pages", json=page_data)
        page_id = create_response.json()["id"]

        update_data = {
            "title": "关于我们（更新版）",
            "content": "<h1>关于我们</h1><p>更新后的内容</p>"
        }

        response = authenticated_client.put(f"/api/v1/content/pages/{page_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["title"] == "关于我们（更新版）"

    def test_delete_page(self, authenticated_client):
        """测试删除页面"""
        # 先创建一个页面
        page_data = {
            "title": "待删除页面",
            "slug": "to-be-deleted",
            "content": "<h1>待删除</h1>",
            "summary": "待删除摘要"
        }
        create_response = authenticated_client.post("/api/v1/content/pages", json=page_data)
        page_id = create_response.json()["id"]

        response = authenticated_client.delete(f"/api/v1/content/pages/{page_id}")
        assert response.status_code == 200

        # 验证已删除
        get_response = authenticated_client.get(f"/api/v1/content/pages/{page_id}")
        assert get_response.status_code == 404

    def test_publish_page(self, authenticated_client):
        """测试发布页面"""
        # 先创建一个草稿页面
        page_data = {
            "title": "草稿页面",
            "slug": "draft-page",
            "content": "<h1>草稿内容</h1>",
            "summary": "草稿摘要",
            "status": "draft"
        }
        create_response = authenticated_client.post("/api/v1/content/pages", json=page_data)
        page_id = create_response.json()["id"]

        # 更新为发布状态
        update_data = {"status": "published"}
        response = authenticated_client.put(f"/api/v1/content/pages/{page_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["status"] == "published"

    def test_unpublish_page(self, authenticated_client):
        """测试取消发布页面"""
        # 先创建一个已发布页面
        page_data = {
            "title": "已发布页面",
            "slug": "published-page",
            "content": "<h1>已发布内容</h1>",
            "summary": "已发布摘要",
            "status": "published"
        }
        create_response = authenticated_client.post("/api/v1/content/pages", json=page_data)
        page_id = create_response.json()["id"]

        # 更新为草稿状态
        update_data = {"status": "draft"}
        response = authenticated_client.put(f"/api/v1/content/pages/{page_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["status"] == "draft"


class TestContentVersionControl:
    """内容版本控制测试"""

    def test_create_version(self, authenticated_client):
        """测试创建版本"""
        # 先创建一个页面
        page_data = {
            "title": "版本测试页面",
            "slug": "version-test",
            "content": "<h1>版本测试内容</h1>",
            "summary": "版本测试摘要"
        }
        create_response = authenticated_client.post("/api/v1/content/pages", json=page_data)
        page_id = create_response.json()["id"]

        version_data = {
            "change_log": "更新公司介绍内容"
        }

        response = authenticated_client.post(f"/api/v1/content/pages/{page_id}/versions", json=version_data)
        assert response.status_code in [200, 201]

        if response.status_code in [200, 201]:
            data = response.json()
            assert "version_number" in data
            assert "id" in data

    def test_list_versions(self, authenticated_client):
        """测试获取版本列表"""
        # 先创建一个页面
        page_data = {
            "title": "版本列表测试",
            "slug": "version-list-test",
            "content": "<h1>版本列表测试内容</h1>",
            "summary": "版本列表测试摘要"
        }
        create_response = authenticated_client.post("/api/v1/content/pages", json=page_data)
        page_id = create_response.json()["id"]

        response = authenticated_client.get(f"/api/v1/content/pages/{page_id}/versions")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_get_version_detail(self, authenticated_client):
        """测试获取版本详情"""
        # 先创建一个页面和版本
        page_data = {
            "title": "版本详情测试",
            "slug": "version-detail-test",
            "content": "<h1>版本详情测试内容</h1>",
            "summary": "版本详情测试摘要"
        }
        create_response = authenticated_client.post("/api/v1/content/pages", json=page_data)
        page_id = create_response.json()["id"]

        version_response = authenticated_client.post(f"/api/v1/content/pages/{page_id}/versions", json={"change_log": "测试版本"})
        version_id = version_response.json()["id"]

        response = authenticated_client.get(f"/api/v1/content/pages/{page_id}/versions/{version_id}")
        assert response.status_code == 200

    def test_rollback_to_version(self, authenticated_client):
        """测试回滚到指定版本"""
        # 先创建一个页面和版本
        page_data = {
            "title": "回滚测试页面",
            "slug": "rollback-test",
            "content": "<h1>原始内容</h1>",
            "summary": "原始摘要"
        }
        create_response = authenticated_client.post("/api/v1/content/pages", json=page_data)
        page_id = create_response.json()["id"]

        # 创建一个版本
        version_response = authenticated_client.post(f"/api/v1/content/pages/{page_id}/versions", json={"change_log": "创建初始版本"})
        version_id = version_response.json()["id"]

        # 修改页面内容
        update_response = authenticated_client.put(f"/api/v1/content/pages/{page_id}", json={"title": "修改后的标题"})
        assert update_response.status_code == 200

        # 回滚到版本
        rollback_data = {
            "version_id": version_id
        }

        response = authenticated_client.post(f"/api/v1/content/pages/{page_id}/rollback", json=rollback_data)
        assert response.status_code == 200

        data = response.json()
        assert "message" in data

    def test_rollback_nonexistent_version(self, authenticated_client):
        """测试回滚到不存在的版本"""
        # 先创建一个页面
        page_data = {
            "title": "回滚失败测试",
            "slug": "rollback-fail-test",
            "content": "<h1>回滚失败测试内容</h1>",
            "summary": "回滚失败测试摘要"
        }
        create_response = authenticated_client.post("/api/v1/content/pages", json=page_data)
        page_id = create_response.json()["id"]

        rollback_data = {
            "version_id": "nonexistent-version-id"
        }

        response = authenticated_client.post(f"/api/v1/content/pages/{page_id}/rollback", json=rollback_data)
        assert response.status_code == 404

    def test_create_version_without_log(self, authenticated_client):
        """测试创建版本时不提供变更日志"""
        # 先创建一个页面
        page_data = {
            "title": "无日志版本测试",
            "slug": "no-log-version",
            "content": "<h1>无日志版本测试内容</h1>",
            "summary": "无日志版本测试摘要"
        }
        create_response = authenticated_client.post("/api/v1/content/pages", json=page_data)
        page_id = create_response.json()["id"]

        response = authenticated_client.post(f"/api/v1/content/pages/{page_id}/versions")
        assert response.status_code in [200, 201]

    def test_version_number_increment(self, authenticated_client):
        """测试版本号递增"""
        # 先创建一个页面
        page_data = {
            "title": "版本递增测试",
            "slug": "version-increment-test",
            "content": "<h1>版本递增测试内容</h1>",
            "summary": "版本递增测试摘要"
        }
        create_response = authenticated_client.post("/api/v1/content/pages", json=page_data)
        page_id = create_response.json()["id"]

        version_data_1 = {"change_log": "第一次修改"}
        response_1 = authenticated_client.post(f"/api/v1/content/pages/{page_id}/versions", json=version_data_1)

        version_data_2 = {"change_log": "第二次修改"}
        response_2 = authenticated_client.post(f"/api/v1/content/pages/{page_id}/versions", json=version_data_2)

        if response_1.status_code in [200, 201] and response_2.status_code in [200, 201]:
            data_1 = response_1.json()
            data_2 = response_2.json()
            assert data_2["version_number"] > data_1["version_number"]


class TestContentSearch:
    """内容搜索测试"""

    def test_search_pages_by_title(self, client):
        """测试按标题搜索页面"""
        response = client.get("/api/v1/content/pages/search?q=关于")
        assert response.status_code == 200

    def test_search_pages_empty_result(self, client):
        """测试搜索无结果"""
        response = client.get("/api/v1/content/pages/search?q=不存在的关键词xyz123")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 0

    def test_search_pages_with_pagination(self, client):
        """测试搜索带分页"""
        response = client.get("/api/v1/content/pages/search?q=测试&page=1&page_size=5")
        assert response.status_code == 200
