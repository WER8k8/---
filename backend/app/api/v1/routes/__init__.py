# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""API v1 路由模块汇聚层。

已通过 FIX-30 auto_discovery 机制实现了完全的自动路由注册。
路由的 prefix 和 tags 已注入到各个独立的模块文件中。
"""
from pathlib import Path
from fastapi import APIRouter
from app.api.v1.routes.auto_discovery import auto_register_routes

router = APIRouter(prefix="/v1")

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
    #    exclude ab_test：routes/ab_test.py 为假桩（硬编码空数据不查库），
    #    真实实现是顶层 app.api.v1.ab_test（17 端点，前端 pause/complete/variants/stats 全靠它）。
    count_routes = auto_register_routes(router, exclude_modules={"metrics", "ab_test", "invoice_applications"})

    # 2c) invoice_applications 含 client_router/finance_router 双子路由（自带 /client /finance 前缀），
    #     不能走 auto_discovery 的模块名前缀自动包装，否则双前缀；照 admin_bff 先例显式并入。
    try:
        from app.api.v1.routes.invoice_applications import (
            client_router as invoice_client_router,
            finance_router as invoice_finance_router,
        )

        router.include_router(invoice_client_router)
        router.include_router(invoice_finance_router)
        logging.getLogger(__name__).info("FIX-30: 已挂载 invoice_applications client/finance 双子路由")
    except Exception as _inv_exc:  # noqa: BLE001
        logging.getLogger(__name__).error("FIX-30: 挂载 invoice_applications 失败: %s", _inv_exc)

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
    try:
        from app.api.v1.marketing import router as marketing_router
        router.include_router(marketing_router)
        logging.getLogger(__name__).info("MarTech: 已挂载 marketing 子包")
    except Exception as _mkt_exc:  # noqa: BLE001
        logging.getLogger(__name__).error("MarTech: 挂载 marketing 子包失败: %s", _mkt_exc)
    try:
        from app.api.v1.geo import router as geo_router
        router.include_router(geo_router)
        logging.getLogger(__name__).info("GEO: 已挂载 geo 子包")
    except Exception as _geo_exc:  # noqa: BLE001
        logging.getLogger(__name__).error("GEO: 挂载 geo 子包失败: %s", _geo_exc)

    # 3) 扫描 app.api.v1 顶层散落 .py 模块（不在 routes/ 下的独立文件）
    #    显式排除：routes（已扫）、admin_bff（已手动）、ai/chat/seo/super_admin/system/marketing/geo（子包）
    from app.api.v1.routes.auto_discovery import _resolve_domain_tag as _domain_tag
    _TOP_LEVEL_EXCLUDE = {
        "routes", "admin_bff", "ai", "chat", "seo", "super_admin", "system", "marketing", "geo",
        "__init__",  # 包初始化文件，无 router
        # 重复实现：routes/ 下已有权威版本（routes.analytics 11 路由 / routes.users
        # 覆盖全部用户端点），顶层文件仅保留模型供 import，路由不再注册。
        "analytics", "users",
        # routes/ 权威版已服务前端全部调用（含 /products/popular、/products/slug/{slug}、
        # /content/pages/stats、/content/pages/upload-image、/content/seo/{type}/{id}）。
        # 顶层独有端点（by-slug、pages/export、seo/page/{id} 等）零调用方或已被
        # routes/ 泛化模式遮蔽（seo/page/{id} → seo/{resource_type}/{resource_id}），不再注册。
        "content", "products",
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
