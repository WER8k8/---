"""出海国家矩阵与程序化方案落地页自动化测试套件。

覆盖：
1. 出海四大战区（GCC, EU, ASEAN, NA）国家档案完整性与端口配置
2. /api/v1/geo/solutions 国家战区列表 API 响应
3. /api/v1/geo/solutions/{country_code} 专项痛点与规范 API 响应
4. /api/v1/geo/solutions/{country_code}/{product_slug} 全量落地页 Bundle (SEO/Schema/FAQ/Logistics)
5. Sitemap 动态注入海外 5 国程序化方案 Landing URL 验证
6. 异常参数与不存在国家的 404 容错防崩
"""

import uuid
import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from app.models.product import Category, Product
from app.models.tenant import Tenant, TenantPlan
from app.services.geo.geo_matrix_landing_service import COUNTRY_PROFILES, GeoMatrixLandingService


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def geo_test_data():
    """准备国家矩阵落地页测试数据。"""
    db = next(get_db())
    created_tenant = False
    created_cat = False
    try:
        tenant = db.query(Tenant).filter(Tenant.is_active.is_(True)).first()
        if not tenant:
            plan = db.query(TenantPlan).first()
            if not plan:
                plan = TenantPlan(
                    name="旗舰版",
                    code=f"flagship-{uuid.uuid4().hex[:6]}",
                    price_monthly=2000,
                    price_yearly=20000,
                )
                db.add(plan)
                db.flush()
            tenant = Tenant(
                name="优丁中东欧亚海外出海基地",
                domain=f"test-geo-{uuid.uuid4().hex[:6]}.com",
                plan_id=plan.id,
                is_active=True,
            )
            db.add(tenant)
            db.flush()
            created_tenant = True

        cat = db.query(Category).filter(Category.is_active.is_(True)).first()
        if not cat:
            cat = Category(
                name="特种耐火保温",
                slug=f"fireproof-{uuid.uuid4().hex[:6]}",
                is_active=True,
            )
            db.add(cat)
            db.flush()
            created_cat = True

        p1 = Product(
            tenant_id=tenant.id,
            category_id=cat.id,
            name="出海高强轻质陶粒板",
            name_en="Ultra-Lightweight Ceramsite Panel",
            slug=f"ceramsite-panel-{uuid.uuid4().hex[:6]}",
            density="420 kg/m3",
            strength="4.8 MPa",
            thermal_conductivity="0.075 W/(m*K)",
            fire_rating="Class A1",
            is_active=True,
        )
        db.add(p1)
        db.commit()
        db.refresh(p1)
        db.refresh(tenant)

        yield {"tenant": tenant, "product": p1}
    finally:
        try:
            db.query(Product).filter(Product.id == p1.id).delete(synchronize_session=False)
            if created_cat:
                db.query(Category).filter(Category.id == cat.id).delete(synchronize_session=False)
            if created_tenant:
                db.query(Tenant).filter(Tenant.id == tenant.id).delete(synchronize_session=False)
            db.commit()
        except Exception:
            db.rollback()
        db.close()


def test_01_country_profiles_integrity():
    """测试 1: 验证出海战区 5 国档案核心字段完整性。"""
    required_keys = [
        "country_code",
        "country_name_zh",
        "country_name_en",
        "flag_emoji",
        "region_name",
        "destination_ports",
        "transit_days",
        "primary_pain_points",
        "local_standards",
        "preferential_tariffs",
        "container_suggestion",
        "currency",
        "target_climate",
    ]
    for code in ["sa", "ae", "de", "vn", "us"]:
        assert code in COUNTRY_PROFILES
        profile = COUNTRY_PROFILES[code]
        for k in required_keys:
            assert k in profile, f"Missing key {k} in country profile {code}"
        assert len(profile["destination_ports"]) >= 1
        assert len(profile["primary_pain_points"]) >= 2
        assert len(profile["local_standards"]) >= 2


def test_02_api_list_solutions(client):
    """测试 2: /api/v1/geo/solutions 返回所有支持国家与重点港口。"""
    res = client.get("/api/v1/geo/solutions")
    assert res.status_code == 200
    body = res.json()
    assert body.get("code") == 0
    countries = body.get("data", [])
    assert len(countries) >= 5
    country_codes = [c["country_code"] for c in countries]
    assert "sa" in country_codes
    assert "ae" in country_codes
    assert "de" in country_codes
    assert "vn" in country_codes
    assert "us" in country_codes


def test_03_api_single_country_profile(client):
    """测试 3: /api/v1/geo/solutions/{country_code} 获取沙特与德国方案。"""
    res_sa = client.get("/api/v1/geo/solutions/sa")
    assert res_sa.status_code == 200
    body_sa = res_sa.json()
    assert body_sa["data"]["country_name_zh"] == "沙特阿拉伯"
    assert "Dammam" in body_sa["data"]["destination_ports"][0]

    res_de = client.get("/api/v1/geo/solutions/de")
    assert res_de.status_code == 200
    body_de = res_de.json()
    assert body_de["data"]["country_name_zh"] == "德国"
    assert "Passivhaus" in body_de["data"]["primary_pain_points"][0]


def test_04_api_country_product_landing_bundle(client, geo_test_data):
    """测试 4: /api/v1/geo/solutions/{country_code}/{product_slug} 完整方案数据包。"""
    product = geo_test_data["product"]
    res = client.get(f"/api/v1/geo/solutions/sa/{product.slug}")
    assert res.status_code == 200
    body = res.json()
    assert body.get("code") == 0
    bundle = body.get("data", {})

    # 1. 验证基础国家档案与产品信息（含动态抽取 key_specs 通用指标）
    assert bundle["country_profile"]["country_code"] == "sa"
    assert bundle["product"]["slug"] == product.slug
    assert bundle["product"]["fire_rating"] == "Class A1"
    assert "key_specs" in bundle["product"]
    assert len(bundle["product"]["key_specs"]) >= 4

    # 2. 验证 SEO 针对沙特定制
    seo = bundle.get("seo", {})
    assert "Saudi Arabia Certified" in seo.get("meta_title", "")
    assert "Dammam" in seo.get("meta_title", "")
    assert "/solutions/sa/" in seo.get("canonical_url", "")

    # 3. 验证海运物流与履约单证
    shipping = bundle.get("shipping_logistics", {})
    assert "18 - 22 天直航" in shipping.get("transit_days", "")
    assert "Commercial Invoice (CI)" in shipping.get("documents_provided", [])

    # 4. 验证中英双语 FAQ
    faqs = bundle.get("faqs", [])
    assert len(faqs) >= 3
    assert "Saudi Arabia" in faqs[0]["question_en"]
    assert "沙特阿拉伯" in faqs[0]["question_zh"]

    # 5. 验证 Schema.org 结构化数据
    schemas = bundle.get("schemas", {})
    assert schemas["product"]["@type"] == "Product"
    assert schemas["product"]["offers"]["areaServed"]["name"] == "Saudi Arabia"
    assert schemas["breadcrumbs"]["@type"] == "BreadcrumbList"


def test_05_sitemap_geo_matrix_urls_injected(client, geo_test_data):
    """测试 5: 验证动态 Sitemap.xml 已成功注入海外出海 5 国程序化方案着陆页。"""
    product = geo_test_data["product"]
    res = client.get("/sitemap.xml")
    assert res.status_code == 200
    xml = res.text
    # 验证海外 5 国方案 URL 均被注入
    for c_code in ["sa", "ae", "de", "vn", "us"]:
        target_loc = f"/solutions/{c_code}/{product.slug}"
        assert target_loc in xml, f"Loc {target_loc} not found in sitemap.xml"


def test_06_nonexistent_country_or_product_404(client, geo_test_data):
    """测试 6: 不存在的国家或产品返回 404，不崩溃。"""
    product = geo_test_data["product"]
    res_bad_country = client.get(f"/api/v1/geo/solutions/xyz/{product.slug}")
    assert res_bad_country.status_code == 404

    res_bad_product = client.get("/api/v1/geo/solutions/sa/non-existent-slug-12345")
    assert res_bad_product.status_code == 404

