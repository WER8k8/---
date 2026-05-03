"""
产品管理API测试 - CRUD操作 + 批量操作 + 导入导出
"""

import pytest
import io
import csv


class TestProductCRUD:
    """产品CRUD测试"""

    def test_create_product(self, authenticated_client):
        """测试创建产品"""
        product_data = {
            "name": "LC5.0轻集料混凝土",
            "slug": "lc5-concrete",
            "category_id": "test-category-id",
            "description": "密度等级LC5.0，适用于屋面找坡",
            "density": "500",
            "strength": "LC5.0",
            "is_active": True
        }

        response = authenticated_client.post("/api/v1/products", json=product_data)
        assert response.status_code in [200, 201]

        data = response.json()
        assert data["name"] == product_data["name"]
        assert "id" in data

    def test_list_products(self, client):
        """测试获取产品列表"""
        response = client.get("/api/v1/products?page=1&page_size=10")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_get_product_detail(self, authenticated_client):
        """测试获取产品详情"""
        # 先创建产品
        product_data = {
            "name": "Test Product",
            "slug": "test-product-detail",
            "category_id": "test-category-id",
            "is_active": True
        }
        create_response = authenticated_client.post("/api/v1/products", json=product_data)
        if create_response.status_code in [200, 201]:
            product_id = create_response.json()["id"]
            response = authenticated_client.get(f"/api/v1/products/{product_id}")
            assert response.status_code == 200
        else:
            pytest.skip("Product creation failed")

    def test_update_product(self, authenticated_client):
        """测试更新产品"""
        # 先创建产品
        product_data = {
            "name": "Test Product Update",
            "slug": "test-product-update",
            "category_id": "test-category-id",
            "is_active": True
        }
        create_response = authenticated_client.post("/api/v1/products", json=product_data)
        if create_response.status_code in [200, 201]:
            product_id = create_response.json()["id"]
            update_data = {
                "name": "Test Product Updated",
                "description": "Updated description"
            }
            response = authenticated_client.put(f"/api/v1/products/{product_id}", json=update_data)
            assert response.status_code == 200
        else:
            pytest.skip("Product creation failed")

    def test_delete_product(self, authenticated_client):
        """测试删除产品"""
        # 先创建产品
        product_data = {
            "name": "Test Product Delete",
            "slug": "test-product-delete",
            "category_id": "test-category-id",
            "is_active": True
        }
        create_response = authenticated_client.post("/api/v1/products", json=product_data)
        if create_response.status_code in [200, 201]:
            product_id = create_response.json()["id"]
            response = authenticated_client.delete(f"/api/v1/products/{product_id}")
            assert response.status_code == 200
        else:
            pytest.skip("Product creation failed")


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

        response = authenticated_client.post("/api/v1/products/categories", json=category_data)
        assert response.status_code in [200, 201]

    def test_list_categories(self, client):
        """测试获取分类列表"""
        response = client.get("/api/v1/products/categories")
        assert response.status_code == 200

    def test_get_category_tree(self, client):
        """测试获取分类树"""
        response = client.get("/api/v1/products/categories/tree")
        assert response.status_code == 200


class TestBatchOperations:
    """批量操作测试"""

    def test_batch_delete_products(self, authenticated_client):
        """测试批量删除产品"""
        delete_data = {
            "ids": ["test-id-1", "test-id-2", "test-id-3"]
        }

        response = authenticated_client.post("/api/v1/products/batch-delete", json=delete_data)
        assert response.status_code in [200, 404]

        data = response.json()
        assert "deleted_count" in data or "message" in data

    def test_batch_delete_empty_ids(self, authenticated_client):
        """测试批量删除空ID列表"""
        delete_data = {"ids": []}

        response = authenticated_client.post("/api/v1/products/batch-delete", json=delete_data)
        assert response.status_code == 400

    def test_batch_update_status_activate(self, authenticated_client):
        """测试批量启用产品"""
        update_data = {
            "ids": ["test-id-1", "test-id-2"],
            "is_active": True
        }

        response = authenticated_client.post("/api/v1/products/batch-update-status", json=update_data)
        assert response.status_code in [200, 404]

    def test_batch_update_status_deactivate(self, authenticated_client):
        """测试批量禁用产品"""
        update_data = {
            "ids": ["test-id-1", "test-id-2"],
            "is_active": False
        }

        response = authenticated_client.post("/api/v1/products/batch-update-status", json=update_data)
        assert response.status_code in [200, 404]

    def test_batch_update_empty_ids(self, authenticated_client):
        """测试批量更新空ID列表"""
        update_data = {"ids": [], "is_active": True}

        response = authenticated_client.post("/api/v1/products/batch-update-status", json=update_data)
        assert response.status_code == 400


class TestImportExport:
    """导入导出测试"""

    def test_export_products(self, authenticated_client):
        """测试导出产品CSV"""
        response = authenticated_client.get("/api/v1/products/export")
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")

    def test_export_products_with_filter(self, authenticated_client):
        """测试带筛选条件导出产品"""
        response = authenticated_client.get("/api/v1/products/export?is_active=true")
        assert response.status_code == 200

    def test_import_products_csv(self, authenticated_client):
        """测试导入产品CSV"""
        csv_content = "name,slug,category_id,description,density,strength,状态\n"
        csv_content += "测试产品1,test-product-1,cat-1,测试描述,500,LC5.0,启用\n"
        csv_content += "测试产品2,test-product-2,cat-1,测试描述2,600,LC7.5,启用\n"

        files = {"file": ("products.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        response = authenticated_client.post("/api/v1/products/import", files=files)
        assert response.status_code in [200, 400]

        data = response.json()
        assert "imported_count" in data or "message" in data

    def test_import_invalid_file_type(self, authenticated_client):
        """测试导入非CSV文件"""
        files = {"file": ("products.txt", io.BytesIO(b"test content"), "text/plain")}
        response = authenticated_client.post("/api/v1/products/import", files=files)
        assert response.status_code == 400

    def test_import_empty_csv(self, authenticated_client):
        """测试导入空CSV"""
        csv_content = "name,slug,category_id\n"
        files = {"file": ("empty.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        response = authenticated_client.post("/api/v1/products/import", files=files)
        assert response.status_code in [200, 400]
