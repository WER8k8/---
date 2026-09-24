# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""路由内省工具 —— 可靠列出已挂载的全部路由路径。

背景（2026-09-24 全域孤岛普查发现并修复的缺陷）
------------------------------------------------
本仓 FastAPI 版本对 `include_router` 采用**惰性 `_IncludedRouter` 包装**，
因此下面这种写法是坏的：

    paths = [getattr(r, "path", "") or "" for r in app.routes]

实测：`app.routes` 只有 **18 条**（其中 16 条带 path），
而被 include 的业务路由有 **1823 条** —— 全在惰性包装里看不到。

后果（真实误判）：
  · `seven_step_framework_service` 把「已有 39 条 `/api/v1/payment` 路由」
    误报为「缺少 payment 路由」→ 第 1 步恒 fail；
  · `production_readiness_service.check_mounted_routes` 同样会误报一批「缺失」。

正解：走 `app.openapi()` —— 它会完整展开全部子路由；
失败时逐级降级到 routes 遍历（宁可偏少也不抛错）。
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def mounted_route_paths(app: Any = None) -> list[str]:
    """返回已挂载的全部路由路径（去重 + 排序）。

    :param app: FastAPI 实例；留空则自动取 `app.main.app`
    :return: 形如 ``['/api/v1/ops/seven-steps/audit', ...]`` 的路径清单
    """
    target = app
    if target is None:
        try:
            from app.main import app as _app  # noqa: PLC0415

            target = _app
        except Exception as exc:  # noqa: BLE001
            logger.warning("无法导入 app，路由内省返回空清单: %s", exc)
            return []

    paths: set[str] = set()

    # 1) openapi()：唯一能完整展开惰性 include_router 的方式
    try:
        spec = target.openapi() or {}
        paths.update(str(p) for p in (spec.get("paths") or {}).keys())
    except Exception as exc:  # noqa: BLE001
        logger.warning("openapi() 内省失败，降级为 routes 遍历: %s", exc)

    # 2) 降级路径：直接遍历（会偏少，但聊胜于无）
    if not paths:
        try:
            for r in target.routes:
                p = str(getattr(r, "path", "") or "")
                if p:
                    paths.add(p)
        except Exception:  # noqa: BLE001
            pass

    return sorted(paths)


def has_route_path(paths: list[str], prefix: str) -> bool:
    """判断路径清单中是否存在以 ``prefix`` 开头的路由。"""
    return any(p.startswith(prefix) for p in paths)
