# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Documents\上线网站开发完成\上线网站.worktrees\agents-install-vscode-cline-deploy-strix")
sys.path.insert(0, str(ROOT / "backend"))

import httpx
from sqlalchemy import text

from app.core.database import SessionLocal

r = httpx.get("http://127.0.0.1:8001/health", timeout=5)
print("health", r.status_code, r.text[:180])

db = SessionLocal()
try:
    pub = db.execute(
        text("select count(*) from information_schema.tables where table_schema = 'public'")
    ).scalar()
    allc = db.execute(text("select count(*) from information_schema.tables")).scalar()
    ver = db.execute(text("select version()")).scalar()
    print("pg_public_tables", pub)
    print("pg_all_tables", allc)
    print("pg_version", ver)
    for t in [
        "tenants",
        "users",
        "inquiries",
        "prospect_leads",
        "skills",
        "ai_tasks",
        "orders",
        "token_ledger_entries",
        "products",
        "keywords",
    ]:
        try:
            n = db.execute(text(f"select count(*) from {t}")).scalar()
            print("rows", t, n)
        except Exception as exc:  # noqa: BLE001
            print("rows", t, "ERR", str(exc)[:100])
finally:
    db.close()
