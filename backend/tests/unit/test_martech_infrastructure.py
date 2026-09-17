"""谷歌营销技术 (MarTech) 专项自动化测试套件。

覆盖：
1. Google Merchant Center (GMC) 标准 XML/RSS 2.0 数据流输出与 Google Shopping 属性检验
2. GMC Feed 租户隔离与独立站适配
3. IndexNow 身份验证 /indexnow-key.txt 端点
4. IndexNow 批量 URL 提交与降级容错机制
5. 服务端营销高价值事件收集器 /api/v1/marketing/events
6. GMC 数据流 XML 实体防注入与转义安全
"""

import uuid
import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from app.models.product import Category, Product
from app.models.tenant import Tenant, TenantPlan
from app.services.marketing.gmc_feed_service import GmcFeedService


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def martech_test_data():
    """准备 MarTech 专用测试租户与产品。"""
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
                name="优丁国际外贸示范工厂",
                domain=f"test-martech-{uuid.uuid4().hex[:6]}.com",
                plan_id=plan.id,
                is_active=True,
            )
            db.add(tenant)
            db.flush()
            created_tenant = True

        cat = db.query(Category).filter(Category.is_active.is_(True)).first()
        if not cat:
            cat = Category(
                name="特种轻质混凝土",
                slug=f"concrete-{uuid.uuid4().hex[:6]}",
                is_active=True,
            )
            db.add(cat)
            db.flush()
            created_cat = True

        p1 = Product(
            tenant_id=tenant.id,
            category_id=cat.id,
            name="外贸专供微孔保温砖 P1",
            name_en="Export-Grade Micro-Porous Thermal Brick P1",
            slug=f"thermal-brick-{uuid.uuid4().hex[:6]}",
            density="380 kg/m³",
            strength="4.2 MPa",
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


def test_01_gmc_feed_xml_endpoint(client, martech_test_data):
    """测试 1: GMC Feed 根路径与 API 端点返回标准 XML。"""
    res = client.get("/gmc-feed.xml")
    assert res.status_code == 200
    assert "application/xml" in res.headers.get("content-type", "")
    xml = res.text
    assert '<rss version="2.0"' in xml
    assert 'xmlns:g="http://base.google.com/ns/1.0"' in xml
    assert "<g:id>" in xml
    assert "<g:title>" in xml
    assert "<g:price>" in xml
    assert "<g:availability>in_stock</g:availability>" in xml
    assert "<g:condition>new</g:condition>" in xml
    assert "<g:brand>" in xml
    assert "<g:shipping>" in xml


def test_02_gmc_feed_tenant_isolation(client, martech_test_data):
    """测试 2: GMC Feed 支持按租户隔离输出。"""
    tenant_id = martech_test_data["tenant"].id
    res = client.get(f"/api/v1/marketing/gmc-feed.xml?tenant_id={tenant_id}")
    assert res.status_code == 200
    xml = res.text
    assert martech_test_data["product"].slug in xml
    assert martech_test_data["tenant"].name in xml


def test_03_indexnow_key_endpoint(client):
    """测试 3: IndexNow 协议密钥验证 txt 端点。"""
    res = client.get("/indexnow-key.txt")
    assert res.status_code == 200
    assert "text/plain" in res.headers.get("content-type", "")
    assert len(res.text.strip()) >= 8

    res_api = client.get("/api/v1/seo/indexnow/key.txt")
    assert res_api.status_code == 200
    assert res_api.text.strip() == res.text.strip()


def test_04_indexnow_submit_endpoint(client, martech_test_data):
    """测试 4: IndexNow 接收 URL 并进行提交广播处理。"""
    p = martech_test_data["product"]
    payload = {
        "urls": [f"https://www.youdingjiancai.com/products/{p.slug}"],
        "host": "www.youdingjiancai.com",
    }
    res = client.post("/api/v1/seo/indexnow/submit", json=payload)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["submitted_count"] == 1
    assert data["status"] in ("success", "offline_queued")


def test_05_marketing_events_collector(client, martech_test_data):
    """测试 5: 服务端营销事件收集器正常捕获高价值外贸转化事件。"""
    events = [
        {"event_name": "generate_lead", "product_slug": martech_test_data["product"].slug, "properties": {"name": "John Doe", "phone": "+12025550143"}},
        {"event_name": "whatsapp_click", "product_slug": martech_test_data["product"].slug, "properties": {"source": "floating_bubble"}},
        {"event_name": "boq_calculated", "product_slug": martech_test_data["product"].slug, "properties": {"container": "40HQ", "volume": 58}},
    ]

    for ev in events:
        res = client.post("/api/v1/marketing/events", json=ev)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["received"] is True
        assert data["event_name"] == ev["event_name"]


def test_06_gmc_service_xml_escaping():
    """测试 6: GMC 生成器对特殊字符（&, <, >, ", '）进行严密转义。"""
    from app.services.marketing.gmc_feed_service import _escape_xml

    unsafe = 'Concrete & Mortar <"Premium" \'Grade\'>'
    safe = _escape_xml(unsafe)
    assert "&amp;" in safe
    assert "&lt;" in safe
    assert "&gt;" in safe
    assert "&quot;" in safe
    assert "&apos;" in safe
