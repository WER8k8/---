from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.cache_decorator import cache_response
from app.core.database import get_db
from app.core.response import success_response
from app.core.security import require_admin
from app.models.case_study import CaseStudy
from app.models.content import ContentPage
from app.models.inquiry import Inquiry
from app.models.product import Product

router = APIRouter()


@router.get("/dashboard")
@cache_response(expire=300, prefix="analytics")
def get_analytics_dashboard(
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """get_analytics_dashboard。

    参数说明：
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    total_inquiries = db.query(
        func.count(
            Inquiry.id)).filter(
        Inquiry.is_active).scalar() or 0
    pending_inquiries = (
        db.query(
            func.count(
                Inquiry.id)).filter(
            Inquiry.is_active,
            Inquiry.status == "pending").scalar() or 0)
    contacted_inquiries = (
        db.query(
            func.count(
                Inquiry.id)).filter(
            Inquiry.is_active,
            Inquiry.status == "contacted").scalar() or 0)

    hot_products = (
        db.query(Product).filter(
            Product.is_active).order_by(
            Product.view_count.desc()).limit(10).all())
    hot_cases = (
        db.query(CaseStudy).filter(
            CaseStudy.is_active).order_by(
            CaseStudy.view_count.desc()).limit(10).all())

    total_products = db.query(
        func.count(
            Product.id)).filter(
        Product.is_active).scalar() or 0
    total_cases = db.query(
        func.count(
            CaseStudy.id)).filter(
        CaseStudy.is_active).scalar() or 0
    total_pages = db.query(
        func.count(
            ContentPage.id)).filter(
        ContentPage.is_active).scalar() or 0

    return success_response(data={
        "inquiries": {
            "total": total_inquiries,
            "pending": pending_inquiries,
            "contacted": contacted_inquiries,
        },
        "content": {
            "total_products": total_products,
            "total_cases": total_cases,
            "total_pages": total_pages,
        },
        "hot_products": [
            {"id": str(p.id), "name": p.name, "view_count": p.view_count, "slug": p.slug} for p in hot_products
        ],
        "hot_cases": [
            {"id": str(c.id), "name": c.project_name, "view_count": c.view_count, "slug": c.slug} for c in hot_cases
        ],
    })
