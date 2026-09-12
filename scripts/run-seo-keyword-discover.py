#!/usr/bin/env python3
"""周一 SEO 挖词 — 产业带词库 + 租户站点关键词 → 建议列表（诚实，无假排名）。

Usage:
  python scripts/run-seo-keyword-discover.py
  python scripts/run-seo-keyword-discover.py --tenant dev.local
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "ops" / "seo-keyword-discover-latest.json"
BACKEND = ROOT / "backend"

sys.path.insert(0, str(BACKEND))
os.environ.setdefault("ENVIRONMENT", "development")
os.environ["DB_TYPE"] = "sqlite"
os.environ.setdefault("JWT_SECRET_KEY", "seo-keyword-discover-" + "x" * 24)
os.environ.setdefault("SECRET_KEY", os.environ["JWT_SECRET_KEY"])

# 强制 dev SQLite，避免误读本机 .env 里的 Postgres
from app.core.sqlite_paths import resolve_sqlite_database_url as _resolve_sqlite  # noqa: E402

_dev_sqlite = _resolve_sqlite("sqlite:///./youding_dev.db")
os.environ["DATABASE_URL"] = _dev_sqlite

import app.models  # noqa: E402

from app.core import database as db_mod  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.models.tenant import Tenant  # noqa: E402
from app.services.dacheng_keyword_seed_service import list_belt_packs, load_dacheng_keyword_pack  # noqa: E402
from app.services.tenant_product_context import resolve_tenant_product_hint  # noqa: E402

_db_url = _dev_sqlite
settings.DATABASE_URL = _db_url
os.environ["DATABASE_URL"] = _db_url
db_mod.rebind_engine(_db_url)


def _tenant_keywords(tenant: Tenant) -> list[str]:
    out: list[str] = []
    hint = resolve_tenant_product_hint(tenant)
    if hint:
        out.append(hint.strip())
    try:
        settings = json.loads(tenant.settings or "{}")
        brand = settings.get("brand") if isinstance(settings.get("brand"), dict) else {}
        site = brand.get("site_content") if isinstance(brand.get("site_content"), dict) else {}
        pages = site.get("pages") if isinstance(site.get("pages"), dict) else {}
        home = pages.get("home") if isinstance(pages.get("home"), dict) else {}
        raw = str(home.get("seoKeywords") or "").strip()
        for part in raw.split(","):
            t = part.strip()
            if t and t not in out:
                out.append(t)
    except (json.JSONDecodeError, TypeError):
        pass
    return out[:12]


def main() -> int:
    parser = argparse.ArgumentParser(description="Monday SEO keyword discovery")
    parser.add_argument("--tenant", default="dev.local")
    parser.add_argument("--belt-id", default="all")
    parser.add_argument("--limit", type=int, default=40)
    args = parser.parse_args()

    db = db_mod.SessionLocal()
    try:
        tenant = db.query(Tenant).filter(Tenant.domain == args.tenant, Tenant.is_active.is_(True)).first()
        tenant_kws = _tenant_keywords(tenant) if tenant else []
        packs = list_belt_packs(belt_id=args.belt_id)
        belt_kws: list[str] = []
        seen: set[str] = set()
        for pack in packs:
            for kw in pack.get("ranking_keywords") or []:
                text = str(kw).strip()
                if text and text not in seen:
                    seen.add(text)
                    belt_kws.append(text)
            for prod in pack.get("products") or []:
                if isinstance(prod, dict):
                    for field in ("name", "keyword", "en"):
                        text = str(prod.get(field) or "").strip()
                        if text and text not in seen:
                            seen.add(text)
                            belt_kws.append(text)

        suggestions: list[dict[str, str]] = []
        for kw in tenant_kws:
            suggestions.append({"keyword": kw, "source": "tenant_site", "priority": "high"})
        for kw in belt_kws:
            if len(suggestions) >= args.limit:
                break
            if any(s["keyword"] == kw for s in suggestions):
                continue
            suggestions.append({"keyword": kw, "source": "belt_pack", "priority": "medium"})

        payload = {
            "ok": True,
            "task": "SEO-KEYWORD-DISCOVER",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "weekday": datetime.now().strftime("%A"),
            "tenant": args.tenant,
            "tenant_found": tenant is not None,
            "belt_id": args.belt_id,
            "pack_meta": {
                "belts": len(packs),
                "root_version": load_dacheng_keyword_pack().get("version"),
            },
            "suggestion_count": len(suggestions),
            "suggestions": suggestions[: args.limit],
            "next_actions": [
                "租户管理员可在「SEO 关键词」页 preview/seed 入库",
                "GEO 引擎用 primary keyword 跑 unified-geo-v1",
                "未接 DeerFlow 时不宣称已自动排名",
            ],
            "out_of_scope": ["无实盘 Baidu 排名", "无 Perplexity Key 时不跑 AI 榜"],
        }
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"ok": True, "count": len(suggestions), "report": str(REPORT)}, ensure_ascii=False))
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
