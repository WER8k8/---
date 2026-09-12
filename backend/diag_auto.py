import warnings, logging, importlib, pkgutil, traceback
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

from fastapi import APIRouter
from app.api.v1.routes import auto_discovery as ad

pkg = "app.api.v1.routes"
package = importlib.import_module(pkg)
pkg_dir = __import__("pathlib").Path(package.__file__).parent

print("=== 逐模块 import 测试 (routes/) ===")
ok, fail = [], {}
for _, mod, is_pkg in pkgutil.iter_modules([str(pkg_dir)]):
    if mod.startswith("_") or mod == "auto_discovery":
        continue
    full = f"{pkg}.{mod}"
    try:
        m = importlib.import_module(full)
        has = hasattr(m, "router") and isinstance(getattr(m, "router"), APIRouter)
        status = "router OK" if has else ("NO router attr" if hasattr(m, "router") else "no router")
        ok.append((mod, status))
    except Exception as e:
        fail[mod] = f"{type(e).__name__}: {str(e)[:200]}"

for mod, st in sorted(ok):
    print(f"  OK   {mod:28s} {st}")
for mod, err in sorted(fail.items()):
    print(f"  FAIL {mod:28s} {err}")

print(f"\n=== 汇总: 成功 {len(ok)} / 失败 {len(fail)} ===")

# 实际运行 auto_register
test = APIRouter(prefix="/v1")
cnt = ad.auto_register_routes(test)
print("auto_register_routes 返回计数:", cnt, " test router 实际 routes:", len(test.routes))
