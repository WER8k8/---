#!/usr/bin/env python3
"""FORUM-01~05 smoke — 路由、Webhook 增强、语言桥、Sidecar 状态。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def main() -> int:
    errors: list[str] = []

    try:
        from app.api.v1.routes.forum import router as forum_router
        from app.api.v1.routes.public_forum import router as public_router

        paths = {getattr(r, "path", "") for r in forum_router.routes}
        need = {"/forum/status", "/forum/config", "/forum/webhook", "/forum/setup-guide", "/forum/translate-qa"}
        missing = need - paths
        if missing:
            errors.append(f"forum routes missing: {missing}")
        pub = {getattr(r, "path", "") for r in public_router.routes}
        if "/tenants/{domain}/forum-embed" not in pub:
            errors.append("public forum-embed missing")
    except Exception as exc:
        errors.append(f"import routes: {exc}")

    try:
        from app.services.forum_sidecar_service import forum_sidecar_status, sidecar_base_url
        from app.services.forum_webhook_service import ingest_forum_webhook

        st = forum_sidecar_status()
        if not st.get("url"):
            errors.append("sidecar url empty")
        if sidecar_base_url() != st.get("url"):
            errors.append("sidecar url mismatch")
    except Exception as exc:
        errors.append(f"sidecar status: {exc}")

    try:
        from sqlalchemy.exc import OperationalError

        from app.db.session import SessionLocal
        from app.models.tenant import Tenant
        from app.services.forum_webhook_service import ingest_forum_webhook as _ingest

        db = SessionLocal()
        try:
            tenant = db.query(Tenant).first()
            if tenant:
                r = _ingest(
                    db,
                    tenant=tenant,
                    payload={"event": "question.created", "title": "岩棉 A1 防火厚度多少"},
                )
                if not r.get("ok"):
                    errors.append("webhook ingest failed")
        finally:
            db.close()
    except OperationalError:
        print("WARN: DB unavailable, skip webhook ingest test")
    except Exception as exc:
        errors.append(f"webhook db test: {exc}")

    try:
        from app.api.v1.routes.building_wiki import create_forum_qa_draft

        art = create_forum_qa_draft("岩棉防火等级", "A1级不燃，常用密度80-120kg/m3，厚度按设计要求。" * 2)
        if not art or not art.get("id"):
            errors.append("wiki forum draft failed")
    except Exception as exc:
        errors.append(f"wiki draft: {exc}")

    if errors:
        print("FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print("OK forum sidecar FORUM-01~05")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
