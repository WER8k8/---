# -*- coding: utf-8 -*-
"""上线就绪度体检：收集闭环报告所需实证数据"""
import warnings, os, sys, json
warnings.filterwarnings("ignore")
os.environ.setdefault("ENV", "dev")

out = {}

# 1. 应用装配
try:
    from app.main import app
    from starlette.routing import Route as StarletteRoute
    paths = set()
    def walk(router, prefix=""):
        for r in getattr(router, "routes", []):
            t = type(r).__name__
            if t == "_IncludedRouter":
                orr = getattr(r, "original_router", None)
                if orr is not None:
                    walk(orr, prefix + getattr(r, "prefix", "") or "")
            elif t == "Mount":
                walk(getattr(r, "app", None), prefix + (getattr(r, "path", "") or ""))
            elif hasattr(r, "path") and hasattr(r, "methods"):
                p = prefix + (getattr(r, "path", "") or "")
                for m in (r.methods or set()):
                    if m not in ("HEAD", "OPTIONS"):
                        paths.add((m, p))
    walk(app)
    out["endpoints"] = len(paths)
    def seg(p):
        parts = [x for x in p.split("/") if x]
        return parts[2] if len(parts) > 2 else (parts[0] if parts else "?")
    allmods = sorted({seg(p) for _, p in paths})
    v1mods = sorted({p.split("/")[2] for _, p in paths if p.startswith("/v1/") and len(p.split("/")) > 3})
    out["api_modules"] = len(v1mods) if v1mods else len(allmods)
    out["api_module_list"] = v1mods if v1mods else allmods[:80]
    out["app_title"] = getattr(app, "title", "?")
except Exception as e:
    out["assembly_error"] = f"{type(e).__name__}: {e}"

# 2. 数据层
try:
    from app.core.database import SessionLocal
    from sqlalchemy import text
    db = SessionLocal()
    def cnt(q):
        try:
            return db.execute(text(q)).scalar() or 0
        except Exception:
            return -1
    out["tables"] = cnt("SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")
    out["users"] = cnt("SELECT count(*) FROM users")
    out["tenants"] = cnt("SELECT count(*) FROM tenants")
    out["user_tenants"] = cnt("SELECT count(*) FROM user_tenants")
    out["admin_roles"] = cnt("SELECT count(*) FROM admin_roles")
    out["admin_permissions"] = cnt("SELECT count(*) FROM admin_permissions")
    out["admin_menus"] = cnt("SELECT count(*) FROM admin_menus")
    out["products"] = cnt("SELECT count(*) FROM products")
    out["leads"] = cnt("SELECT count(*) FROM leads")
    db.close()
except Exception as e:
    out["db_error"] = f"{type(e).__name__}: {e}"

# 3. 配置
try:
    from app.core.config import settings
    out["db_type"] = getattr(settings, "DB_TYPE", "?")
    out["db_url"] = str(getattr(settings, "DATABASE_URL", "?")).split("@")[-1]
    out["redis_enabled"] = getattr(settings, "REDIS_ENABLED", "?")
    out["env"] = getattr(settings, "ENV", getattr(settings, "APP_ENV", "?"))
except Exception as e:
    out["config_error"] = f"{type(e).__name__}: {e}"

print(json.dumps(out, ensure_ascii=False, indent=1))
