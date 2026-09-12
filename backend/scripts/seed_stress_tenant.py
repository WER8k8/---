"""压测种子：套餐 + 租户 + super_admin/tenant_admin 用户 + user_tenants 绑定。

用法（backend 容器内）：python /app/scripts/seed_stress_tenant.py
幂等：按唯一键（plan.code / tenant.domain / user.username）已存在即跳过。
"""
import logging
import uuid
from datetime import datetime, timedelta, timezone

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("seed")

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.tenant import Tenant, TenantPlan, UserTenant
from app.models.user import User

PLAN_CODE = "pro"
TENANT_DOMAIN = "stress-a.local"
TENANT_NAME = "压测租户A"

USERS = [
    {"username": "admin", "email": "admin@stress-a.local", "password": "Admin123!", "role": "super_admin"},
    {"username": "tenant_demo", "email": "tenant_demo@stress-a.local", "password": "TenantDemo@2026!", "role": "tenant_admin"},
]


def main() -> int:
    db = SessionLocal()
    try:
        plan = db.query(TenantPlan).filter(TenantPlan.code == PLAN_CODE).first()
        if not plan:
            plan = TenantPlan(
                name="专业版", code=PLAN_CODE, price_monthly=99000, price_yearly=999000,
                max_users=20, max_sites=5, max_products=1000, max_ai_quota=100000,
                features='["seo","globalization","international","media_factory","agent"]',
            )
            db.add(plan)
            db.flush()
            log.info("created plan %s", plan.id)
        else:
            log.info("plan exists %s", plan.id)

        tenant = db.query(Tenant).filter(Tenant.domain == TENANT_DOMAIN).first()
        if not tenant:
            tenant = Tenant(
                name=TENANT_NAME, contact_name="压测管理员", contact_email="contact@stress-a.local",
                domain=TENANT_DOMAIN, plan_id=plan.id, status="active",
                subscribed_at=datetime.now(timezone.utc),
                trial_ends_at=datetime.now(timezone.utc) + timedelta(days=3650),
            )
            db.add(tenant)
            db.flush()
            log.info("created tenant %s", tenant.id)
        else:
            log.info("tenant exists %s", tenant.id)

        created = {}
        for u in USERS:
            user = db.query(User).filter(User.username == u["username"]).first()
            if not user:
                user = User(
                    id=str(uuid.uuid4()), username=u["username"], email=u["email"],
                    hashed_password=get_password_hash(u["password"]), role=u["role"], is_active=True,
                    created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
                )
                db.add(user)
                db.flush()
                log.info("created user %s/%s", u["username"], u["role"])
            else:
                log.info("user exists %s", u["username"])
            created[u["username"]] = user

        td = created["tenant_demo"]
        bind = (
            db.query(UserTenant)
            .filter(UserTenant.user_id == td.id, UserTenant.tenant_id == tenant.id)
            .first()
        )
        if not bind:
            db.add(UserTenant(user_id=td.id, tenant_id=tenant.id, role="admin", is_active=True))
            log.info("bound tenant_demo -> tenant %s", tenant.id)
        else:
            log.info("binding exists")

        db.commit()
        log.info("OK tenant_id=%s admin=tenant_demo/TenantDemo@2026! super=admin/Admin123!", tenant.id)
        return 0
    except Exception as exc:
        db.rollback()
        log.error("FAILED: %s", exc)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
