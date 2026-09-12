import warnings
warnings.filterwarnings("ignore")
from app.main import app
from fastapi.routing import APIRoute, APIRouter
from starlette.routing import Mount

paths = {}
def walk(routes, prefix=""):
    for r in routes:
        if isinstance(r, APIRoute):
            p = r.path
            methods = ",".join(sorted(m for m in r.methods if m not in ("HEAD","OPTIONS")))
            paths.setdefault(p, set()).update(methods.split(","))
        elif isinstance(r, Mount):
            sub = getattr(r, "app", None)
            if sub is not None:
                sp = getattr(sub, "routes", None)
                if sp is not None:
                    walk(sp, prefix + r.path)
        elif hasattr(r, "routes"):
            walk(r.routes, prefix)

walk(app.routes)
print("MOUNTED PATH COUNT:", len(paths))
# 按业务前缀分组
from collections import Counter
c = Counter()
for k in paths:
    parts = k.split("/")
    seg = parts[3] if len(parts) > 3 else "(root)"
    c[seg] += 1
print("\n=== 业务域分布 (prefix /api/v1/<seg>) ===")
for seg, n in c.most_common(60):
    print(f"  {n:3d}  /{seg}")
print("\n=== 完整路径清单 ===")
for k in sorted(paths):
    print(f"  {','.join(sorted(paths[k])):16s} {k}")
