#!/usr/bin/env python3
"""本地开发：幂等补齐 dev.local 租户演示数据（不新建第二租户、不造假页面）。"""

from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)
os.environ.setdefault("DATABASE_URL", "sqlite:///./youding_dev.db")
os.environ.setdefault("ENVIRONMENT", "development")

DEMO_USERNAME = "tenant"
DEMO_EMAIL = "tenant@dev.local"
DEMO_PASSWORD = "tenant123"
DEV_TENANT_DOMAIN = "dev.local"
ADMIN_BASE = os.environ.get("FRONTEND_URL", "http://127.0.0.1:5173").rstrip("/")

from app.core.security import get_password_hash  # noqa: E402
from app.db.session import SessionLocal, init_db  # noqa: E402
from app.models.tenant import Tenant, TenantPlan, TenantSubscription, UserTenant  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.inquiry import Inquiry  # noqa: E402
from app.services.platform_catalog import all_catalog_rows, upsert_platforms  # noqa: E402
from app.services.tenant_onboarding_service import provision_tenant_onboarding  # noqa: E402


def _ensure_tenant_user(db) -> tuple[User, bool]:
    user = db.query(User).filter(User.username == DEMO_USERNAME).first()
    if not user:
        user = db.query(User).filter(User.email == DEMO_EMAIL).first()
    created = False
    now = datetime.now(timezone.utc)
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            username=DEMO_USERNAME,
            email=DEMO_EMAIL,
            display_name="演示管理员",
            hashed_password=get_password_hash(DEMO_PASSWORD),
            role="tenant_admin",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        db.add(user)
        db.flush()
        created = True
    return user, created


def _resolve_dev_tenant(db) -> Tenant | None:
    return db.query(Tenant).filter(Tenant.domain == DEV_TENANT_DOMAIN).first()


def _ensure_demo_inquiry(db, tenant: Tenant) -> bool:
    existing = (
        db.query(Inquiry)
        .filter(
            Inquiry.tenant_id == str(tenant.id),
            Inquiry.email == "buyer.demo@example.com",
        )
        .first()
    )
    if existing:
        return False
    db.add(
        Inquiry(
            id=str(uuid.uuid4()),
            tenant_id=str(tenant.id),
            name="John Smith",
            phone="+971-555-0100",
            email="buyer.demo@example.com",
            product="Rock wool insulation boards",
            message=(
                "Hello, we are a building materials distributor in Dubai. "
                "We need rock wool insulation boards for HVAC projects. "
                "Please send catalog, MOQ, FOB Tianjin price and fire rating certificates."
            ),
            status="pending",
            source_channel="dev_seed",
            is_active=True,
        )
    )
    return True


def main() -> int:
    init_db()
    db = SessionLocal()
    try:
        upsert_platforms(db, all_catalog_rows())
        db.commit()

        user, created_user = _ensure_tenant_user(db)
        tenant = _resolve_dev_tenant(db)
        if not tenant:
            print(
                "ERROR: 未找到 dev.local 租户，请先运行 backend/scripts/ensure_dev_sqlite.py"
            )
            return 1

        plan = db.query(TenantPlan).filter(TenantPlan.id == tenant.plan_id).first()
        if not plan:
            plan = db.query(TenantPlan).filter(TenantPlan.code == "dev").first()
        if not plan:
            print("ERROR: 套餐不存在，请先 init_db / ensure_dev_sqlite")
            return 1

        link = (
            db.query(UserTenant)
            .filter(UserTenant.user_id == user.id, UserTenant.tenant_id == tenant.id)
            .first()
        )
        if not link:
            db.add(
                UserTenant(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    tenant_id=tenant.id,
                    role="tenant_admin",
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                )
            )
            db.flush()

        sub = (
            db.query(TenantSubscription)
            .filter(TenantSubscription.tenant_id == tenant.id, TenantSubscription.status == "active")
            .first()
        )
        if not sub:
            now = datetime.now(timezone.utc)
            db.add(
                TenantSubscription(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant.id,
                    plan_id=plan.id,
                    billing_cycle="monthly",
                    amount=plan.price_monthly,
                    status="active",
                    started_at=now,
                    created_at=now,
                )
            )
            db.flush()

        onboarding = provision_tenant_onboarding(
            db,
            tenant,
            user,
            plan,
            platform_names=["微信公众号", "抖音", "YouTube", "哔哩哔哩"],
        )
        seeded_inquiry = _ensure_demo_inquiry(db, tenant)
        db.commit()

        print("OK dev tenant demo ready")
        print(f"  用户名: {DEMO_USERNAME}")
        print(f"  邮箱:   {DEMO_EMAIL}")
        print(f"  密码:   {DEMO_PASSWORD}")
        print(f"  租户:   {tenant.name} ({tenant.domain})")
        print(f"  用户:   {'新建' if created_user else '已存在'}")
        print(f"  平台位: {len(onboarding.get('platforms', []))}")
        print(f"  演示询盘: {'已补齐 John Smith 英文询盘' if seeded_inquiry else '已存在'}")
        print("")
        print("  唯一登录: {}/login  （禁止新建 /client/login 假页，旧链仅 302）".format(ADMIN_BASE))
        print("  租户首页: /client/today  -> views/client/today-three.vue")
        print("  租户工作台: /client/dashboard  -> views/client/dashboard.vue")
        print("  SEO 绑定: /client/seo-publish  -> views/seo-matrix/publish.vue")
        print("  文章转视频: /client/article-to-video  -> views/admin/ai-center/article-to-video.vue")
        print("  询盘语言桥: /client/inquiries  -> 展开行「中文摘要 / 英文草稿」")
        print("  租户挂网预览: http://localhost:3000/tenant?__tenant=dev.local&lpro=1")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
