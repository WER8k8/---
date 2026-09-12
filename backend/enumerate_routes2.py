"""正确枚举 FastAPI 0.139 路由：穿透 _IncludedRouter / Mount。"""
import warnings
warnings.filterwarnings("ignore")

from fastapi.routing import APIRoute
from starlette.routing import Mount
from app.main import app

paths = {}

def add(path, methods):
    if not path.startswith("/"):
        path = "/" + path
    paths.setdefault(path, set()).update(methods)

def walk(routes, prefix=""):
    for r in routes:
        if isinstance(r, APIRoute):
            add(prefix + r.path, [m for m in r.methods if m not in ("HEAD", "OPTIONS")])
        elif isinstance(r, Mount):
            sub = getattr(r, "app", None)
            if sub is not None and hasattr(sub, "routes"):
                walk(sub.routes, prefix + r.path)
        else:
            # _IncludedRouter（FastAPI 0.139）或任何持有子 router 的对象
            sub = getattr(r, "router", None)
            p2 = getattr(r, "prefix", "") or ""
            if sub is not None and hasattr(sub, "routes"):
                walk(sub.routes, prefix + p2)
            elif hasattr(r, "routes"):
                walk(r.routes, prefix)

walk(app.routes)
print("真实挂载 PATH 总数:", len(paths))

from collections import Counter
c = Counter()
for k in paths:
    parts = k.split("/")
    seg = parts[3] if len(parts) > 3 else "(root)"
    c[seg] += 1
print("\n=== /api/v1/<业务域> 分布 (前 40) ===")
for seg, nn in c.most_common(40):
    print(f"  {nn:3d}  /{seg}")

print("\n=== 关键业务端点是否存在 ===")
for key in ["/api/v1/health", "/api/v1/products", "/api/v1/auth/login", "/api/v1/orders",
            "/api/v1/leads/summary", "/api/v1/seo", "/api/v1/tenants", "/api/v1/inquiries"]:
    hit = [k for k in paths if k.startswith(key)]
    print(f"  {'OK ' if hit else 'MISS'} {key}  -> {hit[:2]}")
