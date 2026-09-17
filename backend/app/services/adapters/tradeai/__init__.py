# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Trade AI Agent 适配器（总纲 §5.2：代码级嫁接，MIT）。

来源：Trade AI Agent（Gitee: LBones-li/agent_trade_b，README 声明 MIT；
商用合入前需书面确认，见总纲 §9.4-1）。代码复制于 `_external/trade-ai-agent/`。

桥接其已验证兼容的编排核心三件套（连通性试验 _compat_report2：
IMPORT OK skill_base / workflow_engine / agent）：

    BaseSkill + SkillRegistry   → 迁移 083 skills 表的运行时执行层
    WorkflowEngine/Definition   → ai_tasks（082）子任务条件分支与暂停/恢复
    AgentOrchestrator           → Hermes 内层编排的可挂载执行器

命名冲突处理（关键）：优丁与 Trade AI 顶层包都叫 `app`。
本适配器在初始化时把 vendor 模块整体迁入 `tradeai_vendor.app.*`
命名空间（临时换出-载入-改名-还原），保证：
- 优丁 `app` 包不受污染；
- vendor 模块间 `from app.x import y` 的顶层引用在加载窗口内完成解析。
残余风险：vendor 代码中的函数级惰性 `from app.x import ...`（如有）
会在主进程内命中优丁 app，需在接线前用 grep 扫描确认（见 README）。

冻结约束（总纲 §1.2/§1.3）：
- 适配器不持有链路状态：任务真相归 ai_tasks，本层只做执行；
- 租户隔离优先：对外只暴露 tenant_orchestrator()/make_context()，
  tenant_id 写入 ExecutionContext 状态袋，供落库/审计钩子使用；
- 本模块不被任何现有路由/服务 import（增量挂载，零回归风险）。
"""

from __future__ import annotations

import importlib
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_VENDOR_PREFIX = "tradeai_vendor"
_VENDOR_CORE_MODULES = (
    "app.core.skill_base",
    "app.core.workflow_engine",
    "app.core.agent",
)


# ---------------------------------------------------------------------------
# 1. 路径与环境引导
# ---------------------------------------------------------------------------

def _resolve_tradeai_backend() -> Path:
    """优先环境变量，其次按仓库相对位置推导（工作区根/_external）。"""
    env_path = os.environ.get("TRADEAI_BACKEND_PATH", "").strip()
    if env_path:
        return Path(env_path)
    # 本文件: <ws>/上线网站开发完成/上线网站.worktrees/<wt>/backend/app/services/adapters/tradeai/__init__.py
    ws_root = Path(__file__).resolve().parents[7]
    return ws_root / "_external" / "trade-ai-agent" / "backend"


def _ensure_env() -> None:
    """Trade AI 的 app.config 要求 SECRET_KEY；生产必须显式配置。"""
    if not os.environ.get("SECRET_KEY"):
        dedicated = os.environ.get("TRADEAI_SECRET_KEY", "").strip()
        if dedicated:
            os.environ["SECRET_KEY"] = dedicated
        else:
            os.environ["SECRET_KEY"] = "tradeai-adapter-dev-key-change-in-prod"
            logger.warning(
                "tradeai adapter: SECRET_KEY 未配置，使用开发占位值；"
                "生产环境必须设置 TRADEAI_SECRET_KEY（总纲 §7.7 密钥纪律）"
            )
    os.environ.setdefault("DATABASE_URL", "postgresql://localhost/unused")
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

    # P3 fix: 主仓 dev env 的 CORS_ORIGINS 是逗号字符串，但 vendor Settings 声明
    # CORS_ORIGINS: List[str]（pydantic env 源无法从裸逗号串解析 → vendor 加载失败）。
    # 这里把继承来的逗号串归一化为 JSON 列表字符串，供 vendor List[str] 解析。
    if _normalize_cors_origins(os.environ):
        logger.info("tradeai adapter: CORS_ORIGINS 已归一化为 JSON 列表（兼容 vendor Settings）")


def _normalize_cors_origins(env: dict) -> bool:
    """若 env 里 CORS_ORIGINS 是逗号分隔串（非 JSON 列表），改成 JSON 列表串。

    返回是否发生改动。单元素 / 已 JSON / 空值均不动（无歧义）。
    """
    raw = (env.get("CORS_ORIGINS") or "").strip()
    if not raw:
        return False
    if raw.startswith("["):
        return False  # 已是 JSON 列表格式
    items = [x.strip() for x in raw.split(",") if x.strip()]
    if len(items) <= 1:
        return False  # 单元素无歧义
    import json

    env["CORS_ORIGINS"] = json.dumps(items)
    return True


_backend_path = _resolve_tradeai_backend()


# ---------------------------------------------------------------------------
# 2. 命名空间隔离加载（解决双方顶层包同名 `app` 的冲突）
# ---------------------------------------------------------------------------

def _load_vendor_isolated() -> bool:
    """把 vendor 的 app.* 模块载入并改名到 tradeai_vendor.app.*。

    步骤：换出当前进程已加载的 app.* → 插入 vendor 路径 → 载入核心模块
    （其内部相互引用在此窗口内完成）→ 全部改名为 vendor 前缀 → 还原原 app.*
    → 移除 vendor 路径（避免 tests 等同名目录污染）。
    """
    if f"{_VENDOR_PREFIX}.app" in sys.modules:
        return True
    if not _backend_path.exists():
        logger.error(
            "tradeai adapter: 未找到后端目录 %s（可用 TRADEAI_BACKEND_PATH 指定）",
            _backend_path,
        )
        return False

    _ensure_env()
    saved = {n: sys.modules.pop(n) for n in list(sys.modules) if n == "app" or n.startswith("app.")}
    sys.path.insert(0, str(_backend_path))
    try:
        for m in _VENDOR_CORE_MODULES:
            importlib.import_module(m)
        vendor = {n: sys.modules.pop(n) for n in list(sys.modules) if n == "app" or n.startswith("app.")}
        for n, mod in vendor.items():
            sys.modules[f"{_VENDOR_PREFIX}.{n}"] = mod
        logger.info("tradeai adapter: vendor modules loaded under %s.* (%d modules)", _VENDOR_PREFIX, len(vendor))
        return True
    except Exception as e:  # pragma: no cover
        logger.error("tradeai adapter: vendor 加载失败 %s: %s", type(e).__name__, e)
        return False
    finally:
        sys.modules.update(saved)
        try:
            sys.path.remove(str(_backend_path))
        except ValueError:
            pass


_loaded = _load_vendor_isolated()


# ---------------------------------------------------------------------------
# 3. 惰性导出（统一走 vendor 命名空间）
# ---------------------------------------------------------------------------

_EXPORTS = {
    # skill_base
    "BaseSkill": f"{_VENDOR_PREFIX}.app.core.skill_base",
    "SkillRegistry": f"{_VENDOR_PREFIX}.app.core.skill_base",
    "SkillStatus": f"{_VENDOR_PREFIX}.app.core.skill_base",
    # workflow_engine
    "WorkflowEngine": f"{_VENDOR_PREFIX}.app.core.workflow_engine",
    "WorkflowDefinition": f"{_VENDOR_PREFIX}.app.core.workflow_engine",
    "WorkflowExecution": f"{_VENDOR_PREFIX}.app.core.workflow_engine",
    "StepDefinition": f"{_VENDOR_PREFIX}.app.core.workflow_engine",
    "StepCondition": f"{_VENDOR_PREFIX}.app.core.workflow_engine",
    "ExecutionStatus": f"{_VENDOR_PREFIX}.app.core.workflow_engine",
    # agent / context
    "AgentOrchestrator": f"{_VENDOR_PREFIX}.app.core.agent",
    "ExecutionContext": f"{_VENDOR_PREFIX}.app.core.context",
    "MessageContext": f"{_VENDOR_PREFIX}.app.core.context",
}


def __getattr__(name: str) -> Any:
    """__getattr__。

    参数说明：
    :param name: 参数 name
    :return: 返回处理结果。
    """
    if name in _EXPORTS:
        return getattr(importlib.import_module(_EXPORTS[name]), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# ---------------------------------------------------------------------------
# 4. 租户作用域工厂（唯一推荐入口）
# ---------------------------------------------------------------------------

_tenant_orchestrators: Dict[str, Any] = {}


def tenant_orchestrator(tenant_id: str) -> Any:
    """按租户返回隔离的 AgentOrchestrator 实例（其原生为全局单例，总纲 §5.2.3-④ 改造项）。"""
    if not tenant_id:
        raise ValueError("tenant_id 必填（冻结原则 §1.2-3 租户隔离优先）")
    if tenant_id not in _tenant_orchestrators:
        orch_cls = getattr(importlib.import_module(_EXPORTS["AgentOrchestrator"]), "AgentOrchestrator")
        _tenant_orchestrators[tenant_id] = orch_cls()
        logger.info("tradeai adapter: created orchestrator for tenant=%s", tenant_id)
    return _tenant_orchestrators[tenant_id]


def make_context(
    tenant_id: str,
    task_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    **inputs: Any,
) -> Any:
    """创建带租户标记的 ExecutionContext（tenant_id 入状态袋，供落库/审计钩子）。

    vendor 的 ExecutionContext 构造需要 workflow_id/execution_id（连通性试验后修正），
    缺省时自动生成 UUID，与 ai_tasks 的 trace 关联靠状态袋中的 task_id。
    """
    import uuid
    ctx_cls = getattr(importlib.import_module(_EXPORTS["ExecutionContext"]), "ExecutionContext")
    ctx = ctx_cls(
        workflow_id=workflow_id or f"wf-{uuid.uuid4().hex[:12]}",
        execution_id=execution_id or f"exec-{uuid.uuid4().hex[:12]}",
    )
    ctx.set_state("tenant_id", tenant_id)
    if task_id:
        ctx.set_state("task_id", task_id)
    for k, v in inputs.items():
        ctx.set_input(k, v)
    return ctx


def is_available() -> bool:
    """健康自检：vendor 已隔离加载且核心类可取。"""
    if not _loaded:
        return False
    try:
        _ = __getattr__("BaseSkill")
        _ = __getattr__("WorkflowEngine")
        _ = __getattr__("AgentOrchestrator")
        return True
    except Exception:  # pragma: no cover
        return False
