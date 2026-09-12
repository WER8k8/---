"""API v1 路由模块汇聚层。

已通过 FIX-30 auto_discovery 机制实现了完全的自动路由注册。
路由的 prefix 和 tags 已注入到各个独立的模块文件中。
"""
from pathlib import Path
from fastapi import APIRouter
from app.core.response import success_response
from app.api.v1.routes.auto_discovery import auto_register_routes

router = APIRouter(prefix="/v1")

@router.get("/health", tags=["系统"])
def v1_health():
    """API v1 根级健康检查（便于网关探测 `/api/v1/health`）"""
    return success_response(data={"status": "ok"})

# 自动扫描并挂载所有路由。
# 注意：不在包 __init__ 执行期直接调用 auto_register_routes，否则会因循环 import
# （路由子模块回引 app.api.v1.routes / app.main 等尚未完成初始化的包）导致逐模块导入
# 被静默跳过，最终业务路由全部丢失（仅剩 /v1/health）。
# 改为延迟注册：由 app.main 在整条 app 包导入完成后显式调用 register_routes() 触发。
_registered = False


def register_routes():
    """在 app 包完全导入后调用，扫描并挂载全部业务路由（幂等）。

    扫描范围：
      1) app.api.v1.routes 子目录（auto_register_routes 默认范围，含 ~180 个路由模块）；
      2) app.api.v1 顶层散落模块（site_builder / n8n / deerflow / products / orders /
         inquiries / chat 等历史遗留顶层 .py 文件，此前因 auto_discovery 只扫 routes/
         子目录而全部丢失）。
    """
    global _registered
    if _registered:
        return
    import logging

    # 1) 扫描 routes/ 子目录（FIX-30 auto_discovery 原有范围）
    count_routes = auto_register_routes(router, exclude_modules={"metrics"})

    # 2) 手动挂载 admin_bff（它是子包，auto_discovery 不会扫子包；且 prefix/tags 内部自管）
    from app.api.v1.admin_bff import router as admin_bff_router
    router.include_router(admin_bff_router)

    # 2b) P0-03 / P0-02：显式挂载 seo + super_admin 子包。此前二者被 _TOP_LEVEL_EXCLUDE
    #     排除、而 auto_discovery 只扫 routes/ 子目录与 v1 顶层 .py（不扫子包）→ 两大子包
    #     从未被挂载。照 admin_bff 先例显式并入；各自 try 隔离，单个子包导入失败不影响另一个。
    try:
        from app.api.v1.seo import router as seo_router

        router.include_router(seo_router, prefix="/seo", tags=["SEO 高阶"])
        logging.getLogger(__name__).info("P0-03: 已挂载 seo 子包（prefix=/seo）")
    except Exception as _seo_exc:  # noqa: BLE001
        logging.getLogger(__name__).error("P0-03: 挂载 seo 子包失败: %s", _seo_exc)
    try:
        from app.api.v1.super_admin import router as super_admin_router

        # super_admin 子包 router 自带 prefix=/super-admin
        router.include_router(super_admin_router)
        logging.getLogger(__name__).info("P0-02: 已挂载 super_admin 子包（prefix=/super-admin）")
    except Exception as _sa_exc:  # noqa: BLE001
        logging.getLogger(__name__).error("P0-02: 挂载 super_admin 子包失败: %s", _sa_exc)

    # 3) 扫描 app.api.v1 顶层散落 .py 模块（不在 routes/ 下的独立文件）
    #    显式排除：routes（已扫）、admin_bff（已手动）、ai/chat/seo/super_admin/system（子包）
    from app.api.v1.routes.auto_discovery import _resolve_domain_tag as _domain_tag
    _TOP_LEVEL_EXCLUDE = {
        "routes", "admin_bff", "ai", "chat", "seo", "super_admin", "system",
        "__init__",  # 包初始化文件，无 router
    }
    import importlib, pkgutil
    top_count = 0
    try:
        v1_pkg = importlib.import_module("app.api.v1")
        v1_dir = v1_pkg.__file__ and str(Path(v1_pkg.__file__).parent) or ""
        if v1_dir:
            for _, mod_name, _ in pkgutil.iter_modules([v1_dir]):
                if mod_name.startswith("_") or mod_name in _TOP_LEVEL_EXCLUDE:
                    continue
                full = f"app.api.v1.{mod_name}"
                try:
                    m = importlib.import_module(full)
                    if hasattr(m, "router") and isinstance(m.router, APIRouter):
                        prefix = getattr(m, "ROUTE_PREFIX", f"/{mod_name.replace('_', '-')}")
                        if prefix == "/":
                            prefix = ""
                        tags = getattr(m, "ROUTE_TAGS", None) or [_domain_tag(mod_name)]
                        router.include_router(m.router, prefix=prefix, tags=tags)
                        top_count += 1
                        logging.getLogger(__name__).debug(
                            "FIX-30-TOP: 挂载顶层 %s (prefix=%s)", full, prefix,
                        )
                except Exception as e:
                    logging.getLogger(__name__).warning(
                        "FIX-30-TOP: 跳过顶层 %s: %s", full, e,
                    )
    except Exception as e:
        logging.getLogger(__name__).error("FIX-30-TOP: 顶层扫描失败: %s", e)

    _registered = True
    logging.getLogger(__name__).info(
        "FIX-30: routes=%d + top_level=%d + admin_bff=1 → 全部注册完成",
        count_routes, top_count,
    )
