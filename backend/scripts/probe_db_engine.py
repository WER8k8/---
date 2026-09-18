# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Documents\上线网站开发完成\上线网站.worktrees\agents-install-vscode-cline-deploy-strix")
sys.path.insert(0, str(ROOT / "backend"))

from app.core import config as app_config
from app.core.database import SessionLocal, engine
from sqlalchemy import text

print("settings.DB_TYPE", app_config.settings.DB_TYPE)
print("settings.DATABASE_URL", app_config.settings.DATABASE_URL)
print("engine", engine.dialect.name, str(engine.url))
print("env_file", getattr(app_config.settings.model_config, "env_file", None))

# inspect how env candidates resolved
src = Path(app_config.__file__).read_text(encoding="utf-8", errors="ignore")
for i, line in enumerate(src.splitlines()[:50], 1):
    if "env" in line.lower() or "candidate" in line.lower():
        print(f"configL{i}", line)

db = SessionLocal()
try:
    if engine.dialect.name == "postgresql":
        print("public_tables", db.execute(text("select count(*) from information_schema.tables where table_schema='public'")).scalar())
        print("version", db.execute(text("select version()")).scalar())
    else:
        rows = db.execute(text("select name from sqlite_master where type='table' order by name")).fetchall()
        print("sqlite_table_count", len(rows))
        print("sqlite_tables_sample", [r[0] for r in rows[:25]])
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
        "wallet_accounts",
        "opportunity",
        "opportunities",
    ]:
        try:
            n = db.execute(text(f"select count(*) from {t}")).scalar()
            print("rows", t, n)
        except Exception as exc:  # noqa: BLE001
            print("rows", t, "ERR", str(exc).splitlines()[0][:140])
finally:
    db.close()

print("sqlite_file_exists", (ROOT / "backend/youding_dev.db").exists())
print("sqlite_file_size", (ROOT / "backend/youding_dev.db").stat().st_size if (ROOT / "backend/youding_dev.db").exists() else None)

for rel in ["backend/.env", "backend/config/dev/.env", ".env"]:
    p = ROOT / rel
    if not p.exists():
        print("env", rel, "missing")
        continue
    for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = line.strip()
        if s.startswith(("DB_TYPE=", "DATABASE_URL=", "REDIS_URL=", "REDIS_ENABLED=")):
            print("env", rel, s)
