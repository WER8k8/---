"""验证开发配置对齐后：应用能否以 PG 库正常装配 + 路由全量挂载。"""
import warnings
warnings.filterwarnings("ignore")
from dotenv import load_dotenv
load_dotenv("config/dev/.env", override=True)

from fastapi.routing import APIRoute, APIRouter
from starlette.routing import Mount

from app.core.database import engine
print("数据库方言:", engine.dialect.name)
print("数据库 URL:", str(engine.url).split("@")[-1] if "@" in str(engine.url) else str(engine.url))

from app.main import app
print("app.title:", app.title, "| app.APP_NAME 来源 OK")

paths = {}
seen = set()
def add(p, m):
    p = "/" + p.lstrip("/")
    paths.setdefault(p, set()).update(m)

def walk(routes, prefix=""):
    for r in routes:
        if id(r) in seen: continue
        seen.add(id(r))
        if isinstance(r, APIRoute):
            add(prefix + r.path, [x for x in r.methods if x not in ("HEAD","OPTIONS")])
        elif isinstance(r, Mount):
            sub = getattr(r, "app", None)
            if sub is not None and hasattr(sub, "routes"):
                walk(sub.routes, prefix + r.path)
        else:
            orig = getattr(r, "original_router", None)
            if orig is not None:
                walk(orig.routes, prefix + (orig.prefix or ""))
            elif isinstance(r, APIRouter):
                walk(r.routes, prefix + (r.prefix or ""))
            elif hasattr(r, "routes"):
                walk(r.routes, prefix)

walk(app.routes)
print("挂载端点总数:", len(paths))

from app.core.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
try:
    n_users = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
    n_tenant_link = db.execute(text("SELECT COUNT(*) FROM user_tenants")).scalar()
    n_tables = db.execute(text("SELECT COUNT(*) FROM pg_catalog.pg_tables WHERE schemaname='public'")).scalar()
    print(f"数据流校验 -> 表:{n_tables}  用户:{n_users}  用户-租户关联:{n_tenant_link}")
finally:
    db.close()
