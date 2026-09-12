#!/usr/bin/env python3
"""B-07: 5+5 试点 — seed 平台、创建母版、发布任务、跑 worker，输出验收 JSON。"""
import json
import logging

logger = logging.getLogger(__name__)

import os
import sys
import uuid
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("JWT_SECRET_KEY", "b7-pilot-" + "x" * 32)

if os.getenv("DEMO_USE_PRODUCTION_DB") != "1":
    demo_db = BACKEND / "data" / "demo_acceptance.db"
    demo_db.parent.mkdir(parents=True, exist_ok=True)
    os.environ["DATABASE_URL"] = f"sqlite:///{demo_db.as_posix()}"

import app.models  # noqa: F401

from app.core.database import Base, SessionLocal, engine
from app.models.content import Platform, PlatformAccount, PublishTask
from app.models.content_master import ContentMaster
from app.models.tenant import Tenant, TenantPlan
from app.workers.publish_worker import run_process_pending_tasks

OUT = ROOT / "docs" / "b7-pilot-acceptance-result.json"


def main() -> int:
    from scripts.seed_platforms_pilot import main as seed_main

    seed_main()
    Base.metadata.create_all(
        bind=engine,
        tables=[
            TenantPlan.__table__,
            Tenant.__table__,
            ContentMaster.__table__,
            PlatformAccount.__table__,
            PublishTask.__table__,
        ],
    )
    db = SessionLocal()
    report = {"task_ids": [], "platforms": 0, "ok": False, "db": os.environ.get("DATABASE_URL")}
    try:
        plan = db.query(TenantPlan).filter(TenantPlan.code == "pilot").first()
        if not plan:
            plan = TenantPlan(
                name="试点版",
                code="pilot",
                price_monthly=0,
                price_yearly=0,
                features='["seo","publish"]',
                is_active=True,
            )
            db.add(plan)
            db.commit()
            db.refresh(plan)

        tenant = db.query(Tenant).filter(Tenant.is_active).first()
        if not tenant:
            tenant = Tenant(
                id=str(uuid.uuid4()),
                name="试点租户",
                domain=f"pilot-{uuid.uuid4().hex[:8]}",
                plan_id=plan.id,
                status="active",
                is_active=True,
            )
            db.add(tenant)
            db.commit()
        platforms = db.query(Platform).filter(Platform.is_active).limit(10).all()
        report["platforms"] = len(platforms)
        for plat in platforms:
            if not db.query(PlatformAccount).filter_by(platform_id=plat.id).first():
                db.add(
                    PlatformAccount(
                        platform_id=plat.id,
                        account_name=f"demo-{plat.name}",
                        login_status="logged_in",
                        is_active=True,
                    )
                )
        db.commit()
        master = ContentMaster(
            tenant_id=tenant.id,
            title="B7 试点母版",
            body="试点正文",
            tenant_canonical_url="https://www.example-pilot.com/article/1",
            show_on_hub=True,
            status="draft",
        )
        db.add(master)
        db.commit()
        db.refresh(master)
        task_ids = []
        for plat in platforms:
            acc = db.query(PlatformAccount).filter_by(platform_id=plat.id).first()
            if not acc:
                continue
            t = PublishTask(
                content_master_id=master.id,
                platform_id=plat.id,
                account_id=acc.id,
                region=getattr(plat, "region", None) or "cn",
                primary_url=master.tenant_canonical_url,
                secondary_url=f"https://youding.com/industry/{tenant.domain}/{master.id}",
                status="pending",
            )
            db.add(t)
            db.flush()
            task_ids.append(t.id)
        db.commit()
        stats = run_process_pending_tasks(db, limit=20)
        report["task_ids"] = task_ids
        report["worker"] = stats
        # 无真实发布凭证时任务应失败，禁止 demo-/primary_url 假成功
        report["ok"] = (
            len(task_ids) >= 10
            and stats.get("processed", 0) >= 10
            and stats.get("success", 0) == 0
            and stats.get("failed", 0) >= 10
        )
    finally:
        db.close()
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(json.dumps(report, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
