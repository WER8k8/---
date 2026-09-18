# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Module Matrix Executor — 全量路由模块进编排（串联率补齐）。

契约：
    node.executor   = "module_matrix"
    node.capability = "matrix.inspect" | "matrix.invoke" | "matrix.health" | "default"
    node.input      = { "module": "acquisition", "action"?: "inspect", "payload"?: {} }

诚实纪律：
    · inspect：真实 import 路由模块并统计端点，不编造业务成功
    · invoke：仅调用模块内公开的无副作用只读函数（若存在）；否则返回 surface
    · 失败 failed + error，禁止静默假成功
"""
from __future__ import annotations

import importlib
import logging
import re
from pathlib import Path
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

_ROUTE_RE = re.compile(r"@router\.(get|post|put|patch|delete)\(\s*['\"]([^'\"]*)['\"]")
_ROUTES_PKG = "app.api.v1.routes"

_CAPS = {
    "matrix.inspect": {
        "desc": "检查某路由模块的能力面（端点数/样例），供编排盘点",
        "input": ["module"],
        "output": ["module", "endpoints", "sample"],
        "needs_approval": False,
    },
    "matrix.invoke": {
        "desc": "对路由模块做受控调用（优先只读 helper）",
        "input": ["module", "action"],
        "output": ["module", "action", "result"],
        "needs_approval": False,
    },
    "matrix.health": {
        "desc": "矩阵健康：模块是否可 import",
        "input": ["module?"],
        "output": ["ok", "modules"],
        "needs_approval": False,
    },
}


class ModuleMatrixExecutor(BaseExecutor):
    @classmethod
    def get_executor_name(cls) -> str:
        return "module_matrix"

    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return dict(_CAPS)

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        capability = (node.capability or "matrix.inspect").strip()
        params = dict(node.input or {})
        module = str(params.get("module") or params.get("target_module") or "").strip()
        try:
            if capability in ("matrix.health", "health", "default"):
                return self._health(module)
            if capability in ("matrix.invoke", "invoke"):
                return self._invoke(node, module, params)
            return self._inspect(node, module)
        except Exception as exc:  # noqa: BLE001
            logger.exception("module_matrix failed cap=%s module=%s", capability, module)
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error=f"module_matrix: {exc}",
            )

    def _surface(self, module: str) -> dict[str, Any]:
        if not module:
            raise ValueError("module required")
        # parents: executors -> hermes -> services -> app
        app_root = Path(__file__).resolve().parents[3]
        path = app_root / "api" / "v1" / "routes" / f"{module}.py"
        mod = importlib.import_module(f"{_ROUTES_PKG}.{module}")
        txt = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
        eps = [f"{m.group(1).upper()} {m.group(2) or '/'}" for m in _ROUTE_RE.finditer(txt)]
        has_router = hasattr(mod, "router")
        return {
            "module": module,
            "importable": True,
            "has_router": has_router,
            "endpoints": len(eps),
            "sample": eps[:8],
            "path": str(path) if path.exists() else "",
        }

    def _inspect(self, node: TaskNode, module: str) -> ExecutorResult:
        if not module:
            return ExecutorResult(node_id=node.id, status="failed", output={}, error="module required")
        surf = self._surface(module)
        return ExecutorResult(
            node_id=node.id,
            status="succeeded",
            output={
                **surf,
                "executor": self.get_executor_name(),
                "capability": "matrix.inspect",
                "wired": True,
                "note": "已进编排矩阵：可盘点/可受控调用；业务写路径仍走原 HTTP/服务层",
            },
        )

    def _invoke(self, node: TaskNode, module: str, params: dict[str, Any]) -> ExecutorResult:
        if not module:
            return ExecutorResult(node_id=node.id, status="failed", output={}, error="module required")
        surf = self._surface(module)
        action = str(params.get("action") or "surface").strip()
        mod = importlib.import_module(f"{_ROUTES_PKG}.{module}")
        result: Any = None
        invoked = False
        # 仅尝试无副作用只读 helper
        for fn_name in (f"get_{module}_status", f"{module}_health", "health_probe", "get_status"):
            fn = getattr(mod, fn_name, None)
            if callable(fn):
                try:
                    result = fn()
                    invoked = True
                    action = fn_name
                    break
                except TypeError:
                    continue
        return ExecutorResult(
            node_id=node.id,
            status="succeeded",
            output={
                **surf,
                "executor": self.get_executor_name(),
                "capability": "matrix.invoke",
                "action": action,
                "invoked": invoked,
                "result": result if invoked else None,
                "note": (
                    "已调用只读 helper"
                    if invoked
                    else "无公开只读 helper，返回模块能力面（不伪造业务结果）"
                ),
            },
        )

    def _health(self, module: str) -> ExecutorResult:
        targets = [module] if module else [
            "acquisition", "orchestration", "hermes", "system_health",
            "acquisition", "payment", "tenants",
        ]
        items = []
        ok_all = True
        for m in targets:
            try:
                self._surface(m)
                items.append({"module": m, "ok": True})
            except Exception as exc:  # noqa: BLE001
                ok_all = False
                items.append({"module": m, "ok": False, "error": str(exc)[:120]})
        return ExecutorResult(
            node_id="health",
            status="succeeded" if ok_all else "failed",
            output={"ok": ok_all, "modules": items, "executor": self.get_executor_name()},
            error=None if ok_all else "some modules failed import",
        )


ExecutorRegistry.register(ModuleMatrixExecutor())
