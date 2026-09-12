"""DeepSeek Harness 客户端（懒加载官方 SDK，绝不污染导入期）。

对外暴露三个安全函数：
- is_available()      : SDK 与运行时二进制是否就绪
- health()            : 结构化可用性报告（给 /deepseek-harness/health）
- run_turn(prompt)    : 跑一次 dsh 外层 agent turn，返回 final_response 等

与 hermes_task_bridge 协同：bridge 注册 task_type="deepseek_harness" 时即调用 run_turn，
使统一编排入口 /orchestration/tasks 也能把外层请求路由到 dsh。
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from app.services.deepseek_harness.config import get_settings

logger = logging.getLogger("uj-admin.services.deepseek_harness")

# 清晰的未安装提示（含安装命令）
_INSTALL_HINT = (
    "deepseek_harness SDK 未安装。请运行 '启动脚本/setup-deepseek-harness.bat' "
    "或执行 `pip install deepseek-harness-sdk`（会自动带入预构建 dsh 运行时，无需系统 Node）。"
)


def _import_sdk():
    """懒加载 dsh SDK；缺失时抛出带安装提示的 RuntimeError。"""
    try:
        from deepseek_harness import DeepSeekHarness  # type: ignore
        from deepseek_harness_runtime import bundled_runtime_path  # type: ignore
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(_INSTALL_HINT) from exc
    return DeepSeekHarness, bundled_runtime_path


def is_available() -> bool:
    try:
        _import_sdk()
        return True
    except Exception:
        return False


def runtime_path() -> Optional[str]:
    """返回当前平台 dsh 运行时可执行文件路径，缺失返回 None。"""
    try:
        _, bundled_runtime_path = _import_sdk()
        return str(bundled_runtime_path())
    except Exception as exc:  # noqa: BLE001
        logger.warning("dsh runtime 解析失败: %s", exc)
        return None


def health() -> Dict[str, Any]:
    cfg = get_settings()
    sdk_ok = False
    sdk_err: Optional[str] = None
    try:
        _import_sdk()
        sdk_ok = True
    except Exception as exc:  # noqa: BLE001
        sdk_err = str(exc)
    rp = runtime_path()
    return {
        "available": bool(sdk_ok and rp),
        "sdk_importable": sdk_ok,
        "sdk_error": sdk_err,
        "runtime_binary": rp,
        **cfg.as_dict(),
    }


def run_turn(
    prompt: str,
    *,
    session_id: Optional[str] = None,
    profile: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    reasoning_effort: Optional[str] = None,
    max_tokens: Optional[int] = None,
) -> Dict[str, Any]:
    """运行一次 DeepSeek Harness 外层 agent turn。

    返回 dict：{session_id, final_response, finish_reason, event_count, provider, model, profile}。
    每次调用独立启动/回收 dsh 子进程（SDK 内部惰性启动 + 上下文管理器回收），
    保证多请求并发安全，且出错时子进程一定被回收。
    """
    DeepSeekHarness, _ = _import_sdk()
    cfg = get_settings()
    cfg.ensure_dirs()

    harness = DeepSeekHarness(
        dsh_home=str(cfg.dsh_home),
        cwd=str(cfg.workspace),
        provider=provider or cfg.provider,
        model=model or cfg.model,
        reasoning_effort=reasoning_effort if reasoning_effort is not None else cfg.reasoning_effort,
        max_tokens=max_tokens if max_tokens is not None else cfg.max_tokens,
        profile=profile or cfg.profile,
        api_key=cfg.api_key,
        base_url=cfg.base_url,
        initialize_timeout_seconds=cfg.initialize_timeout_seconds,
        request_timeout_seconds=cfg.request_timeout_seconds,
    )
    with harness:
        result = harness.run(prompt, session_id=session_id)

    return {
        "session_id": result.session_id,
        "final_response": result.final_response,
        "finish_reason": result.finish_reason,
        "event_count": len(result.events),
        "provider": provider or cfg.provider,
        "model": model or cfg.model,
        "profile": profile or cfg.profile,
    }
