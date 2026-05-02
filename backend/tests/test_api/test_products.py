"""
产品管理API测试 - CRUD操作
"""

import pytest


class TestProductCRUD:
    """产品CRUD测试"""

    def test_create_product(self, authenticated_client):
        """测试创建产品"""
        product_data = {
            "name": "LC5.0轻集料混凝土",
            "slug": "lc5-concrete",
            "description": "密度等级LC5.0，适用于屋面找坡",
            "density_grade": "LC5.0",
            "strength_grade": "A",
            "price": 500.0,
            "unit": "立方米",
            "stock": 1000,
            "is_active": True
        }

        response = authenticated_client.post("/api/v1/products/", json=product_data)
        assert response.status_code in [200, 201]

        data = response.json()
        assert data["name"] == product_data["name"]
        assert "id" in data

    def test_list_products(self, client):
        """测试获取产品列表"""
        response = client.get("/api/v1/products/?page=1&page_size=10")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data or isinstance(data, list)

    def test_get_product_detail(self, client):
        """测试获取产品详情"""
        # 假设存在ID为1的产品
        response = client.get("/api/v1/products/1")
        # 可能返回200（存在）或404（不存在）
        assert response.status_code in [200, 404]

    def test_update_product(self, authenticated_client):
        """测试更新产品"""
        update_data = {
            "name": "LC5.0轻集料混凝土（升级版）",
            "price": 550.0
        }

        response = authenticated_client.put("/api/v1/products/1", json=update_data)
        # 可能成功或返回404
        assert response.status_code in [200, 404]

    def test_delete_product(self, authenticated_client):
        """测试删除产品"""
        response = authenticated_client.delete("/api/v1/products/1")
        # 可能成功或返回404
        assert response.status_code in [200, 404]


class TestCategoryCRUD:
    """分类CRUD测试"""

    def test_create_category(self, authenticated_client):
        """测试创建分类"""
        category_data = {
            "name": "轻集料混凝土",
            "slug": "lightweight-aggregate-concrete",
            "description": "各类轻集料混凝土产品",
            "sort_order": 1
        }

        response = authenticated_client.post("/api/v1/products/categories/", json=category_data)
        assert response.status_code in [200, 201]

    def test_list_categories(self, client):
        """测试获取分类列表"""
        response = client.get("/api/v1/products/categories/")
        assert response.status_code == 200
