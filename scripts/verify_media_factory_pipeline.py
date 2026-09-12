#!/usr/bin/env python3
"""多媒体工厂 + 开户 + 引流 链路冒烟（隔离 SQLite，无需外部 CDN 密钥）。

用法（仓库根目录）:
  python scripts/verify_media_factory_pipeline.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)

_db_file = BACKEND / "youding_media_verify.db"
if _db_file.exists():
    _db_file.unlink()

os.environ["ENVIRONMENT"] = "development"
os.environ["DATABASE_URL"] = f"sqlite:///{_db_file.as_posix()}"
os.environ["SECRET_KEY"] = "dev-verify-media-factory-secret-32b"
os.environ["JWT_SECRET_KEY"] = "dev-verify-media-factory-jwt-key-32b"
os.environ["REDIS_ENABLED"] = "false"
os.environ["MEDIA_FACTORY_MOCK_RENDER"] = "true"
os.environ["MEDIA_CLOUD_UPLOAD_ENABLED"] = "false"
os.environ["MEDIA_CLOUD_BACKUP"] = "none"
os.environ["PYTHONPATH"] = str(BACKEND)

from app.core.database import SessionLocal, rebind_engine  # noqa: E402
from app.core.security import create_access_token, get_password_hash  # noqa: E402
from app.db.session import init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.content import Platform, PlatformAccount  # noqa: E402
from app.models.media_factory import MediaRenderTask  # noqa: E402
from app.models.tenant import Tenant, TenantPlan, UserTenant  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.platform_catalog import upsert_platforms, all_catalog_rows  # noqa: E402
from app.services.tenant_onboarding_service import (  # noqa: E402
    backfill_tenant_platform_stubs,
    provision_tenant_onboarding,
)
from fastapi.testclient import TestClient  # noqa: E402


def _unwrap(body: dict) -> dict:
    if isinstance(body.get("data"), dict):
        return body["data"]
    return body


def _api_ok(r) -> bool:
    if r.status_code >= 400:
        return False
    body = r.json()
    code = body.get("code")
    return code in (0, None, "0")


def _api_not_found(r) -> bool:
    if r.status_code == 404:
        return True
    body = r.json()
    return body.get("code") == 404


def main() -> int:
    rebind_engine(os.environ["DATABASE_URL"])
    init_db()

    checks: list[tuple[str, bool, str]] = []

    def record(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, ok, detail))
        mark = "PASS" if ok else "FAIL"
        print(f"  [{mark}] {name}" + (f" — {detail}" if detail else ""))

    client = TestClient(app, raise_server_exceptions=False)

    print("==> 1. 公开端点")
    r = client.get("/api/v1/health")
    record("health", r.status_code == 200, str(r.status_code))

    r = client.get("/api/v1/media-factory/guest-session")
    guest = _unwrap(r.json()) if r.status_code == 200 else {}
    record("guest-session", r.status_code == 200 and bool(guest.get("guest_token")))

    r = client.get("/api/v1/tenants/register/catalog")
    catalog = _unwrap(r.json()) if r.status_code == 200 else {}
    record(
        "register-catalog",
        r.status_code == 200 and bool(catalog.get("platforms") or catalog.get("bundled_services")),
    )

    print("==> 2. 租户与 onboarding")
    db = SessionLocal()
    plan = TenantPlan(
        id=str(uuid4()),
        name="媒体验证套餐",
        code=f"mf-{uuid4().hex[:6]}",
        price_monthly=0,
        price_yearly=0,
        features='["ai","video","seo"]',
    )
    tid = str(uuid4())
    domain = f"mf-{uuid4().hex[:6]}"
    tenant = Tenant(
        id=tid,
        name="媒体验证租户",
        domain=domain,
        plan_id=plan.id,
        status="active",
        settings="{}",
        is_active=True,
    )
    uid = str(uuid4())
    uname = f"mf_ta_{uuid4().hex[:8]}"
    user = User(
        id=uid,
        username=uname,
        email=f"{uname}@local.test",
        hashed_password=get_password_hash("VerifyPass123!"),
        role="tenant_admin",
        is_active=True,
    )
    db.add_all([plan, tenant, user, UserTenant(user_id=uid, tenant_id=tid, role="owner", is_active=True)])
    upsert_platforms(db, all_catalog_rows())
    db.flush()
    onboarding = provision_tenant_onboarding(db, tenant, user, plan, platform_names=["微信公众号", "YouTube"])
    db.commit()

    stub_count = (
        db.query(PlatformAccount).filter(PlatformAccount.tenant_id == tid).count()
    )
    record("onboarding-provision", bool(onboarding.get("checklist")) and stub_count >= 2, f"stubs={stub_count}")

    backfill = backfill_tenant_platform_stubs(db, dry_run=True)
    record(
        "backfill-dry-run",
        backfill.get("tenants_scanned", 0) >= 1,
        f"would_create={backfill.get('accounts_created')}",
    )

    token = create_access_token({"sub": uid})
    h = {"Authorization": f"Bearer {token}"}
    db.close()

    print("==> 3. 媒体工厂 API")
    r = client.get("/api/v1/media-factory/", headers=h)
    overview = _unwrap(r.json()) if r.status_code == 200 else {}
    record(
        "media-overview",
        r.status_code == 200 and "rendered_videos" in overview,
        json.dumps(overview, ensure_ascii=False)[:120],
    )

    r = client.get("/api/v1/media-factory/videos", headers=h)
    videos = r.json()
    data = videos.get("data", videos) if isinstance(videos, dict) else videos
    record("media-videos-list", r.status_code == 200 and isinstance(data, list))

    r = client.get("/api/v1/tenants/current", headers=h)
    current = _unwrap(r.json()) if r.status_code == 200 else {}
    record(
        "tenants-current-onboarding",
        r.status_code == 200 and bool(current.get("onboarding")),
    )

    print("==> 4. 渲染任务 + 租户隔离 + 引流")
    db = SessionLocal()
    task_id = str(uuid4())
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(b"\x00\x00\x00\x20ftypmp42")
        tmp_path = tmp.name

    task = MediaRenderTask(
        id=task_id,
        title="冒烟测试视频",
        task_type="video",
        script="镜头1 | 测试画面 | 测试旁白",
        status="done",
        progress=100,
        tenant_id=tid,
        result_path=tmp_path,
        result_url=f"/uploads/media_factory/{task_id}.mp4",
        cloud_upload_status="skipped",
        cloud_r2_url="https://example.com/demo.mp4",
    )
    db.add(task)

    other_tid = str(uuid4())
    other_task_id = str(uuid4())
    db.add(
        MediaRenderTask(
            id=other_task_id,
            title="其他租户",
            task_type="video",
            script="x",
            status="done",
            progress=100,
            tenant_id=other_tid,
            cloud_upload_status="skipped",
        )
    )
    db.commit()
    db.close()

    r = client.get(f"/api/v1/media-factory/tasks/{task_id}", headers=h)
    got = _unwrap(r.json()) if r.status_code == 200 else {}
    record("task-get-own", r.status_code == 200 and got.get("id") == task_id)

    r = client.get(f"/api/v1/media-factory/tasks/{other_task_id}", headers=h)
    iso_body = r.json()
    iso_data = _unwrap(iso_body) if iso_body.get("code") == 0 else {}
    db_chk = SessionLocal()
    u_chk = db_chk.query(User).filter(User.id == uid).first()
    from app.services.media_factory_service import get_render_task_for_user

    svc_leak = get_render_task_for_user(db_chk, other_task_id, u_chk) if u_chk else None
    db_chk.close()
    iso_ok = svc_leak is None and (iso_body.get("code") == 404 or not iso_data.get("id"))
    record(
        "task-tenant-isolation",
        iso_ok,
        f"http={r.status_code} api_code={iso_body.get('code')} svc_leak={svc_leak is not None}",
    )

    r = client.get(f"/api/v1/media-factory/tasks/{task_id}/seo-bundle", headers=h)
    bundle = _unwrap(r.json()) if r.status_code == 200 else {}
    record("seo-bundle", r.status_code == 200 and bool(bundle.get("meta_title") or bundle.get("title")))

    r = client.post(
        f"/api/v1/media-factory/tasks/{task_id}/publish-traffic",
        headers=h,
        json={"platform_ids": []},
    )
    traffic = _unwrap(r.json()) if r.status_code == 200 else {}
    record(
        "publish-traffic",
        r.status_code == 200,
        str(traffic.get("tenant_landing_url") or traffic.get("results") or r.json().get("message", ""))[:100],
    )

    print("==> 5. SEO 发布服务")
    try:
        from app.services.publish_dispatch_service import SeoPublishService

        svc = SeoPublishService(SessionLocal())
        record("seo-publish-service", hasattr(svc, "_dispatch_to_platform"))
    except Exception as exc:
        record("seo-publish-service", False, str(exc))

    try:
        from app.services.media_lenslink_service import lenslink_configured

        record("lenslink-module", True, f"configured={lenslink_configured()}")
    except Exception as exc:
        record("lenslink-module", False, str(exc))

    failed = [c for c in checks if not c[1]]
    print("\n==> 汇总")
    print(f"  通过 {len(checks) - len(failed)} / {len(checks)}")
    if failed:
        for name, _, detail in failed:
            print(f"  X {name}: {detail}")
        return 1
    print("  全部通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
