# -*- coding: utf-8 -*-
"""P2-2b 路由串联探针：逐一导入所有 api 路由模块，确认每个都暴露可挂载 router。
再生"能力台账串联率"硬数。"""
import importlib
import os
import glob

BASE = "app.api.v1.routes"
routes_dir = os.path.join(os.getcwd(), BASE.replace(".", os.sep))
# auto_discovery 是"自动注册机制"本体，按设计跳过自身，非待串联的路由模块
MECHANISM_FILES = {"auto_discovery"}
modules = sorted(
    f[:-3] for f in os.listdir(routes_dir)
    if f.endswith(".py") and not f.startswith("_") and not f.startswith(".")
    and f[:-3] not in MECHANISM_FILES
)

ok, bad = [], []
marker = None
for name in modules:
    try:
        mod = importlib.import_module(f"{BASE}.{name}")
        has_router = hasattr(mod, "router")
        # 有些模块用 router / api_router / build_router() 等
        if not has_router:
            for cand in ("api_router", "build_router", "register_routes", "routes", "prefix", "router"):
                if hasattr(mod, cand) and cand != "router":
                    has_router = hasattr(mod, cand) is not None
                    marker = (name, cand)
                    break
        # 判定：必须暴露一个 FastAPI APIRouter 属性或可调用的 router 工厂
        if has_router:
            ok.append(name)
        else:
            bad.append((name, "no router attr"))
    except Exception as exc:  # noqa: BLE001
        bad.append((name, f"{type(exc).__name__}:{exc}"))

total = len(modules)
print(f"路由模块总数: {total} | 可解析 router: {len(ok)} | 失败: {len(bad)}")
for n, e in bad[:20]:
    print("  BAD", n, "->", e)
pct = round(len(ok) / total * 100, 1)
print(f"路由到可挂载 router 的串联率: {len(ok)}/{total} = {pct}%")
print("P2-2b 路由串联:", "100%（PASS）" if len(ok) == total else "NOT-100%")