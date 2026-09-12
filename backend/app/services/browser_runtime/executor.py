"""Browser Runtime 真实执行器（轮25-C，Playwright 真接入）。

按 evidence.py 的 EvidenceRecord 6 态契约，落地 navigate / extract / screenshot
三类只读动作的 Playwright async API 调用。fill / click / submit 等写动作在
25-D 接入，本轮仅注册但未实现。

设计要点：
- 走 persistent context（per-tenant user_data_dir），cookies/storage 物理隔离；
- 单次执行 max 30s 硬超时（防御 slow page 死锁）；
- nav 完成后做一次 final screenshot（仅 screenshot 动作再额外覆盖）—— 默认
  执行都留 screenshot 证据（合规审计的最强证据形式）；
- 任何内部异常（超时/网络/JS 错误）统一抛 BrowserRuntimeUnavailable，调用
  方（runtime.execute）负责降级。
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from typing import Any, Optional

from app.core.config import settings
from app.services.browser_runtime.evidence import EvidenceRecord, persist_evidence
from app.services.browser_runtime.exceptions import BrowserRuntimeUnavailable
from app.services.browser_runtime.profile import ProfilePath

logger = logging.getLogger("uj-admin.browser_runtime.executor")

# 单次执行硬超时（秒）—— 防御 slow page 死锁；高负载场景未来按租户调
DEFAULT_TIMEOUT_SEC = 30

# 截图白名单输出目录（防路径注入）
_SCREENSHOT_NAME_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")

# 单节点并发信号量（建议 2 落地：并发限流护栏，防 Chromium 撑爆系统内存）
_concurrency_lock = asyncio.Lock()
_concurrency_semaphore: Optional[asyncio.Semaphore] = None


async def _acquire_concurrency_token():
    """获取并发执行配额。"""
    global _concurrency_semaphore
    if _concurrency_semaphore is None:
        async with _concurrency_lock:
            if _concurrency_semaphore is None:
                max_concurrency = int(
                    getattr(settings, "BROWSER_RUNTIME_MAX_CONCURRENCY", 4) or 4
                )
                _concurrency_semaphore = asyncio.Semaphore(max_concurrency)
    return _concurrency_semaphore


async def _create_browser_context(pw: Any, profile_path: str):
    """创建浏览器执行上下文：优先连接远程 CDP 集群（Sidecar），降级为本机持久化沙箱。"""
    ws_endpoint = (getattr(settings, "BROWSER_RUNTIME_WS_ENDPOINT", "") or "").strip()
    if ws_endpoint:
        try:
            logger.debug("Connecting to remote CDP browser cluster: %s", ws_endpoint)
            browser = await pw.chromium.connect_over_cdp(
                ws_endpoint,
                timeout=DEFAULT_TIMEOUT_SEC * 1000,
            )
            ctx = await browser.new_context(
                viewport={"width": 1280, "height": 720},
            )
            return ctx
        except Exception as exc:
            logger.warning(
                "Failed to connect to remote CDP %s, falling back to local sandbox: %s",
                ws_endpoint, exc,
            )

    return await pw.chromium.launch_persistent_context(
        user_data_dir=profile_path,
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
        ],
        viewport={"width": 1280, "height": 720},
        timeout=DEFAULT_TIMEOUT_SEC * 1000,
    )


def _new_screenshot_filename(evidence_id: str) -> str:
    """基于 evidence_id 生成安全文件名（仅 [A-Za-z0-9._-]）。"""
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", evidence_id)[:64] or "evidence"
    return f"{safe}.png"


async def _real_execute_screenshot(
    *,
    evidence: EvidenceRecord,
    profile: ProfilePath,
) -> EvidenceRecord:
    """screenshot 动作真实执行：launch persistent context → navigate → screenshot。"""
    from playwright.async_api import (  # noqa: PLC0415
        async_playwright,
        TimeoutError as PWTimeout,
    )

    safe_name = _new_screenshot_filename(evidence.id)
    screenshot_full_path = os.path.join(profile.path, "screenshots", safe_name)
    os.makedirs(os.path.dirname(screenshot_full_path), exist_ok=True)

    async with async_playwright() as pw:
        try:
            ctx = await _create_browser_context(pw, profile.path)
        except Exception as exc:  # noqa: BLE001
            raise BrowserRuntimeUnavailable(
                f"playwright launch failed: {str(exc)[:300]}"
            )
        try:
            page = ctx.pages[0] if ctx.pages else await ctx.new_page()
            try:
                await page.goto(
                    evidence.target_url,
                    wait_until="domcontentloaded",
                    timeout=DEFAULT_TIMEOUT_SEC * 1000,
                )
            except PWTimeout as exc:
                # 部分加载成功也算"留证"——保留超时截图
                logger.warning(
                    "executor: nav timeout tenant=%s url=%s (continuing with partial capture)",
                    evidence.metadata.get("masked_tenant"),
                    evidence.target_url,
                )
                evidence.metadata["nav_timeout"] = True
            # screenshot
            try:
                await page.screenshot(
                    path=screenshot_full_path,
                    full_page=False,
                    timeout=DEFAULT_TIMEOUT_SEC * 1000,
                )
            except Exception as exc:  # noqa: BLE001
                raise BrowserRuntimeUnavailable(
                    f"screenshot failed: {str(exc)[:300]}"
                )
        finally:
            try:
                await ctx.close()
            except Exception:  # noqa: BLE001
                pass

    # 写入 Evidence
    size = 0
    try:
        size = os.path.getsize(screenshot_full_path)
    except OSError:
        size = 0
    if size == 0:
        raise BrowserRuntimeUnavailable(
            "screenshot file empty or missing"
        )
    evidence.mark_success(
        output_ref=screenshot_full_path,
        output_summary=f"screenshot {size}B → {os.path.basename(screenshot_full_path)}",
        screenshot_path=screenshot_full_path,
        screenshot_size_bytes=size,
    )
    evidence.metadata["user_data_dir"] = profile.path
    return evidence


async def _real_execute_extract(
    *,
    evidence: EvidenceRecord,
    profile: ProfilePath,
) -> EvidenceRecord:
    """extract 动作真实执行：launch → navigate → 取 title/body 文本。"""
    from playwright.async_api import (  # noqa: PLC0415
        async_playwright,
        TimeoutError as PWTimeout,
    )

    extracted: dict[str, Any] = {}

    async with async_playwright() as pw:
        try:
            ctx = await _create_browser_context(pw, profile.path)
        except Exception as exc:  # noqa: BLE001
            raise BrowserRuntimeUnavailable(
                f"playwright launch failed: {str(exc)[:300]}"
            )
        try:
            page = ctx.pages[0] if ctx.pages else await ctx.new_page()
            try:
                await page.goto(
                    evidence.target_url,
                    wait_until="domcontentloaded",
                    timeout=DEFAULT_TIMEOUT_SEC * 1000,
                )
            except PWTimeout as exc:
                logger.warning(
                    "executor: nav timeout tenant=%s url=%s (extract partial)",
                    evidence.metadata.get("masked_tenant"),
                    evidence.target_url,
                )
                evidence.metadata["nav_timeout"] = True
            extracted["title"] = (await page.title())[:300]
            try:
                body_text = await page.evaluate(
                    "() => document.body ? (document.body.innerText || '').slice(0, 2000) : ''"
                )
                extracted["body_preview"] = (body_text or "")[:2000]
            except Exception as exc:  # noqa: BLE001
                extracted["body_preview"] = ""
                extracted["body_error"] = str(exc)[:200]
        finally:
            try:
                await ctx.close()
            except Exception:  # noqa: BLE001
                pass

    evidence.mark_success(
        output_ref=None,
        output_summary=f"extracted title={extracted.get('title', '')[:50]}",
    )
    evidence.metadata["extracted"] = extracted
    evidence.metadata["user_data_dir"] = profile.path
    return evidence


async def _real_execute_navigate(
    *,
    evidence: EvidenceRecord,
    profile: ProfilePath,
) -> EvidenceRecord:
    """navigate 动作真实执行：launch → goto → status_code 收集。"""
    from playwright.async_api import (  # noqa: PLC0415
        async_playwright,
        TimeoutError as PWTimeout,
    )

    status_code: Optional[int] = None
    final_url: Optional[str] = None

    async with async_playwright() as pw:
        try:
            ctx = await _create_browser_context(pw, profile.path)
        except Exception as exc:  # noqa: BLE001
            raise BrowserRuntimeUnavailable(
                f"playwright launch failed: {str(exc)[:300]}"
            )
        try:
            page = ctx.pages[0] if ctx.pages else await ctx.new_page()
            try:
                response = await page.goto(
                    evidence.target_url,
                    wait_until="domcontentloaded",
                    timeout=DEFAULT_TIMEOUT_SEC * 1000,
                )
                if response is not None:
                    status_code = response.status
                    final_url = response.url
            except PWTimeout:
                logger.warning(
                    "executor: nav timeout tenant=%s url=%s",
                    evidence.metadata.get("masked_tenant"),
                    evidence.target_url,
                )
                evidence.metadata["nav_timeout"] = True
        finally:
            try:
                await ctx.close()
            except Exception:  # noqa: BLE001
                pass

    evidence.mark_success(
        output_ref=None,
        output_summary=f"navigated status={status_code} → {final_url or 'n/a'}",
    )
    evidence.metadata["status_code"] = status_code
    evidence.metadata["final_url"] = final_url
    evidence.metadata["user_data_dir"] = profile.path
    return evidence


# 动作 → 真实执行函数 的分发表（占位，真实表在所有 handler 定义之后）
# 注：先暂时放空避免 NameError，正式声明见 287 行附近 handler 之后
_REAL_DISPATCH: dict[str, Any] = {}


# ---- 轮25-D：写动作 handler ----

# 轮25-D：brand_guard 净化器懒导入（hermes.brand_guard 无 DB 依赖，干净）
_sanitizer = None


def _sanitize(text: Optional[str]) -> str:
    """brand_guard.sanitize_public_copy 懒导入 + 容错（净化器挂了用原文）。"""
    global _sanitizer
    if _sanitizer is None:
        try:
            from app.services.hermes.brand_guard import sanitize_public_copy
            _sanitizer = sanitize_public_copy
        except Exception:  # noqa: BLE001
            _sanitizer = lambda x: x  # 退化到原样，evidence 仍截断
    if text is None:
        return ""
    return _sanitizer(text) if callable(_sanitizer) else text


async def _real_execute_fill(
    *,
    evidence: EvidenceRecord,
    profile: ProfilePath,
) -> EvidenceRecord:
    """fill 动作：launch + goto + page.fill(selector, sanitized_value)。

    净化必走 brand_guard.sanitize_public_copy（R9 配合项）：
    原文不入库，sanitize 后写 Evidence 摘要（最多 4000 字符）。
    """
    from playwright.async_api import (  # noqa: PLC0415
        async_playwright,
        TimeoutError as PWTimeout,
    )
    selector = (evidence.metadata or {}).get("fill_selector") or ""
    raw_value = (evidence.metadata or {}).get("fill_value") or ""
    sanitized = _sanitize(raw_value)

    async with async_playwright() as pw:
        try:
            ctx = await _create_browser_context(pw, profile.path)
        except Exception as exc:  # noqa: BLE001
            raise BrowserRuntimeUnavailable(
                f"playwright launch failed: {str(exc)[:300]}"
            )
        try:
            page = ctx.pages[0] if ctx.pages else await ctx.new_page()
            try:
                await page.goto(
                    evidence.target_url, wait_until="domcontentloaded",
                    timeout=DEFAULT_TIMEOUT_SEC * 1000,
                )
            except PWTimeout:
                evidence.metadata["nav_timeout"] = True
            try:
                await page.fill(selector, sanitized, timeout=DEFAULT_TIMEOUT_SEC * 1000)
            except Exception as exc:  # noqa: BLE001
                # 失败也写 sanitized/original_len 留证（让 Policy/审计可追溯）
                evidence.fill_selector = selector
                evidence.fill_value_sanitized = sanitized[:4000]
                evidence.fill_value_original_len = len(raw_value)
                raise BrowserRuntimeUnavailable(
                    f"fill failed selector={selector!r}: {str(exc)[:300]}"
                )
        finally:
            try:
                await ctx.close()
            except Exception:  # noqa: BLE001
                pass

    evidence.mark_success(
        output_ref=None,
        output_summary=(
            f"fill selector={selector!r} len={len(sanitized)} (orig={len(raw_value)})"
        ),
        fill_selector=selector,
        fill_value_sanitized=sanitized,
        fill_value_original_len=len(raw_value),
    )
    evidence.metadata["user_data_dir"] = profile.path
    return evidence


async def _real_execute_click(
    *,
    evidence: EvidenceRecord,
    profile: ProfilePath,
) -> EvidenceRecord:
    """click 动作：launch + goto + page.click(selector)。"""
    from playwright.async_api import (  # noqa: PLC0415
        async_playwright,
        TimeoutError as PWTimeout,
    )
    selector = (evidence.metadata or {}).get("click_target") or ""

    async with async_playwright() as pw:
        try:
            ctx = await _create_browser_context(pw, profile.path)
        except Exception as exc:  # noqa: BLE001
            raise BrowserRuntimeUnavailable(
                f"playwright launch failed: {str(exc)[:300]}"
            )
        try:
            page = ctx.pages[0] if ctx.pages else await ctx.new_page()
            try:
                await page.goto(
                    evidence.target_url, wait_until="domcontentloaded",
                    timeout=DEFAULT_TIMEOUT_SEC * 1000,
                )
            except PWTimeout:
                evidence.metadata["nav_timeout"] = True
            try:
                # try await for navigation-aware click (wait for post-click load)
                await page.click(selector, timeout=DEFAULT_TIMEOUT_SEC * 1000)
                # 短等待可能的 SPA 路由（best-effort；超时即继续）
                try:
                    await page.wait_for_load_state(
                        "domcontentloaded", timeout=5000
                    )
                except PWTimeout:
                    evidence.metadata["post_click_nav_timeout"] = True
            except Exception as exc:  # noqa: BLE001
                raise BrowserRuntimeUnavailable(
                    f"click failed selector={selector!r}: {str(exc)[:300]}"
                )
        finally:
            try:
                await ctx.close()
            except Exception:  # noqa: BLE001
                pass

    evidence.mark_success(
        output_ref=None,
        output_summary=f"clicked selector={selector!r}",
        click_target=selector,
    )
    evidence.metadata["user_data_dir"] = profile.path
    evidence.metadata["final_url"] = page.url if False else None  # 不持 page 引用
    return evidence


async def _real_execute_submit(
    *,
    evidence: EvidenceRecord,
    profile: ProfilePath,
    db: Optional[Any] = None,  # 轮 25-E：DB Session 可选（shim 路径传 None 走内置）
) -> EvidenceRecord:
    """submit 动作：launch + goto + page.evaluate(form.submit()) + Evidence 留证。

    重要：本 handler 仅在 policy 已通过 `context.auto_submit=True` 的情况下
    才会被调用（Policy 闸门在 runtime.execute 第 4 步已 reject 默认 submit）。

    轮 25-E：当 db 不为 None 时，走 PolicyEngine 真裁决（合规/窗口/配额/人审
    4 维 + 审批单自动建），decision 写入 evidence.metadata.policy_decision，
    approval_id 写入 evidence.submit_approval_id。当 db 为 None（shim 路径）
    时，保留原内置快路径行为（25-D 的 check_submit_policy + submit_auto=True），
    evidence.submit_approval_id 仍为 None。
    """
    # 轮 25-E：PolicyEngine 真裁决（仅当 db 可用时）
    if db is not None:
        try:
            from app.services.policy.engine import (
                PolicyEngine,
                evaluate_action,
            )
            ctx = evidence.metadata.get("policy_context") or {}
            decision = evaluate_action(
                db,
                action="browser.submit",
                tenant_id=evidence.tenant_id,
                company_id=ctx.get("company_id"),
                agent_id=ctx.get("agent_id"),
                context=ctx,
                auto_create_approval=bool(ctx.get("auto_create_approval", True)),
            )
            evidence.metadata["policy_decision"] = decision.decision
            if decision.approval_id:
                evidence.submit_approval_id = decision.approval_id
            if decision.decision == "deny":
                # PolicyEngine 真裁决拒绝 → 走 BLOCKED 路径
                evidence.mark_blocked(
                    policy_verdict={
                        "allowed": False,
                        "code": "POLICY_ENGINE_DENIED",
                        "reason": "; ".join(decision.reasons)[:500],
                        "details": {"approval_id": decision.approval_id},
                    }
                )
                return evidence
            if decision.decision == "require_approval" and not decision.approval_id:
                # 需人审但未自动建单 → 走 BLOCKED
                evidence.mark_blocked(
                    policy_verdict={
                        "allowed": False,
                        "code": "POLICY_ENGINE_REQUIRE_APPROVAL",
                        "reason": "; ".join(decision.reasons)[:500],
                        "details": {"action_required": "manual approval needed"},
                    }
                )
                return evidence
        except Exception as exc:  # noqa: BLE001
            # PolicyEngine 调用失败 = 走内置快路径（不阻断主链路）
            logger.warning(
                "executor: PolicyEngine evaluate failed, fallback to built-in: %s",
                exc,
            )
            evidence.metadata["policy_engine_error"] = str(exc)[:200]
    from playwright.async_api import (  # noqa: PLC0415
        async_playwright,
        TimeoutError as PWTimeout,
    )
    form_selector = (evidence.metadata or {}).get("form_selector") or "form"

    async with async_playwright() as pw:
        try:
            ctx = await _create_browser_context(pw, profile.path)
        except Exception as exc:  # noqa: BLE001
            raise BrowserRuntimeUnavailable(
                f"playwright launch failed: {str(exc)[:300]}"
            )
        try:
            page = ctx.pages[0] if ctx.pages else await ctx.new_page()
            if evidence.target_url:
                try:
                    await page.goto(
                        evidence.target_url, wait_until="domcontentloaded",
                        timeout=DEFAULT_TIMEOUT_SEC * 1000,
                    )
                except PWTimeout:
                    evidence.metadata["nav_timeout"] = True
            # 提交前自动留证（pre-submit screenshot）——审计最关键
            pre_path = os.path.join(profile.path, "screenshots",
                                    f"presubmit_{evidence.id}.png")
            os.makedirs(os.path.dirname(pre_path), exist_ok=True)
            try:
                await page.screenshot(
                    path=pre_path, full_page=False,
                    timeout=DEFAULT_TIMEOUT_SEC * 1000,
                )
                evidence.screenshot_path = pre_path
                evidence.screenshot_size_bytes = os.path.getsize(pre_path)
            except Exception as exc:  # noqa: BLE001
                logger.warning("executor: pre-submit screenshot failed: %s", exc)
            # 真实 submit（用 evaluate 触发 form.requestSubmit 模拟）
            try:
                submit_result = await page.evaluate(
                    """(sel) => {
                        const f = document.querySelector(sel);
                        if (!f) return { ok: false, reason: 'form_not_found' };
                        if (typeof f.requestSubmit === 'function') {
                            f.requestSubmit();
                        } else {
                            f.submit();
                        }
                        return { ok: true, method: typeof f.method === 'string' ? f.method : 'get' };
                    }""",
                    form_selector,
                )
            except Exception as exc:  # noqa: BLE001
                raise BrowserRuntimeUnavailable(
                    f"submit failed: {str(exc)[:300]}"
                )
            evidence.metadata["submit_result"] = submit_result
        finally:
            try:
                await ctx.close()
            except Exception:  # noqa: BLE001
                pass

    evidence.mark_success(
        output_ref=None,
        output_summary=f"submitted form={form_selector!r} method={submit_result.get('method', '?')}",
        submit_auto=True,
    )
    evidence.metadata["user_data_dir"] = profile.path
    return evidence


# 动作 → 真实执行函数 的分发表（轮25-D：6 动作；轮25-C 起 3 只读 + 25-D 3 写）
_REAL_DISPATCH: dict[str, Any] = {
    "screenshot": _real_execute_screenshot,
    "extract": _real_execute_extract,
    "navigate": _real_execute_navigate,
    # 轮25-D 写动作：
    "fill": _real_execute_fill,
    "click": _real_execute_click,
    "submit": _real_execute_submit,
}


# ============================================================
# 轮 25-F：drag / upload / keyboard 三个新 handler
# ============================================================


async def _real_execute_drag(
    *,
    evidence: EvidenceRecord,
    profile: ProfilePath,
) -> EvidenceRecord:
    """drag 动作：launch + goto + page.mouse.down/move/up 拖拽。

    起点/终点 selector 已在 runtime.execute 第 4 步 Policy 闸门通过
    （DRAG_SELECTORS_MISSING / click_target 双重校验），本 handler 只
    负责 Playwright 调用与留证。
    """
    from playwright.async_api import (  # noqa: PLC0415
        async_playwright,
        TimeoutError as PWTimeout,
    )
    drag_from = (evidence.metadata or {}).get("drag_from_selector") or ""
    drag_to = (evidence.metadata or {}).get("drag_to_selector") or ""

    async with async_playwright() as pw:
        try:
            ctx = await _create_browser_context(pw, profile.path)
        except Exception as exc:  # noqa: BLE001
            raise BrowserRuntimeUnavailable(
                f"playwright launch failed: {str(exc)[:300]}"
            )
        try:
            page = ctx.pages[0] if ctx.pages else await ctx.new_page()
            if evidence.target_url:
                try:
                    await page.goto(
                        evidence.target_url, wait_until="domcontentloaded",
                        timeout=DEFAULT_TIMEOUT_SEC * 1000,
                    )
                except PWTimeout:
                    evidence.metadata["nav_timeout"] = True
            try:
                src = page.locator(drag_from).first
                dst = page.locator(drag_to).first
                await src.hover()
                await page.mouse.down()
                await dst.hover()
                await page.mouse.up()
            except Exception as exc:  # noqa: BLE001
                raise BrowserRuntimeUnavailable(
                    f"drag failed: {str(exc)[:300]}"
                )
        finally:
            try:
                await ctx.close()
            except Exception:  # noqa: BLE001
                pass

    evidence.mark_success(
        output_ref=None,
        output_summary=f"dragged {drag_from!r} → {drag_to!r}",
        drag_from_selector=drag_from,
        drag_to_selector=drag_to,
    )
    evidence.metadata["user_data_dir"] = profile.path
    return evidence


async def _real_execute_upload(
    *,
    evidence: EvidenceRecord,
    profile: ProfilePath,
) -> EvidenceRecord:
    """upload 动作：launch + goto + page.set_input_files 上传文件。

    文件路径白名单 + 扩展名校验已在 Policy 闸门完成（UPLOAD_PATH_NOT_ALLOWED
    / UPLOAD_EXT_DENIED），本 handler 只负责 Playwright 调用与留证。
    """
    from playwright.async_api import (  # noqa: PLC0415
        async_playwright,
        TimeoutError as PWTimeout,
    )
    file_paths = list((evidence.metadata or {}).get("upload_file_paths") or [])
    upload_selector = (evidence.metadata or {}).get("upload_selector") or "input[type=file]"

    async with async_playwright() as pw:
        try:
            ctx = await _create_browser_context(pw, profile.path)
        except Exception as exc:  # noqa: BLE001
            raise BrowserRuntimeUnavailable(
                f"playwright launch failed: {str(exc)[:300]}"
            )
        try:
            page = ctx.pages[0] if ctx.pages else await ctx.new_page()
            if evidence.target_url:
                try:
                    await page.goto(
                        evidence.target_url, wait_until="domcontentloaded",
                        timeout=DEFAULT_TIMEOUT_SEC * 1000,
                    )
                except PWTimeout:
                    evidence.metadata["nav_timeout"] = True
            try:
                await page.set_input_files(
                    upload_selector, file_paths,
                    timeout=DEFAULT_TIMEOUT_SEC * 1000,
                )
            except Exception as exc:  # noqa: BLE001
                raise BrowserRuntimeUnavailable(
                    f"upload failed: {str(exc)[:300]}"
                )
        finally:
            try:
                await ctx.close()
            except Exception:  # noqa: BLE001
                pass

    evidence.mark_success(
        output_ref=None,
        output_summary=f"uploaded {len(file_paths)} file(s) via {upload_selector!r}",
        upload_file_paths=file_paths,
        upload_count=len(file_paths),
    )
    evidence.metadata["user_data_dir"] = profile.path
    return evidence


async def _real_execute_keyboard(
    *,
    evidence: EvidenceRecord,
    profile: ProfilePath,
) -> EvidenceRecord:
    """keyboard 动作：launch + goto + page.keyboard.type/press 输入。

    文本长度 + 按键白名单校验已在 Policy 闸门完成（KEYBOARD_TEXT_TOO_LONG
    / KEYBOARD_KEY_DENIED），本 handler 必走 brand_guard 净化文本（与 fill 一致）。
    """
    from playwright.async_api import (  # noqa: PLC0415
        async_playwright,
        TimeoutError as PWTimeout,
    )
    kb_text = (evidence.metadata or {}).get("keyboard_text")
    kb_keys = list((evidence.metadata or {}).get("keyboard_keys") or [])
    # 与 fill 一致：走 brand_guard 净化（懒导入）
    sanitized = _sanitize(kb_text) if kb_text else None

    async with async_playwright() as pw:
        try:
            ctx = await _create_browser_context(pw, profile.path)
        except Exception as exc:  # noqa: BLE001
            raise BrowserRuntimeUnavailable(
                f"playwright launch failed: {str(exc)[:300]}"
            )
        try:
            page = ctx.pages[0] if ctx.pages else await ctx.new_page()
            if evidence.target_url:
                try:
                    await page.goto(
                        evidence.target_url, wait_until="domcontentloaded",
                        timeout=DEFAULT_TIMEOUT_SEC * 1000,
                    )
                except PWTimeout:
                    evidence.metadata["nav_timeout"] = True
            try:
                if sanitized:
                    await page.keyboard.type(
                        sanitized,
                        timeout=DEFAULT_TIMEOUT_SEC * 1000,
                    )
                for key in kb_keys:
                    await page.keyboard.press(key)
            except Exception as exc:  # noqa: BLE001
                raise BrowserRuntimeUnavailable(
                    f"keyboard failed: {str(exc)[:300]}"
                )
        finally:
            try:
                await ctx.close()
            except Exception:  # noqa: BLE001
                pass

    evidence.mark_success(
        output_ref=None,
        output_summary=(
            f"typed {len(sanitized or '')} chars + pressed {len(kb_keys)} key(s)"
        ),
        keyboard_text=(sanitized or "")[:4000] if sanitized else None,
        keyboard_keys=kb_keys[:50],
    )
    evidence.metadata["user_data_dir"] = profile.path
    return evidence


# 动作 → 真实执行函数 的分发表（轮 25-F 扩展：3 新写动作）
_REAL_DISPATCH_EXT: dict[str, Any] = {
    "drag": _real_execute_drag,
    "upload": _real_execute_upload,
    "keyboard": _real_execute_keyboard,
}
_REAL_DISPATCH.update(_REAL_DISPATCH_EXT)


async def run_real_execution(
    *,
    evidence: EvidenceRecord,
    profile: ProfilePath,
    db: Optional[Any] = None,  # 轮 25-E：DB Session 可选（shim 路径传 None）
) -> EvidenceRecord:
    """真实执行入口（轮25-C 内部 API，runtime.execute 第 5 步调用）。

    异常契约：任何 Playwright 内部异常（launch/nav/screenshot/extract）都
    转抛 BrowserRuntimeUnavailable；调用方负责落 Evidence DEGRADED / FAILED。
    本入口额外兜底：参数缺失（None target_url）+ 未知异常 全部自吞，不外泄。
    """
    handler = _REAL_DISPATCH.get(evidence.action)
    if handler is None:
        # 未注册动作走 25-B 同样的 DEGRADED 路径（forward-compat：未来动作）
        evidence.mark_degraded(
            error_code=f"NOT_IMPLEMENTED_{evidence.action.upper()}",
            error_message=f"action {evidence.action!r} implementation pending",
        )
        return evidence
    try:
        # 防御：screenshot/navigate/extract/fill/click 都需要 target_url（落地页）；
        # submit 不强求（form 可能在 popup / 跨页提交）。
        if evidence.action in (
            "screenshot", "navigate", "extract", "fill", "click"
        ) and not evidence.target_url:
            evidence.mark_failed(
                error_code="TARGET_URL_REQUIRED",
                error_message=f"action {evidence.action!r} requires target_url",
            )
            return evidence
        # fill/click 必带 selector（metadata.fill_selector / click_target）
        if evidence.action == "fill" and not (evidence.metadata or {}).get("fill_selector"):
            evidence.mark_failed(
                error_code="FILL_SELECTOR_REQUIRED",
                error_message="fill requires metadata.fill_selector",
            )
            return evidence
        if evidence.action == "click" and not (evidence.metadata or {}).get("click_target"):
            evidence.mark_failed(
                error_code="CLICK_TARGET_REQUIRED",
                error_message="click requires metadata.click_target",
            )
            return evidence
        # 兜底：任何未被 handler 捕获的异常一律 FAILED，绝不外泄给调用方
        # 轮25-D：BrowserRuntimeUnavailable 也自吞（handler 内部 raise 应视为
        # 单次执行失败而非可恢复的"不可用"——统一 FAILED 路径让 runtime.execute
        # 第 5 步只需 catch Exception 兜底，简化调用方契约）。
        try:
            semaphore = await _acquire_concurrency_token()
            async with semaphore:
                # 轮 25-E：submit handler 需要 db（PolicyEngine 真裁决）
                if evidence.action == "submit":
                    return await handler(evidence=evidence, profile=profile, db=db)
                return await handler(evidence=evidence, profile=profile)
        except BrowserRuntimeUnavailable as exc:
            evidence.mark_failed(
                error_code=exc.__class__.__name__,
                error_message=str(exc)[:500],
            )
            return evidence
        except Exception as exc:  # noqa: BLE001
            evidence.mark_failed(
                error_code="EXEC_RUNTIME_ERROR",
                error_message=str(exc)[:500],
            )
            return evidence
    finally:
        # 取证留痕：打通"仅落盘不入库"断点——每条路径（成功/失败/降级）都集中
        # 落盘，并在 task_traces.evidence 列存在时并入（缺列则降级落盘）。
        # 失败静默忽略，绝不阻断主链路。
        try:
            persist_evidence(evidence, db=db)
        except Exception:  # noqa: BLE001
            logger.warning("run_real_execution: persist_evidence 失败（已忽略）")
    return evidence
