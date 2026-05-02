from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.security import require_admin
from app.models.product import Product
from app.models.case_study import CaseStudy, CaseImage
from app.models.inquiry import Inquiry
from app.models.content import ContentPage

router = APIRouter()


@router.get("/dashboard")
def get_analytics_dashboard(db: Session = Depends(get_db), admin = Depends(require_admin)):
    total_inquiries = db.query(func.count(Inquiry.id)).filter(Inquiry.is_active == True).scalar() or 0
    pending_inquiries = db.query(func.count(Inquiry.id)).filter(Inquiry.is_active == True, Inquiry.status == "pending").scalar() or 0
    contacted_inquiries = db.query(func.count(Inquiry.id)).filter(Inquiry.is_active == True, Inquiry.status == "contacted").scalar() or 0

    hot_products = db.query(Product).filter(Product.is_active == True).order_by(Product.view_count.desc()).limit(10).all()
    hot_cases = db.query(CaseStudy).filter(CaseStudy.is_active == True).order_by(CaseStudy.view_count.desc()).limit(10).all()

    total_products = db.query(func.count(Product.id)).filter(Product.is_active == True).scalar() or 0
    total_cases = db.query(func.count(CaseStudy.id)).filter(CaseStudy.is_active == True).scalar() or 0
    total_pages = db.query(func.count(ContentPage.id)).filter(ContentPage.is_active == True).scalar() or 0

    return {
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
            {"id": str(p.id), "name": p.name, "view_count": p.view_count, "slug": p.slug}
            for p in hot_products
        ],
        "hot_cases": [
            {"id": str(c.id), "name": c.project_name, "view_count": c.view_count, "slug": c.slug}
            for c in hot_cases
        ],
    }
