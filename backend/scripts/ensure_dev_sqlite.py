#!/usr/bin/env python3
"""开发 SQLite：补齐 users 缺列 + 确保三套演示账号可登录（超管/租户/代理）。"""

from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


import base64
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("JWT_SECRET_KEY", "ensure-dev-" + "x" * 32)
os.environ.setdefault("SECRET_KEY", os.environ["JWT_SECRET_KEY"])

import app.models  # noqa: F401

from sqlalchemy import inspect, text

from app.core import database as db_mod
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.tenant import Tenant, TenantPlan, UserTenant
from app.models.user import User

from app.core.sqlite_paths import resolve_sqlite_database_url
from app.services.site_ai_service import build_template_site_content
from app.services.site_content_array_i18n import default_product_items_en, default_product_items_zh
from app.services.site_content_i18n_service import ensure_site_content_i18n

_db_url = resolve_sqlite_database_url(
    os.environ.get("DATABASE_URL", "sqlite:///./youding_dev.db")
)
settings.DATABASE_URL = _db_url
os.environ["DATABASE_URL"] = _db_url
db_mod.rebind_engine(_db_url)
engine = db_mod.engine

DEV_ACCOUNTS_PATH = REPO_ROOT / ".project" / "dev-login-accounts.json"

# 最小合法 JPEG（占位，dev 产品图）
_DEV_PLACEHOLDER_JPEG = base64.b64decode(
    "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRof"
    "Hh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwh"
    "MjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAAB"
    "AAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA"
    "/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEA"
    "PwCdABmX/9k="
)
_DEV_PRODUCT_IMAGES = (
    "product-standard.jpg",
    "product-enhanced.jpg",
    "product-oem.jpg",
)

DEFAULT_DEV_ACCOUNTS = [
    {"username": "admin", "password": "admin123", "role": "super_admin", "label": "超管"},
    {"username": "tenant", "password": "tenant123", "role": "tenant_admin", "label": "租户"},
    {"username": "agent", "password": "agent123", "role": "l3", "label": "代理"},
]


def _load_dev_accounts() -> list[dict]:
    if not DEV_ACCOUNTS_PATH.is_file():
        return DEFAULT_DEV_ACCOUNTS
    data = json.loads(DEV_ACCOUNTS_PATH.read_text(encoding="utf-8"))
    return list(data.get("accounts") or DEFAULT_DEV_ACCOUNTS)


def _patch_users_columns() -> list[str]:
    applied: list[str] = []
    insp = inspect(engine)
    if "users" not in insp.get_table_names():
        db_mod.Base.metadata.create_all(bind=engine, tables=[User.__table__])
        return ["create users table"]
    cols = {c["name"] for c in insp.get_columns("users")}
    patches = {
        "is_default_password": "INTEGER NOT NULL DEFAULT 1",
        "display_name": "VARCHAR(100)",
        "role_id": "VARCHAR(36)",
    }
    with engine.begin() as conn:
        for name, ddl in patches.items():
            if name not in cols:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {name} {ddl}"))
                applied.append(name)
    return applied


def _ensure_role_user(username: str, password: str, role: str, label: str) -> str:
    db = db_mod.SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        now = datetime.now(timezone.utc)
        email = f"{username}@dev.local"
        if user:
            user.hashed_password = get_password_hash(password)
            user.role = role
            user.is_active = True
            if hasattr(user, "is_default_password"):
                user.is_default_password = True
            db.commit()
            return f"updated {username}"
        user = User(
            id=str(uuid.uuid4()),
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            display_name=label,
            role=role,
            is_active=True,
            is_default_password=True,
            created_at=now,
            updated_at=now,
        )
        db.add(user)
        db.commit()
        return f"created {username}"
    finally:
        db.close()


def _ensure_dev_accounts() -> list[str]:
    results: list[str] = []
    for acc in _load_dev_accounts():
        results.append(
            _ensure_role_user(
                str(acc["username"]),
                str(acc.get("password") or os.getenv("SEED_ADMIN_PASSWORD", "admin123")),
                str(acc["role"]),
                str(acc.get("label") or acc["username"]),
            )
        )
    return results


def _ensure_dev_tenant(admin_id: str) -> str:
    db_mod.Base.metadata.create_all(
        bind=engine,
        tables=[
            TenantPlan.__table__,
            Tenant.__table__,
            UserTenant.__table__,
        ],
    )
    db = db_mod.SessionLocal()
    try:
        plan = db.query(TenantPlan).filter(TenantPlan.code == "dev").first()
        if not plan:
            plan = TenantPlan(
                name="开发版",
                code="dev",
                price_monthly=0,
                price_yearly=0,
                features='["seo","publish","ubrain"]',
                is_active=True,
            )
            db.add(plan)
            db.flush()
        tenant = db.query(Tenant).filter(Tenant.domain == "dev.local").first()
        if not tenant:
            tenant = Tenant(
                id=str(uuid.uuid4()),
                name="开发租户",
                domain="dev.local",
                plan_id=plan.id,
                status="active",
                is_active=True,
            )
            db.add(tenant)
            db.flush()
        _ensure_dev_local_site_content(tenant)
        _ensure_dev_geo_content_masters(db, tenant_id=str(tenant.id), admin_id=admin_id)
        link = (
            db.query(UserTenant)
            .filter(UserTenant.user_id == admin_id, UserTenant.tenant_id == tenant.id)
            .first()
        )
        if not link:
            db.add(
                UserTenant(
                    user_id=admin_id,
                    tenant_id=tenant.id,
                    role="admin",
                    is_active=True,
                )
            )
        for username, link_role in (
            ("editor", "editor"),
            ("tenant", "tenant_admin"),
            ("tenant_demo", "tenant_admin"),
        ):
            user = db.query(User).filter(User.username == username).first()
            if not user:
                continue
            existing = (
                db.query(UserTenant)
                .filter(UserTenant.user_id == user.id, UserTenant.tenant_id == tenant.id)
                .first()
            )
            if not existing:
                db.add(
                    UserTenant(
                        user_id=user.id,
                        tenant_id=tenant.id,
                        role=link_role,
                        is_active=True,
                    )
                )
        db.commit()
        return str(tenant.id)
    finally:
        db.close()


def _patch_dev_local_brand_bilingual(site: dict) -> None:
    """英文基字段 + zh i18n，语言切换时品牌/Hero/产品可跟随。"""
    en_name = "Development Tenant"
    zh_name = "开发租户"
    product = "Export Products"
    short = product[:20]
    en_desc = (
        f"{en_name} specializes in {product} R&D, manufacturing and export. "
        "Modern production facilities; products shipped to Europe, the Middle East "
        "and Southeast Asia; OEM/ODM and sample orders supported."
    )
    zh_desc = (
        f"{zh_name} 专注 {product} 研发、生产与出口。"
        "拥有现代化生产基地，产品远销欧美、中东、东南亚等市场，支持 OEM/ODM 与样品打样。"
    )

    site_brand = site.get("brand")
    if not isinstance(site_brand, dict):
        site_brand = {}
        site["brand"] = site_brand

    current_name = str(site_brand.get("name") or "").strip()
    if not current_name or current_name == zh_name:
        site_brand["name"] = en_name

    i18n = site_brand.setdefault("i18n", {})
    zh_brand = i18n.setdefault("zh", {})
    if isinstance(zh_brand, dict):
        zh_brand["name"] = zh_name
        zh_brand.setdefault("tagline", "中国出口产品制造商 · OEM/ODM 定制")

    pages = site.setdefault("pages", {})
    if not isinstance(pages, dict):
        pages = {}
        site["pages"] = pages
    home = pages.get("home")
    if not isinstance(home, dict):
        home = {}
        pages["home"] = home

    title = str(home.get("title") or "").strip()
    if not title or zh_name in title or title == zh_name:
        home["title"] = f"{product} Manufacturer, Supplier & Factory"

    desc = str(home.get("description") or "").strip()
    if not desc or "专注" in desc or "研发" in desc:
        home["description"] = en_desc
    home.setdefault("sectionTitle", "Why Choose Us")

    home_i18n = home.setdefault("i18n", {})
    zh_home = home_i18n.setdefault("zh", {})
    if isinstance(zh_home, dict):
        zh_home.setdefault("title", f"{product} 生产厂家 · 供应商")
        zh_home["description"] = zh_desc
        zh_home.setdefault(
            "seoDescription",
            f"{zh_name}专注{product}研发制造与出口，OEM/ODM 定制，欢迎询盘合作。",
        )
        zh_home.setdefault(
            "seoKeywords",
            f"{product},建材出口,制造商,供应商,OEM",
        )

    ru_home = home_i18n.setdefault("ru", {})
    if isinstance(ru_home, dict):
        ru_home.setdefault("title", f"Производитель {product} · поставщик")
        ru_home.setdefault(
            "seoDescription",
            f"{en_name} — производитель {product} из Китая. OEM/ODM, экспорт.",
        )
        ru_home.setdefault(
            "seoKeywords",
            f"{product}, теплоизоляция, минеральная вата, производитель, завод",
        )

    home.setdefault(
        "seoDescription",
        f"{en_name} — {product} manufacturer and exporter from China. OEM/ODM welcome.",
    )
    home.setdefault(
        "seoKeywords",
        f"{product},manufacturer,supplier,factory,export,OEM",
    )
    site.setdefault("seo", {"primaryMarket": "export"})

    products = pages.get("products")
    if not isinstance(products, dict):
        products = {}
        pages["products"] = products
    cat = short
    categories = home.get("categories")
    if isinstance(categories, list) and categories:
        first = categories[0]
        if isinstance(first, dict) and first.get("name"):
            cat = str(first["name"])
    products["productItems"] = default_product_items_en(product, short, cat)
    _dev_images = (
        "/uploads/dev/product-standard.jpg",
        "/uploads/dev/product-enhanced.jpg",
        "/uploads/dev/product-oem.jpg",
    )
    for idx, item in enumerate(products["productItems"]):
        if isinstance(item, dict) and not str(item.get("image") or "").strip():
            item["image"] = _dev_images[idx % len(_dev_images)]
    prod_i18n = products.setdefault("i18n", {})
    zh_prod = prod_i18n.setdefault("zh", {})
    if isinstance(zh_prod, dict):
        zh_prod["productItems"] = default_product_items_zh(product, short, cat)
        for idx, item in enumerate(zh_prod["productItems"]):
            if isinstance(item, dict) and not str(item.get("image") or "").strip():
                item["image"] = _dev_images[idx % len(_dev_images)]

    _ensure_dev_local_faq(home, product=product, company=en_name)


def _ensure_dev_local_faq(home: dict, *, product: str, company: str) -> None:
    """dev.local 补齐 ≥8 条 FAQ，提升 llms.txt / GEO 内容就绪度。"""
    existing = home.get("faq") or home.get("faqs")
    if isinstance(existing, list) and len(existing) >= 8:
        return
    short = product[:24]
    home["faq"] = [
        {
            "question": f"What is {short}?",
            "answer": (
                f"{short} is a construction-grade export product manufactured by {company}. "
                "We supply distributors and EPC contractors with OEM/ODM options."
            ),
        },
        {
            "question": f"What are the main applications of {short}?",
            "answer": (
                "Typical applications include industrial insulation, building envelopes, "
                "HVAC duct lining, and energy-efficiency retrofits for commercial projects."
            ),
        },
        {
            "question": "Do you support OEM/ODM customization?",
            "answer": (
                "Yes. We provide label customization, packaging design, and specification "
                "adjustments for bulk orders. Send your drawing or target spec for a quote."
            ),
        },
        {
            "question": "What is the typical MOQ and lead time?",
            "answer": (
                "MOQ varies by SKU; sample orders are welcome. Standard production lead time "
                "is 15–25 days after deposit, subject to season and container schedule."
            ),
        },
        {
            "question": "Which export markets do you serve?",
            "answer": (
                f"{company} exports to Europe, the Middle East, Southeast Asia and Latin America "
                "with full export documentation and third-party inspection support."
            ),
        },
        {
            "question": "Can you provide test reports and certificates?",
            "answer": (
                "We supply factory test reports, ISO quality certificates, and CE-related "
                "documentation on request for tender and compliance review."
            ),
        },
        {
            "question": "How do I request a quotation?",
            "answer": (
                "Submit product name, quantity, destination port and required spec on the "
                "contact page. Our export team replies within one business day."
            ),
        },
        {
            "question": "Do you offer factory visit or video audit?",
            "answer": (
                "Yes. We welcome buyers to visit our production facility or join a live "
                "video walkthrough before placing bulk orders."
            ),
        },
    ]


def _ensure_dev_geo_content_masters(db, *, tenant_id: str, admin_id: str) -> int:
    """dev.local 补齐已发布内容母版，提升 GEO 内容就绪度（开发种子，非假排名）。"""
    from app.models.content_master import ContentMaster

    db_mod.Base.metadata.create_all(bind=engine, tables=[ContentMaster.__table__])
    published = (
        db.query(ContentMaster)
        .filter(ContentMaster.tenant_id == tenant_id, ContentMaster.status.in_(("published", "scheduled")))
        .count()
    )
    target = 4
    if published >= target:
        return 0
    titles = [
        "Export Products OEM Guide for Distributors",
        "Thermal Insulation Spec Sheet — Factory Direct",
        "Quality Control and Third-Party Inspection FAQ",
        "Case Study: Middle East EPC Bulk Supply",
    ]
    added = 0
    for title in titles[published:target]:
        db.add(
            ContentMaster(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                title=title,
                body=(
                    f"{title}. Verified factory specifications for export buyers. "
                    "Contact sales for MOQ, lead time and OEM options."
                ),
                content_type="article",
                status="published",
                created_by=admin_id or None,
                show_on_hub=True,
            )
        )
        added += 1
    return added


def _ensure_dev_local_site_content(tenant: Tenant) -> None:
    """dev.local 注入/修补带 i18n 的 L-Pro 站点内容，语言切换时 Hero/品牌名可跟随。"""
    try:
        settings = json.loads(tenant.settings or "{}") if tenant.settings else {}
    except json.JSONDecodeError:
        settings = {}
    brand = settings.get("brand") if isinstance(settings.get("brand"), dict) else {}
    raw_site = brand.get("site_content")

    if isinstance(raw_site, dict) and raw_site:
        site = raw_site
    else:
        site = build_template_site_content("Export Products", "Development Tenant")

    _patch_dev_local_brand_bilingual(site)
    site, _ = ensure_site_content_i18n(
        site,
        product_name="Export Products",
        company_name="Development Tenant",
    )
    _patch_dev_local_brand_bilingual(site)

    brand["company_name"] = "开发租户"
    brand["site_title"] = "开发租户"
    brand["site_content"] = site
    settings["brand"] = brand
    tenant.settings = json.dumps(settings, ensure_ascii=False)
    tenant.name = "开发租户"


def _ensure_inquiry_columns() -> list[str]:
    from app.db.session import _ensure_inquiry_attribution_columns, init_db

    init_db()
    _ensure_inquiry_attribution_columns()
    insp = inspect(engine)
    if "inquiries" not in insp.get_table_names():
        return []
    cols = {c["name"] for c in insp.get_columns("inquiries")}
    applied: list[str] = []
    extra = {
        "source_channel": "VARCHAR(64)",
        "phone": "VARCHAR(32)",
    }
    with engine.begin() as conn:
        for name, ddl in extra.items():
            if name not in cols:
                conn.execute(text(f"ALTER TABLE inquiries ADD COLUMN {name} {ddl}"))
                applied.append(name)
    return applied


def _ensure_dev_product_images() -> list[str]:
    from app.core.uploads_path import ensure_uploads_dir

    dev_dir = ensure_uploads_dir() / "dev"
    dev_dir.mkdir(parents=True, exist_ok=True)
    applied: list[str] = []
    for name in _DEV_PRODUCT_IMAGES:
        target = dev_dir / name
        if not target.is_file() or target.stat().st_size < 64:
            target.write_bytes(_DEV_PLACEHOLDER_JPEG)
            applied.append(name)
    return applied


def main() -> int:
    patches = _patch_users_columns()
    inquiry_patches = _ensure_inquiry_columns()
    image_msgs = _ensure_dev_product_images()
    account_msgs = _ensure_dev_accounts()
    db = db_mod.SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        admin_id = str(admin.id) if admin else ""
    finally:
        db.close()
    tenant_id = _ensure_dev_tenant(admin_id) if admin_id else ""
    logger.info(
        f"OK: patches={patches}, inquiries={inquiry_patches}, "
        f"images={image_msgs}, accounts={account_msgs}, tenant_id={tenant_id}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
