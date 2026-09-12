#!/usr/bin/env python3
"""为已有租户 site_content 补全 SITE-JTBD-01 字段（幂等，仅填空）。"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)
os.environ.setdefault("DATABASE_URL", "sqlite:///./youding_dev.db")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("SECRET_KEY", "backfill-jtbd-" + ("x" * 24))
os.environ.setdefault("JWT_SECRET_KEY", os.environ["SECRET_KEY"])

from app.core.database import SessionLocal  # noqa: E402
from app.models.tenant import Tenant  # noqa: E402
from app.services.jtbd_site_service import apply_jtbd_site_pass  # noqa: E402
from app.services.site_content_bridge import sync_site_content_to_brand  # noqa: E402


def _safe_settings(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def main() -> int:
    db = SessionLocal()
    updated = 0
    skipped = 0
    try:
        rows = db.query(Tenant).filter(Tenant.is_active.is_(True)).all()
        for tenant in rows:
            settings = _safe_settings(tenant.settings)
            brand = settings.get("brand") if isinstance(settings.get("brand"), dict) else {}
            site = brand.get("site_content") if isinstance(brand.get("site_content"), dict) else {}
            if not site:
                skipped += 1
                continue
            before = json.dumps(site.get("pages", {}).get("home", {}), sort_keys=True)
            merged = apply_jtbd_site_pass(site)
            after = json.dumps(merged.get("pages", {}).get("home", {}), sort_keys=True)
            if before == after and site.get("meta", {}).get("jtbd_applied"):
                skipped += 1
                continue
            brand["site_content"] = merged
            settings["brand"] = sync_site_content_to_brand(brand, merged)
            tenant.settings = json.dumps(settings, ensure_ascii=False)
            db.add(tenant)
            updated += 1
        db.commit()
        print(f"JTBD backfill: updated={updated} skipped={skipped}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
