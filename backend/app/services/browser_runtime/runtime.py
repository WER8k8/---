"""Browser Runtime 核心（总纲 §4.7 P5：Playwright + CDP）。

本轮 25-B 仅落地**接口契约 + 降级语义**，真实 Playwright 调用实现留待 25-C。
要点：
- 任何 `execute()` 调用无论开关/依赖/Policy 如何，**必返回 EvidenceRecord**（不留白）
- 开关关/白名单不过 → EvidenceRecord 标记 EXEC_DEGRADED（不抛异常）
- Policy 拒绝 → EvidenceRecord 标记 EXEC_BLOCKED（不抛异常）
- Playwright 未装 → EvidenceRecord 标记 EXEC_DEGRADED + warning 日志
- 真实执行成功/失败 → EXEC_SUCCESS / EXEC_FAILED + duration 自动计算

调用方契约：DeerFlow / Paperclip / Hermes / UBrain / Wangcai 任一执行器只需
`await runtime.execute(...)`，主链路不需要 try/except——runtime 自吞所有异常
并落 Evidence（红线 2：零回归）。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.services.browser_runtime.evidence import (
    EXEC_BLOCKED,
    EXEC_DEGRADED,
    EXEC_FAILED,
    EXEC_SUCCESS,
    EvidenceRecord,
)
from app.services.browser_runtime.exceptions import (
    BrowserRuntimeDisabled,
    BrowserRuntimePolicyDenied,
    BrowserRuntimeUnavailable,
)
from app.services.browser_runtime.policy import check_all
from app.services.browser_runtime.profile import (
    ensure_tenant_allowed,
    is_runtime_enabled,
    mask_tenant_id,
    resolve_profile_path,
)

logger = logging.getLogger("uj-admin.browser_runtime")

# 依赖懒导入：未装 Playwright 时降级 noop（红线 2 零回归）
_playwright_spec = None


def _probe_playwright() -> bool:
    """运行时检测 Playwright 是否就绪。失败 = False（不抛）。"""
    global _playwright_spec
    if _playwright_spec is not None:
        return _playwright_spec
    try:
        import playwright.async_api  # noqa: F401, PLC0415
        _playwright_spec = True
    except Exception:  # noqa: BLE001
        _playwright_spec = False
    return _playwright_spec


def status() -> dict[str, Any]:
    """Browser Runtime 当前状态（供 admin 监控/调试）。"""
    return {
        "enabled": is_runtime_enabled(),
        "playwright_available": _probe_playwright(),
        "verdict": "READY" if (is_runtime_enabled() and _probe_playwright())
        else "DEGRADED" if is_runtime_enabled() else "DISABLED",
    }


async def execute(
    *,
    tenant_id: str,
    actor: str,
    action: str,
    url: Optional[str] = None,
    input_text: Optional[str] = None,
    click_target: Optional[str] = None,
    fill_selector: Optional[str] = None,
    fill_value: Optional[str] = None,
    form_selector: Optional[str] = None,
    context: Optional[dict[str, Any]] = None,
    metadata: Optional[dict[str, Any]] = None,
    db: Optional[Any] = None,  # 轮 25-E：DB Session 可选（shim 路径传 None）
) -> EvidenceRecord:
    """执行一次浏览器动作（异步），**必返回 EvidenceRecord**（不抛异常给调用方）。

    异常处理：所有内部异常被捕获并落 Evidence（status=DEGRADED/FAILED/BLOCKED），
    调用方拿到 EvidenceRecord 后由调用方决定是否中断主链路（绝大多数场景：仅
    记 warning 继续）。
    """
    rec = EvidenceRecord(
        tenant_id=tenant_id,
        actor=actor,
        action=action,
        target_url=url,
        input_summary=(input_text or "")[:200] if input_text else None,
        metadata=dict(metadata or {}),
    )
    rec.metadata["profile_path"] = None
    rec.metadata["masked_tenant"] = mask_tenant_id(tenant_id)
    # 轮25-D：写动作专用字段从 kwargs 透传到 metadata
    if click_target is not None:
        rec.metadata["click_target"] = click_target
    if fill_selector is not None:
        rec.metadata["fill_selector"] = fill_selector
    if fill_value is not None:
        rec.metadata["fill_value"] = fill_value
    if form_selector is not None:
        rec.metadata["form_selector"] = form_selector
    if context is not None:
        rec.metadata["policy_context"] = dict(context)

    # 1) 开关 + 白名单闸门
    if not is_runtime_enabled():
        rec.mark_degraded(
            error_code="BROWSER_RUNTIME_DISABLED",
            error_message="BROWSER_RUNTIME_ENABLED is False",
        )
        logger.info(
            "browser_runtime: disabled, degraded tenant=%s action=%s",
            rec.metadata["masked_tenant"], action,
        )
        return rec

    # 2) 白名单（ensure_tenant_allowed 抛 BrowserRuntimeDisabled 时降级）
    try:
        ensure_tenant_allowed(tenant_id)
        prof = resolve_profile_path(tenant_id)
        rec.metadata["profile_path"] = str(prof)
    except BrowserRuntimeDisabled as exc:
        rec.mark_degraded(
            error_code="BROWSER_RUNTIME_DISABLED",
            error_message=str(exc),
        )
        logger.warning(
            "browser_runtime: %s — tenant=%s action=%s",
            rec.error_code, rec.metadata["masked_tenant"], action,
        )
        return rec
    except Exception as exc:  # noqa: BLE001 — Profile 隔离错误也降级（防泄漏优先）
        rec.mark_failed(
            error_code="PROFILE_ISOLATION_ERROR",
            error_message=str(exc),
        )
        logger.error(
            "browser_runtime: profile_isolation tenant=%s action=%s err=%s",
            rec.metadata["masked_tenant"], action, exc,
        )
        return rec

    # 3) Policy 闸门（拒绝 = BLOCKED，不降级）
    # 轮25-D 扩展：click_target / submit 上下文一并校验
    policy_ctx = rec.metadata.get("policy_context") or {}
    verdict = check_all(
        action=action,
        url=url,
        input_text=input_text,
        click_target=click_target or rec.metadata.get("click_target"),
        context=policy_ctx,
    )
    if not verdict.allowed:
        rec.mark_blocked(policy_verdict=verdict.to_dict())
        logger.warning(
            "browser_runtime: blocked tenant=%s action=%s code=%s reason=%s",
            rec.metadata["masked_tenant"], action, verdict.code, verdict.reason,
        )
        return rec

    # 4) 依赖检测
    if not _probe_playwright():
        rec.mark_degraded(
            error_code="PLAYWRIGHT_UNAVAILABLE",
            error_message=(
                "playwright not installed — `pip install playwright && "
                "playwright install chromium`"
            ),
        )
        logger.warning(
            "browser_runtime: playwright unavailable, degraded tenant=%s action=%s",
            rec.metadata["masked_tenant"], action,
        )
        return rec

    # 5) 真实执行（轮25-C：Playwright 真接入；25-D 起补 fill/click/submit）
    rec.mark_running()
    # 防御：导入语句失败会让 from X import Y 触发 UnboundLocalError
    # （Python 函数体内 import 失败会污染同名局部变量），故先在 try 外完成所有 import。
    try:
        from app.services.browser_runtime.profile import ensure_profile_dir
        from app.services.browser_runtime.executor import run_real_execution
        from app.services.browser_runtime.exceptions import (
            BrowserRuntimeUnavailable,
        )
    except ImportError as exc:
        rec.mark_failed(
            error_code="BROWSER_RUNTIME_IMPORT_ERROR",
            error_message=f"import failed: {exc}",
        )
        logger.error(
            "browser_runtime: import failed tenant=%s action=%s err=%s",
            rec.metadata["masked_tenant"], action, exc,
        )
        return rec
    try:
        # 惰性创建 Profile 物理目录（user_data_dir 容器）
        prof_dir = ensure_profile_dir(prof)
        # 轮 25-E：db 透传到 executor（仅 submit handler 实际使用）
        rec = await run_real_execution(evidence=rec, profile=prof_dir, db=db)
    except BrowserRuntimeUnavailable as exc:
        rec.mark_failed(
            error_code=exc.__class__.__name__,
            error_message=str(exc),
        )
        logger.warning(
            "browser_runtime: exec failed tenant=%s action=%s code=%s",
            rec.metadata["masked_tenant"], action, rec.error_code,
        )
    except Exception as exc:  # noqa: BLE001 — 真接入异常一律捕获，绝不外泄
        rec.mark_failed(
            error_code="EXEC_RUNTIME_ERROR",
            error_message=str(exc)[:500],
        )
        logger.error(
            "browser_runtime: unexpected exec error tenant=%s action=%s err=%s",
            rec.metadata["masked_tenant"], action, exc,
        )
    return rec
