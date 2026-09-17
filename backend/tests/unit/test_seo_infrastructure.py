"""SEO 基础设施与千人千面 Google 展示优化专项测试套件。

覆盖 10 项严苛门禁：
1. robots.txt 规范与 Crawl Budget 指令
2. llms.txt 标准 Markdown 输出 (AI Overviews 接入)
3. llms-full.txt 深度知识库参数提取
4. 动态 Sitemap.xml (支持 12 语种 hreflang 与 Google Image 扩展)
5. Sitemap Index 规范
6. /products/sitemap-feed 支持多租户过滤
7. /products/slug/{slug}/seo-bundle 全量信号包 (Product/Breadcrumb/FAQPage)
8. ProductSeoGenerator 千人千面与内容指纹唯一性
9. /seo/product-seo/{id}/preview Google SERP 模拟预览与对比矩阵
10. ProductSeoGenerator 数据持久化闭环 (seo_metadata + product_faqs)
"""

import uuid
import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, engine, get_db
from app.main import app
from app.models.product import Category, Product, ProductFaq
from app.models.seo_metadata import SeoMetadata
from app.models.tenant import Tenant
from app.models.user import User
from app.services.seo.product_seo_generator import ProductSeoGenerator


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def seo_test_data():
    """准备基础测试数据：分类、租户与两款不同参数的产品。"""
    from app.models.tenant import Tenant, TenantPlan

    db = next(get_db())
    created_tenant = False
    try:
        tenant = db.query(Tenant).filter(Tenant.is_active.is_(True)).first()
        if not tenant:
            plan = db.query(TenantPlan).first()
            if not plan:
                plan = TenantPlan(name="专业版", code=f"pro-{uuid.uuid4().hex[:6]}", price_monthly=1000, price_yearly=10000)
                db.add(plan)
                db.flush()
            tenant = Tenant(
                name="优丁绿色建材测试厂",
                domain=f"test-seo-{uuid.uuid4().hex[:6]}.com",
                plan_id=plan.id,
                is_active=True,
            )
            db.add(tenant)
            db.flush()
            created_tenant = True

        cat = db.query(Category).filter(Category.is_active.is_(True)).first()
        created_cat = False
        if not cat:
            cat = Category(
                name="新型保温砂浆",
                slug=f"mortar-cat-{uuid.uuid4().hex[:6]}",
                is_active=True,
            )
            db.add(cat)
            db.flush()
            created_cat = True

        p1 = Product(
            tenant_id=tenant.id,
            category_id=cat.id,
            name="无机轻集料保温砂浆 Type-A",
            name_en="Inorganic Lightweight Thermal Mortar Type-A",
            slug=f"mortar-type-a-{uuid.uuid4().hex[:6]}",
            density="320 kg/m³",
            strength="3.8 MPa",
            thermal_conductivity="0.065 W/(m·K)",
            fire_rating="A1",
            is_active=True,
        )
        p2 = Product(
            tenant_id=tenant.id,
            category_id=cat.id,
            name="超轻陶粒承重混凝土 Type-B",
            name_en="Ultralight Ceramsite Load-bearing Concrete Type-B",
            slug=f"ceramsite-type-b-{uuid.uuid4().hex[:6]}",
            density="750 kg/m³",
            strength="7.5 MPa",
            thermal_conductivity="0.12 W/(m·K)",
            fire_rating="A1",
            is_active=True,
        )
        db.add_all([p1, p2])
        db.commit()
        db.refresh(p1)
        db.refresh(p2)
        db.refresh(tenant)

        yield {"tenant": tenant, "cat": cat, "p1": p1, "p2": p2}
    finally:
        # 清理测试产品与关联数据
        try:
            db.query(ProductFaq).filter(ProductFaq.product_id.in_([p1.id, p2.id])).delete(synchronize_session=False)
            db.query(SeoMetadata).filter(SeoMetadata.resource_id.in_([p1.id, p2.id])).delete(synchronize_session=False)
            db.query(Product).filter(Product.id.in_([p1.id, p2.id])).delete(synchronize_session=False)
            if created_cat:
                db.query(Category).filter(Category.id == cat.id).delete(synchronize_session=False)
            if created_tenant:
                db.query(Tenant).filter(Tenant.id == tenant.id).delete(synchronize_session=False)
            db.commit()
        except Exception:
            db.rollback()
        db.close()


def test_01_robots_txt_endpoint(client):
    """测试 1: robots.txt 规范与 Crawl Budget 指令。"""
    res = client.get("/robots.txt")
    assert res.status_code == 200
    text = res.text
    assert "User-agent: Googlebot" in text
    assert "Allow: /products" in text
    assert "Disallow: /admin/" in text
    assert "Disallow: /client/" in text
    assert "Sitemap:" in text


def test_02_llms_txt_endpoint(client):
    """测试 2: /llms.txt 标准 Markdown 输出。"""
    res = client.get("/llms.txt")
    assert res.status_code == 200
    assert "text/markdown" in res.headers.get("content-type", "")
    assert "LLM Context & Knowledge Index" in res.text
    assert "Technical Compliance" in res.text


def test_03_llms_full_txt_endpoint(client):
    """测试 3: /llms-full.txt 深度知识库参数输出。"""
    res = client.get("/llms-full.txt")
    assert res.status_code == 200
    assert "Full AI & LLM Knowledge Base" in res.text
    assert "Density" in res.text or "密度" in res.text


def test_04_sitemap_xml_structure(client, seo_test_data):
    """测试 4: Sitemap.xml 包含 hreflang 与 Google 扩展。"""
    res = client.get("/sitemap.xml")
    assert res.status_code == 200
    assert "application/xml" in res.headers.get("content-type", "")
    xml = res.text
    assert "<urlset" in xml
    assert "xmlns:xhtml=" in xml
    assert "xmlns:image=" in xml
    assert 'hreflang="en-US"' in xml
    assert 'hreflang="x-default"' in xml
    assert seo_test_data["p1"].slug in xml


def test_05_sitemap_index_xml(client):
    """测试 5: Sitemap Index 结构符合规范。"""
    res = client.get("/sitemap-index.xml")
    assert res.status_code == 200
    assert "<sitemapindex" in res.text
    assert "<sitemap>" in res.text
    assert "/sitemap.xml</loc>" in res.text


def test_06_product_sitemap_feed_with_tenant(client, seo_test_data):
    """测试 6: /products/sitemap-feed 支持按租户隔离。"""
    tenant_id = seo_test_data["tenant"].id
    res = client.get(f"/api/v1/products/sitemap-feed?tenant_id={tenant_id}")
    assert res.status_code == 200
    payload = res.json()
    items = payload.get("data") or payload.get("items") or []
    slugs = [it["slug"] for it in items]
    assert seo_test_data["p1"].slug in slugs
    assert seo_test_data["p2"].slug in slugs


def test_07_product_seo_bundle_structure(client, seo_test_data):
    """测试 7: /products/slug/{slug}/seo-bundle 聚合全量 SEO/GEO 信号包。"""
    p1 = seo_test_data["p1"]
    res = client.get(f"/api/v1/products/slug/{p1.slug}/seo-bundle")
    assert res.status_code == 200
    data = res.json()["data"]

    assert data["canonical_url"].endswith(p1.slug)
    assert len(data["faqs"]) >= 2
    assert "information_gain" in data

    # 验证 Google Schema.org Product
    schema_prod = data["schemas"]["product"]
    assert schema_prod["@type"] == "Product"
    assert "offers" in schema_prod
    assert "aggregateRating" in schema_prod
    assert schema_prod["aggregateRating"]["ratingValue"] == "4.9"
    assert "hasMerchantReturnPolicy" in schema_prod["offers"]

    # 验证 BreadcrumbList
    schema_bread = data["schemas"]["breadcrumb"]
    assert schema_bread["@type"] == "BreadcrumbList"
    assert len(schema_bread["itemListElement"]) >= 3


def test_08_product_seo_generator_uniqueness(seo_test_data):
    """测试 8: 千人千面 — 两款不同物理参数产品的 Meta 绝不重复且指纹唯一。"""
    db = next(get_db())
    try:
        gen = ProductSeoGenerator(db)
        meta1 = gen.build_unique_meta(seo_test_data["p1"], "租户A")
        meta2 = gen.build_unique_meta(seo_test_data["p2"], "租户B")

        # 验证标题与描述不同
        assert meta1["title_zh"] != meta2["title_zh"]
        assert meta1["description_zh"] != meta2["description_zh"]
        assert meta1["title_en"] != meta2["title_en"]
        assert meta1["description_en"] != meta2["description_en"]

        # 验证指纹完全独立
        assert meta1["fingerprint"] != meta2["fingerprint"]
        assert len(meta1["fingerprint"]) == 16
    finally:
        db.close()


def test_09_product_seo_preview_endpoint(client, seo_test_data):
    """测试 9: Google SERP 模拟预览与对比矩阵 API。"""
    p1 = seo_test_data["p1"]
    res = client.get(f"/api/v1/seo/product-seo/{p1.id}/preview")
    assert res.status_code == 200
    data = res.json()["data"]

    assert "google_serp_desktop" in data
    assert "Rating: 4.9" in "".join(data["google_serp_desktop"]["rich_elements"])
    assert "information_gain_score" in data
    assert data["information_gain_score"]["score"] >= 90
    assert "comparison_matrix" in data
    assert len(data["comparison_matrix"]["rows"]) >= 4


def test_10_product_seo_generate_persists_data(seo_test_data):
    """测试 10: 端到端生成服务将 SEO 元数据与 FAQs 正确持久化入库。"""
    db = next(get_db())
    try:
        gen = ProductSeoGenerator(db)
        p1 = seo_test_data["p1"]
        tenant = seo_test_data["tenant"]

        res = gen.apply_seo_for_product(str(p1.id), tenant_id=str(tenant.id))
        assert res["status"] == "success"

        # 检查 product 表自身字段是否已更新
        fresh_p1 = db.query(Product).filter(Product.id == p1.id).first()
        assert fresh_p1 is not None
        assert fresh_p1.meta_title is not None
        assert fresh_p1.meta_description is not None
        assert "320 kg/m³" in fresh_p1.meta_title

        # 检查 seo_metadata 表
        seo_meta = db.query(SeoMetadata).filter(
            SeoMetadata.resource_type == "product",
            SeoMetadata.resource_id == str(p1.id),
        ).first()
        assert seo_meta is not None
        assert seo_meta.schema_markup is not None

        # 检查 product_faqs 表
        faqs = db.query(ProductFaq).filter(ProductFaq.product_id == str(p1.id)).all()
        assert len(faqs) >= 5
        assert any("防潮" in f.question_zh or "性能" in f.question_zh for f in faqs)
    finally:
        db.close()
