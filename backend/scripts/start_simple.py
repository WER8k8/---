"""简化版启动脚本 - 不依赖Redis"""

from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Request
from typing import List, Optional
from datetime import datetime
import uuid
import json
import os
import sys

from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

# 设置环境变量禁用Redis
os.environ["REDIS_ENABLED"] = "false"
os.environ["ENVIRONMENT"] = "development"


# 简化版 - 不导入复杂的API路由，直接定义简单的API端点
app = FastAPI(
    title="优丁建材 API",
    description="保温建材企业官网系统API",
    version="1.0.0",
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 模拟数据存储
class Product(BaseModel):
    id: str
    name: str
    slug: str
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    price: Optional[float] = None
    unit: Optional[str] = None
    specifications: Optional[dict] = None
    is_active: bool = True
    is_featured: bool = False
    sort_order: int = 0
    created_at: datetime
    updated_at: datetime


class Category(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    parent_id: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0
    created_at: datetime
    updated_at: datetime


class CaseStudy(BaseModel):
    id: str
    project_name: str
    slug: str
    location: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None
    cover_image: Optional[str] = None
    construction_area: Optional[str] = None
    project_date: Optional[str] = None
    status: str = "published"
    is_active: bool = True
    sort_order: int = 0
    view_count: int = 0
    created_at: datetime
    updated_at: datetime


class News(BaseModel):
    id: str
    title: str
    slug: str
    summary: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None
    cover_image: Optional[str] = None
    category: str = "company"
    published_at: Optional[datetime] = None
    is_active: bool = True
    sort_order: int = 0
    view_count: int = 0
    created_at: datetime
    updated_at: datetime


class Inquiry(BaseModel):
    id: str
    name: str
    phone: str
    email: Optional[str] = None
    company: Optional[str] = None
    product_id: Optional[str] = None
    message: Optional[str] = None
    status: str = "pending"
    created_at: datetime


# 模拟数据库
mock_categories = [
    Category(
        id=str(uuid.uuid4()),
        name="轻集料混凝土",
        slug="lightweight-aggregate-concrete",
        description="专业轻集料混凝土生产，质量可靠",
        is_active=True,
        sort_order=1,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    ),
    Category(
        id=str(uuid.uuid4()),
        name="保温砂浆",
        slug="insulation-mortar",
        description="高效保温砂浆，节能环保",
        is_active=True,
        sort_order=2,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    ),
    Category(
        id=str(uuid.uuid4()),
        name="陶粒混凝土",
        slug="ceramsite-concrete",
        description="优质陶粒混凝土，性能优越",
        is_active=True,
        sort_order=3,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    ),
]

mock_products = [
    Product(
        id=str(uuid.uuid4()),
        name="LC5.0轻集料混凝土",
        slug="lc5-0-lightweight-concrete",
        category_id=mock_categories[0].id,
        category_name=mock_categories[0].name,
        description="干密度等级500级，抗压强度5.0MPa的优质轻集料混凝土，适用于屋面保温、室内垫层等场景",
        price=280.0,
        unit="元/立方米",
        is_active=True,
        is_featured=True,
        sort_order=1,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    ),
    Product(
        id=str(uuid.uuid4()),
        name="LC7.5轻集料混凝土",
        slug="lc7-5-lightweight-concrete",
        category_id=mock_categories[0].id,
        category_name=mock_categories[0].name,
        description="干密度等级600级，抗压强度7.5MPa的轻集料混凝土，综合性能优越，适用于多种建筑场景",
        price=320.0,
        unit="元/立方米",
        is_active=True,
        is_featured=True,
        sort_order=2,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    ),
    Product(
        id=str(uuid.uuid4()),
        name="LC10.0轻集料混凝土",
        slug="lc10-0-lightweight-concrete",
        category_id=mock_categories[0].id,
        category_name=mock_categories[0].name,
        description="干密度等级700级，抗压强度10.0MPa的高强度轻集料混凝土，承载能力强",
        price=360.0,
        unit="元/立方米",
        is_active=True,
        is_featured=False,
        sort_order=3,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    ),
    Product(
        id=str(uuid.uuid4()),
        name="膨胀珍珠岩保温砂浆",
        slug="expanded-perlite-insulation-mortar",
        category_id=mock_categories[1].id,
        category_name=mock_categories[1].name,
        description="以膨胀珍珠岩为骨料的保温砂浆，导热系数低，保温效果好",
        price=85.0,
        unit="元/袋",
        is_active=True,
        is_featured=True,
        sort_order=1,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    ),
    Product(
        id=str(uuid.uuid4()),
        name="玻化微珠保温砂浆",
        slug="vitrified-microbead-insulation-mortar",
        category_id=mock_categories[1].id,
        category_name=mock_categories[1].name,
        description="采用玻化微珠为骨料的新型保温砂浆，强度高，吸水率低",
        price=120.0,
        unit="元/袋",
        is_active=True,
        is_featured=False,
        sort_order=2,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    ),
    Product(
        id=str(uuid.uuid4()),
        name="陶粒混凝土",
        slug="ceramsite-concrete-product",
        category_id=mock_categories[2].id,
        category_name=mock_categories[2].name,
        description="优质陶粒为骨料的混凝土产品，轻质高强，保温隔热性能优越",
        price=290.0,
        unit="元/立方米",
        is_active=True,
        is_featured=False,
        sort_order=1,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    ),
]

mock_cases = [
    CaseStudy(
        id=str(uuid.uuid4()),
        project_name="某商业广场保温工程",
        slug="commercial-plaza-insulation",
        location="上海市浦东新区",
        description="大型商业广场屋面及外墙保温工程，使用轻集料混凝土1200立方米",
        content="该项目位于上海市浦东新区，总建筑面积15万平方米。我们提供了从设计到施工的全程服务，采用LC7.5轻集料混凝土作为屋面保温材料，陶粒混凝土作为室内垫层。项目自2023年3月开工，历时6个月完成，获得了业主的高度评价。",
        cover_image="https://images.unsplash.com/photo-1541829070-731301338e86?w=800&h=400&fit=crop",
        construction_area="150000平方米",
        project_date="2023-03",
        status="published",
        is_active=True,
        sort_order=1,
        view_count=1258,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    ),
    CaseStudy(
        id=str(uuid.uuid4()),
        project_name="某住宅小区节能改造",
        slug="residential-community-renovation",
        location="北京市朝阳区",
        description="老旧小区节能改造项目，采用保温砂浆进行外墙保温",
        content="该项目是北京市朝阳区重点节能改造工程，涉及28栋老旧住宅楼。我们采用膨胀珍珠岩保温砂浆对外墙进行了全面保温处理，显著改善了居民的居住舒适度，降低了冬季采暖能耗。",
        cover_image="https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=800&h=400&fit=crop",
        construction_area="85000平方米",
        project_date="2023-06",
        status="published",
        is_active=True,
        sort_order=2,
        view_count=876,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    ),
    CaseStudy(
        id=str(uuid.uuid4()),
        project_name="某工业园区厂房建设",
        slug="industrial-park-construction",
        location="江苏省苏州市",
        description="工业园区新建厂房项目，大量使用陶粒混凝土",
        content="该工业园区位于苏州工业园区，总占地面积200亩。新建的12栋标准厂房全部采用陶粒混凝土作为地面材料，既减轻了建筑荷载，又提供了良好的保温隔热性能。",
        cover_image="https://images.unsplash.com/photo-1487958449943-2429e8be8625?w=800&h=400&fit=crop",
        construction_area="120000平方米",
        project_date="2023-09",
        status="published",
        is_active=True,
        sort_order=3,
        view_count=654,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    ),
]

mock_news = [
    News(
        id=str(uuid.uuid4()),
        title="公司荣获2023年度建材行业创新奖",
        slug="company-wins-innovation-award-2023",
        summary="我公司研发的新型轻集料混凝土产品在2023年度建材行业评选中荣获创新奖",
        content="在刚刚结束的2023年度中国建材行业创新发展大会上，我公司自主研发的'高强低密轻集料混凝土'荣获技术创新奖。该产品相比传统产品，密度降低15%，强度提高20%，市场反响热烈。",
        cover_image="https://images.unsplash.com/photo-1552664730-d307ca884978?w=800&h=400&fit=crop",
        category="company",
        published_at=datetime.now(),
        is_active=True,
        sort_order=1,
        view_count=2341,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    ),
    News(
        id=str(uuid.uuid4()),
        title="轻集料混凝土在装配式建筑中的应用前景",
        slug="lightweight-concrete-prefabrication-application",
        summary="专家分析轻集料混凝土在装配式建筑领域的广阔应用前景",
        content="随着装配式建筑的快速发展，轻集料混凝土因其轻质、高强、保温等优点，在装配式建筑构件中得到了越来越广泛的应用。预计到2025年，相关市场规模将突破500亿元。",
        cover_image="https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=800&h=400&fit=crop",
        category="industry",
        published_at=datetime.now(),
        is_active=True,
        sort_order=2,
        view_count=1856,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    ),
    News(
        id=str(uuid.uuid4()),
        title="我公司与知名地产商达成战略合作",
        slug="strategic-partnership-real-estate",
        summary="我公司与国内TOP10地产商签订年度战略合作协议",
        content="经过多轮洽谈，我公司与国内知名地产商正式签署年度战略合作协议。根据协议，我公司将为其全国范围内的项目供应轻集料混凝土、保温砂浆等产品，预计年度采购额超过2亿元。",
        cover_image="https://images.unsplash.com/photo-1552581234-26160f608093?w=800&h=400&fit=crop",
        category="company",
        published_at=datetime.now(),
        is_active=True,
        sort_order=3,
        view_count=1567,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    ),
    News(
        id=str(uuid.uuid4()),
        title="新型保温砂浆产品正式上市",
        slug="new-insulation-mortar-launch",
        summary="我公司最新研发的纳米改性保温砂浆正式上市销售",
        content="经过两年研发，我公司新一代纳米改性保温砂浆产品正式上市。该产品添加了纳米气凝胶颗粒，导热系数降低30%，同时保持了良好的施工性能和经济性。",
        cover_image="https://images.unsplash.com/photo-1518709766631-a6a7f45921c3?w=800&h=400&fit=crop",
        category="product",
        published_at=datetime.now(),
        is_active=True,
        sort_order=4,
        view_count=1234,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    ),
]

mock_inquiries = []


# API端点
@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "message": "API is running"}


# 产品相关API
@app.get("/api/v1/products", response_model=List[Product])
async def get_products(
        category_id: Optional[str] = None,
        featured: Optional[bool] = None,
        limit: Optional[int] = None):
    result = [p for p in mock_products if p.is_active]
    if category_id:
        result = [p for p in result if p.category_id == category_id]
    if featured is not None:
        result = [p for p in result if p.is_featured == featured]
    if limit:
        result = result[:limit]
    return result


@app.get("/api/v1/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    for product in mock_products:
        if product.id == product_id and product.is_active:
            return product
    raise HTTPException(status_code=404, detail="Product not found")


@app.get("/api/v1/products/slug/{slug}", response_model=Product)
async def get_product_by_slug(slug: str):
    for product in mock_products:
        if product.slug == slug and product.is_active:
            return product
    raise HTTPException(status_code=404, detail="Product not found")


# 分类相关API
@app.get("/api/v1/categories", response_model=List[Category])
async def get_categories():
    return [c for c in mock_categories if c.is_active]


@app.get("/api/v1/categories/{category_id}", response_model=Category)
async def get_category(category_id: str):
    for category in mock_categories:
        if category.id == category_id and category.is_active:
            return category
    raise HTTPException(status_code=404, detail="Category not found")


@app.get("/api/v1/categories/slug/{slug}", response_model=Category)
async def get_category_by_slug(slug: str):
    for category in mock_categories:
        if category.slug == slug and category.is_active:
            return category
    raise HTTPException(status_code=404, detail="Category not found")


# 案例相关API
@app.get("/api/v1/cases", response_model=List[CaseStudy])
async def get_cases(limit: Optional[int] = None):
    result = [c for c in mock_cases if c.is_active and c.status == "published"]
    if limit:
        result = result[:limit]
    return result


@app.get("/api/v1/cases/{case_id}", response_model=CaseStudy)
async def get_case(case_id: str):
    for case in mock_cases:
        if case.id == case_id and case.is_active and case.status == "published":
            return case
    raise HTTPException(status_code=404, detail="Case not found")


@app.get("/api/v1/cases/slug/{slug}", response_model=CaseStudy)
async def get_case_by_slug(slug: str):
    for case in mock_cases:
        if case.slug == slug and case.is_active and case.status == "published":
            return case
    raise HTTPException(status_code=404, detail="Case not found")


# 新闻相关API
@app.get("/api/v1/news", response_model=List[News])
async def get_news(
        category: Optional[str] = None,
        limit: Optional[int] = None):
    result = [n for n in mock_news if n.is_active]
    if category:
        result = [n for n in result if n.category == category]
    if limit:
        result = result[:limit]
    return result


@app.get("/api/v1/news/{news_id}", response_model=News)
async def get_news_item(news_id: str):
    for news in mock_news:
        if news.id == news_id and news.is_active:
            return news
    raise HTTPException(status_code=404, detail="News not found")


@app.get("/api/v1/news/slug/{slug}", response_model=News)
async def get_news_by_slug(slug: str):
    for news in mock_news:
        if news.slug == slug and news.is_active:
            return news
    raise HTTPException(status_code=404, detail="News not found")


# 询盘相关API
class InquiryCreate(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    company: Optional[str] = None
    product_id: Optional[str] = None
    message: Optional[str] = None


@app.post("/api/v1/inquiries")
async def create_inquiry(data: InquiryCreate):
    inquiry = Inquiry(
        id=str(uuid.uuid4()),
        name=data.name,
        phone=data.phone,
        email=data.email,
        company=data.company,
        product_id=data.product_id,
        message=data.message,
        status="pending",
        created_at=datetime.now(),
    )
    mock_inquiries.append(inquiry)
    return {
        "success": True,
        "message": "Inquiry submitted successfully",
        "inquiry_id": inquiry.id}


# 首页数据聚合API
@app.get("/api/v1/home")
async def get_home_data():
    return {
        "featured_products": [p for p in mock_products if p.is_featured and p.is_active][:4],
        "latest_cases": mock_cases[:3],
        "latest_news": mock_news[:3],
        "categories": [c for c in mock_categories if c.is_active],
    }


# 飞书Webhook端点
@app.post("/api/v1/feishu/webhook")
async def feishu_webhook(request: Request):
    try:
        body = await request.json()
        challenge = body.get("challenge", "")
        if challenge:
            return {"challenge": challenge}
        return {"code": 0, "message": "success"}
    except Exception as e:
        logger.info('Webhook error: {e}', e)
        return {"code": -1, "message": str(e)}


# 启动服务器
if __name__ == "__main__":
    import uvicorn

    logger.info('🚀 启动优丁建材API服务...')
    logger.info('📍 API地址: http://127.0.0.1:20000')
    logger.info('📚 文档地址: http://127.0.0.1:20000/docs')
    uvicorn.run(app, host="127.0.0.1", port=20000)
