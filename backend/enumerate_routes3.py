"""穿透 FastAPI 0.139 _IncludedRouter(original_router) 的真实路由枚举。"""
import warnings
warnings.filterwarnings("ignore")

from fastapi.routing import APIRoute, APIRouter
from starlette.routing import Mount
from app.main import app

paths = {}
seen = set()

def add(path, methods):
    if not path.startswith("/"):
        path = "/" + path
    path = path.replace("//", "/")
    paths.setdefault(path, set()).update(methods)

def walk(routes, prefix=""):
    for r in routes:
        if id(r) in seen:
            continue
        seen.add(id(r))
        if isinstance(r, APIRoute):
            add(prefix + r.path, [m for m in r.methods if m not in ("HEAD", "OPTIONS")])
            continue
        if isinstance(r, Mount):
            sub = getattr(r, "app", None)
            if sub is not None and hasattr(sub, "routes"):
                walk(sub.routes, prefix + r.path)
            continue
        # _IncludedRouter: 子 router 在 original_router
        orig = getattr(r, "original_router", None)
        if orig is not None:
            ictx = getattr(r, "include_context", None)
            ipre = ""
            if isinstance(ictx, dict):
                ipre = ictx.get("prefix", "") or ""
            elif ictx is not None:
                ipre = getattr(ictx, "prefix", "") or ""
            walk(orig.routes, prefix + ipre + (orig.prefix or ""))
            continue
        # 裸 APIRouter
        if isinstance(r, APIRouter):
            walk(r.routes, prefix + (r.prefix or ""))
            continue
        if hasattr(r, "routes"):
            walk(r.routes, prefix)

walk(app.routes)
print("真实挂载 PATH 总数:", len(paths))

from collections import Counter
c = Counter()
for k in paths:
    parts = k.split("/")
    seg = parts[3] if len(parts) > 3 else "(root)"
    c[seg] += 1
print("\n=== /api/v1/<业务域> 分布 (前 45) ===")
for seg, nn in c.most_common(45):
    print(f"  {nn:3d}  /{seg}")

print("\n=== 关键业务端点是否存在 ===")
for key in ["/api/v1/health", "/api/v1/products", "/api/v1/auth/login", "/api/v1/orders",
            "/api/v1/leads/summary", "/api/v1/seo", "/api/v1/tenants", "/api/v1/inquiries",
            "/api/v1/n8n", "/api/v1/deerflow", "/api/v1/sitemap", "/api/v1/site_builder"]:
    hit = [k for k in paths if k.startswith(key)]
    print(f"  {'OK  ' if hit else 'MISS'} {key}  -> {hit[:1]}")
