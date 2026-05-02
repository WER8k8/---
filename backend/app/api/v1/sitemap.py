from fastapi import APIRouter
from fastapi.responses import Response
from sqlalchemy import select
from app.core.database import get_db
from app.models.product import Product
from app.models.case_study import CaseStudy
from app.models.content import ContentPage

router = APIRouter()

BASE_URL = "https://www.youding.com"


@router.get("/sitemap.xml")
async def generate_sitemap():
    db = next(get_db())

    products = db.execute(
        select(Product.slug, Product.updated_at).where(Product.is_active == True)
    ).fetchall()

    cases = db.execute(
        select(CaseStudy.slug, CaseStudy.updated_at).where(CaseStudy.is_active == True)
    ).fetchall()

    pages = db.execute(
        select(ContentPage.slug, ContentPage.updated_at).where(ContentPage.is_active == True)
    ).fetchall()

    urls = []
    urls.append(f"  <url><loc>{BASE_URL}/</loc><priority>1.0</priority><changefreq>daily</changefreq></url>")
    urls.append(f"  <url><loc>{BASE_URL}/products</loc><priority>0.9</priority><changefreq>weekly</changefreq></url>")
    urls.append(f"  <url><loc>{BASE_URL}/cases</loc><priority>0.8</priority><changefreq>weekly</changefreq></url>")
    urls.append(f"  <url><loc>{BASE_URL}/about</loc><priority>0.7</priority><changefreq>monthly</changefreq></url>")
    urls.append(f"  <url><loc>{BASE_URL}/contact</loc><priority>0.6</priority><changefreq>monthly</changefreq></url>")

    for p in products:
        lastmod = p.updated_at.strftime("%Y-%m-%d") if p.updated_at else "2026-01-01"
        urls.append(f"  <url><loc>{BASE_URL}/products/{p.slug}</loc><lastmod>{lastmod}</lastmod><priority>0.8</priority><changefreq>weekly</changefreq></url>")

    for c in cases:
        lastmod = c.updated_at.strftime("%Y-%m-%d") if c.updated_at else "2026-01-01"
        urls.append(f"  <url><loc>{BASE_URL}/cases/{c.slug}</loc><lastmod>{lastmod}</lastmod><priority>0.7</priority><changefreq>monthly</changefreq></url>")

    for p in pages:
        lastmod = p.updated_at.strftime("%Y-%m-%d") if p.updated_at else "2026-01-01"
        urls.append(f"  <url><loc>{BASE_URL}/content/{p.slug}</loc><lastmod>{lastmod}</lastmod><priority>0.6</priority><changefreq>monthly</changefreq></url>")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>"""

    return Response(content=xml, media_type="application/xml")
