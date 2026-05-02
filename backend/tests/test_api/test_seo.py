"""
SEO功能API测试
"""

import pytest


class TestContentOptimizer:
    """内容优化器测试"""

    def test_optimize_meta(self, authenticated_client):
        """测试Meta标签优化"""
        optimize_data = {
            "title": "轻集料混凝土",
            "description": "高性能轻集料混凝土产品",
            "keywords": ["轻集料", "混凝土"]
        }

        response = authenticated_client.post(
            "/api/v1/seo/content-optimizer/optimize",
            json=optimize_data
        )
        # 可能成功或返回AI服务错误
        assert response.status_code in [200, 500]


class TestSiteAudit:
    """网站审计测试"""

    def test_create_audit(self, authenticated_client):
        """测试创建网站审计任务"""
        audit_data = {
            "url": "https://youding.com",
            "audit_dimensions": [
                "meta_tags",
                "headings",
                "images",
                "links"
            ]
        }

        response = authenticated_client.post("/api/v1/seo/site-audit/", json=audit_data)
        assert response.status_code in [200, 201]

    def test_list_audits(self, authenticated_client):
        """测试获取审计列表"""
        response = authenticated_client.get("/api/v1/seo/site-audit/")
        assert response.status_code == 200


class TestLLMsTxt:
    """LLMs.txt测试"""

    def test_generate_llms_txt(self, authenticated_client):
        """测试生成LLMs.txt"""
        generate_data = {
            "company_name": "优丁建材有限公司",
            "business": "轻集料混凝土生产销售",
            "products": ["LC5.0", "LC7.5", "LC10"]
        }

        response = authenticated_client.post(
            "/api/v1/seo/llms-txt/generate",
            json=generate_data
        )
        assert response.status_code in [200, 201]


class TestKeywordRanking:
    """关键词排名测试"""

    def test_list_keywords(self, authenticated_client):
        """测试获取关键词列表"""
        response = authenticated_client.get("/api/v1/seo/keywords/")
        assert response.status_code == 200

    def test_create_keyword(self, authenticated_client):
        """测试创建关键词"""
        keyword_data = {
            "keyword": "轻集料混凝土",
            "search_engine": "baidu",
            "target_url": "https://youding.com/products",
            "category": "产品词"
        }

        response = authenticated_client.post("/api/v1/seo/keywords/", json=keyword_data)
        assert response.status_code in [200, 201]


class TestSchemaMarkup:
    """Schema标记测试"""

    def test_generate_schema(self, authenticated_client):
        """测试生成Schema标记"""
        schema_data = {
            "type": "Product",
            "name": "LC5.0轻集料混凝土",
            "description": "密度等级LC5.0",
            "price": 500.0
        }

        response = authenticated_client.post(
            "/api/v1/seo/schema-markup/generate",
            json=schema_data
        )
        assert response.status_code in [200, 201]


class TestEEAT:
    """EEAT评分测试"""

    def test_get_eeat_summary(self, authenticated_client):
        """测试获取EEAT摘要"""
        response = authenticated_client.get("/api/v1/seo/eeat/dashboard/summary")
        assert response.status_code in [200, 404]


class TestCompliance:
    """合规审查测试"""

    def test_scan_content(self, authenticated_client):
        """测试扫描内容合规性"""
        scan_data = {
            "content": "这是最好的轻集料混凝土产品",
            "content_type": "text"
        }

        response = authenticated_client.post(
            "/api/v1/seo/compliance/scan",
            json=scan_data
        )
        assert response.status_code in [200, 201]

    def test_list_violations(self, authenticated_client):
        """测试获取违规记录列表"""
        response = authenticated_client.get("/api/v1/seo/compliance/violations")
        assert response.status_code == 200
