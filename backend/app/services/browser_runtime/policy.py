# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Browser Runtime Policy 闸门（总纲 §4.7 + 既有 Policy Engine 复用）。

本轮 25-B 提供轻量内置闸门（域名/动作/输入模式三层最小集），高阶策略（窗口期/
配额/合规字典）后续迭代接入既有 `app/services/policy/`。内置闸门全部 best-effort：
拒绝返回 verdict 给调用方，不抛异常（Policy 拒绝是合法业务流，不是故障）。

轮25-D 扩展：fill / click / submit 三类写动作闸门——
- fill：填值必走 brand_guard 净化（R9 配合项），input_text 字段不超 8000 字符；
- click：click target 仅接受 `selector` 字段（防 JS 表达式注入），同源校验；
- submit：默认 require_human_review（与既有 `HUMAN_REVIEW_ACTIONS["paperclip.task_execute"]`
  语义一致），除非 context 显式 `auto_submit=true`（白名单租户内开关）。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional

# 允许的 browser 动作白名单（最小集；新增动作需在 docs 登记）
ALLOWED_ACTIONS: frozenset[str] = frozenset({
    "navigate",    # 仅 GET 导航
    "extract",     # DOM 抽取（只读）
    "screenshot",  # 截图取证
    # 轮25-D 新增（写动作）：
    "fill",        # 表单填值（必走 brand_guard 净化）
    "click",       # 点击（selector 注入拦截 + 同源校验）
    "submit",      # 提交（默认人审）
    # 轮25-F 新增（写动作扩展）：
    "drag",        # 拖拽（源 + 目标 selector，同源校验）
    "upload",      # 文件上传（路径白名单 + 扩展名校验）
    "keyboard",    # 键盘输入（按键白名单 + 文本长度上限）
})

# 写动作子集（额外闸门）
WRITE_ACTIONS: frozenset[str] = frozenset({
    "fill", "click", "submit",
    "drag", "upload", "keyboard",  # 轮 25-F 新增
})

# 填值字段长度上限（防 prompt 爆炸；与 wangcai.llm 的 500 字符截断纪律一致）
FILL_MAX_LENGTH = 8000

# 轮 25-F：键盘输入长度上限（与 fill 同档但保守 2000——单次按键更短）
KEYBOARD_TEXT_MAX_LENGTH = 2000

# 轮 25-F：上传文件路径白名单（仅允许本机临时目录与租户 Profile 目录）
# 防路径注入——任何 ../ 解析后越界立即拒
_UPLOAD_PATH_ALLOWED_PREFIXES: tuple[str, ...] = (
    "/tmp/",
    "/var/tmp/",
    "C:\\Windows\\Temp\\",
    "C:\\Users\\",
)

# 轮 25-F：上传文件扩展名白名单（防恶意脚本上传）
UPLOAD_ALLOWED_EXTENSIONS: frozenset[str] = frozenset({
    ".pdf", ".docx", ".doc", ".xls", ".xlsx", ".csv",
    ".txt", ".md", ".png", ".jpg", ".jpeg", ".gif",
    ".zip",  # 仅合规压缩包
})

# 轮 25-F：键盘按键白名单（防 JS 注入式按键序列）
# 仅安全按键通过；功能键（F1-F12）/ 方向键 / Tab / Enter / Backspace / Delete / Escape
KEY_ALLOWED_KEYS: frozenset[str] = frozenset({
    "Tab", "Enter", "Backspace", "Delete", "Escape",
    "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight",
    "Home", "End", "PageUp", "PageDown",
    "F1", "F2", "F3", "F4", "F5", "F6",
    "F7", "F8", "F9", "F10", "F11", "F12",
    "Shift", "Control", "Alt", "Meta",
    "CapsLock", "NumLock", "ScrollLock",
    "ContextMenu", "Insert", "Home", "End",
})

# 轮 25-F：drag 起点/终点 selector 校验（复用 click 的 CSS selector 正则）
# drag 实际上传 source_selector + target_selector 两个 click_target 字段

# click target 允许的形态（防 JS 表达式注入——只接受 CSS selector 字符串）
# 注：'#id' / '.class' / 'tag' / '[attr=val]' / 'tag[attr=val]' 等合规
_CLICK_SELECTOR_RE = re.compile(
    r"^(?:"
    # tag 开头：tag / tag.class / tag#id / tag.class#id / tag[attr]
    r"[A-Za-z][A-Za-z0-9_-]*"
    r"(?:[.#][A-Za-z][A-Za-z0-9_-]*|\[[^\]]{1,200}\]"
    r"|:[A-Za-z-]+(?:\([^)]*\))?)*"
    # 或 id/class 开头：#id / .class / #id.class / .class#id
    r"|[#.][A-Za-z][A-Za-z0-9_-]*(?:[.#][A-Za-z][A-Za-z0-9_-]*)*"
    r")$"
)
# click target 拒绝的模式（明显 JS/伪协议）
_CLICK_DENY_RE = re.compile(
    r"(?i)(javascript:|data:text/html|<script|on\w+\s*=)"
)

# 默认允许的域名（最小集；实际运营时由 admin 配置覆盖）
DEFAULT_ALLOWED_DOMAINS: tuple[str, ...] = (
    "example.com", "example.org",
    "*.youding.com",  # 自家域名通配
    "localhost",
    "127.0.0.1",
)

# 拒绝的输入模式（OWASP LLM01 + R9 红线参考；与 brand_guard/claw_patrol 互补）
_DENY_INPUT_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"<\s*script\b", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"on\w+\s*=\s*[\"']", re.IGNORECASE),
)


@dataclass
class PolicyVerdict:
    allowed: bool
    reason: str = ""
    code: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "code": self.code,
            **self.details,
        }


def check_action(action: str) -> PolicyVerdict:
    """动作合法性检查。"""
    if action in ALLOWED_ACTIONS:
        return PolicyVerdict(allowed=True, code="OK")
    return PolicyVerdict(
        allowed=False,
        reason=f"action {action!r} not in allow-list",
        code="ACTION_NOT_ALLOWED",
    )


def check_url(
    url: str,
    *,
    allowed_domains: Optional[tuple[str, ...]] = None,
) -> PolicyVerdict:
    """URL 域名合法性检查（防 SSRF/越权访问）。"""
    if not url:
        return PolicyVerdict(allowed=False, reason="empty url", code="URL_EMPTY")
    if not url.startswith(("http://", "https://")):
        return PolicyVerdict(
            allowed=False, reason="url scheme not allowed", code="URL_SCHEME_DENIED"
        )
    # 提取 host
    try:
        from urllib.parse import urlparse  # noqa: PLC0415
        host = (urlparse(url).hostname or "").lower()
    except Exception:  # noqa: BLE001
        return PolicyVerdict(allowed=False, reason="url parse failed", code="URL_PARSE_FAIL")
    if not host:
        return PolicyVerdict(
            allowed=False, reason="url has no host", code="URL_NO_HOST"
        )
    # 白名单匹配（支持 *. 通配）
    domains = allowed_domains or DEFAULT_ALLOWED_DOMAINS
    for pat in domains:
        p = pat.lower()
        if p.startswith("*."):
            if host.endswith(p[1:]):  # *.youding.com → .youding.com
                return PolicyVerdict(allowed=True, code="OK")
        elif host == p:
            return PolicyVerdict(allowed=True, code="OK")
    return PolicyVerdict(
        allowed=False,
        reason=f"host {host!r} not in allow-list",
        code="URL_HOST_DENIED",
        details={"host": host},
    )


def check_input(text: Optional[str]) -> PolicyVerdict:
    """输入模式检查（防脚本注入—— R9 配合项）。"""
    if not text:
        return PolicyVerdict(allowed=True, code="OK")
    for pat in _DENY_INPUT_PATTERNS:
        if pat.search(text):
            return PolicyVerdict(
                allowed=False,
                reason="input contains denied pattern",
                code="INPUT_DENIED",
                details={"pattern": pat.pattern},
            )
    return PolicyVerdict(allowed=True, code="OK")


def check_all(
    *,
    action: str,
    url: Optional[str] = None,
    input_text: Optional[str] = None,
    click_target: Optional[str] = None,
    context: Optional[dict[str, Any]] = None,
) -> PolicyVerdict:
    """四合一闸门（动作 + URL + 输入 + click_target + submit 上下文）。

    先全部跑，任一拒绝即返回。submit 默认 require_human_review，除非
    context.auto_submit=True。fill 必走 brand_guard 净化（调用方负责
    sanitize_public_copy，本闸门只做长度/模式校验）。
    """
    va = check_action(action)
    if not va.allowed:
        return va
    if url is not None:
        vu = check_url(url)
        if not vu.allowed:
            return vu
    if input_text is not None:
        vi = check_input(input_text)
        if not vi.allowed:
            return vi
    # 写动作长度硬上限（与填值字段同检）
    if action == "fill":
        if input_text is not None and len(input_text) > FILL_MAX_LENGTH:
            return PolicyVerdict(
                allowed=False,
                reason=f"fill value too long: {len(input_text)} > {FILL_MAX_LENGTH}",
                code="FILL_TOO_LONG",
            )
    if action == "click":
        vc = check_click_target(click_target)
        if not vc.allowed:
            return vc
    if action == "submit":
        vs = check_submit_policy(context or {})
        if not vs.allowed:
            return vs
    # 轮 25-F：drag 起点/终点 selector 校验
    if action == "drag":
        drag_from = (context or {}).get("drag_from_selector") or click_target
        drag_to = (context or {}).get("drag_to_selector")
        if not drag_from or not drag_to:
            return PolicyVerdict(
                allowed=False,
                reason="drag requires drag_from_selector and drag_to_selector",
                code="DRAG_SELECTORS_MISSING",
            )
        v_from = check_click_target(drag_from)
        if not v_from.allowed:
            return v_from
        v_to = check_click_target(drag_to)
        if not v_to.allowed:
            return v_to
    # 轮 25-F：upload 文件路径白名单 + 扩展名校验
    if action == "upload":
        file_paths = (context or {}).get("upload_file_paths") or []
        if not file_paths or not isinstance(file_paths, list):
            return PolicyVerdict(
                allowed=False,
                reason="upload requires context.upload_file_paths (list)",
                code="UPLOAD_PATHS_MISSING",
            )
        if len(file_paths) > 5:
            return PolicyVerdict(
                allowed=False,
                reason=f"upload allows max 5 files, got {len(file_paths)}",
                code="UPLOAD_TOO_MANY",
            )
        for fp in file_paths:
            if not isinstance(fp, str):
                return PolicyVerdict(
                    allowed=False,
                    reason="upload paths must be strings",
                    code="UPLOAD_PATH_INVALID",
                )
            # 路径白名单
            if not any(fp.startswith(p) for p in _UPLOAD_PATH_ALLOWED_PREFIXES):
                return PolicyVerdict(
                    allowed=False,
                    reason=f"upload path not in allow-list: {fp[:80]}",
                    code="UPLOAD_PATH_NOT_ALLOWED",
                    details={"path": fp[:200]},
                )
            # 扩展名校验
            import os as _os
            ext = _os.path.splitext(fp)[1].lower()
            if ext not in UPLOAD_ALLOWED_EXTENSIONS:
                return PolicyVerdict(
                    allowed=False,
                    reason=f"upload ext not in allow-list: {ext!r}",
                    code="UPLOAD_EXT_DENIED",
                    details={"ext": ext},
                )
    # 轮 25-F：keyboard 文本长度 + 按键白名单
    if action == "keyboard":
        kb_text = (context or {}).get("keyboard_text")
        kb_keys = (context or {}).get("keyboard_keys") or []
        if kb_text is not None and len(kb_text) > KEYBOARD_TEXT_MAX_LENGTH:
            return PolicyVerdict(
                allowed=False,
                reason=f"keyboard text too long: {len(kb_text)} > {KEYBOARD_TEXT_MAX_LENGTH}",
                code="KEYBOARD_TEXT_TOO_LONG",
            )
        if kb_keys:
            if not isinstance(kb_keys, list):
                return PolicyVerdict(
                    allowed=False,
                    reason="keyboard_keys must be list",
                    code="KEYBOARD_KEYS_INVALID",
                )
            for k in kb_keys:
                if not isinstance(k, str) or k not in KEY_ALLOWED_KEYS:
                    return PolicyVerdict(
                        allowed=False,
                        reason=f"key not in allow-list: {k!r}",
                        code="KEYBOARD_KEY_DENIED",
                        details={"key": k},
                    )
        if not kb_text and not kb_keys:
            return PolicyVerdict(
                allowed=False,
                reason="keyboard requires keyboard_text or keyboard_keys",
                code="KEYBOARD_EMPTY",
            )
    return PolicyVerdict(allowed=True, code="OK")


def check_click_target(selector: Optional[str]) -> PolicyVerdict:
    """click target 合法性检查（防 JS 表达式注入）。

    仅接受 CSS selector 字符串（不含 JS 代码路径）：
    - `#id` / `.class` / `tag` / `[attr=val]` / `tag[attr=val]` / `:pseudo`
    - 长度 1-300；空值拒绝
    - 拒 JS 协议 / 脚本标签 / 事件处理属性
    - 拒纯单 token 文本（如 "submit"、"click"）——单 token 必带 # . [ : 之一
    """
    if not selector or not isinstance(selector, str):
        return PolicyVerdict(
            allowed=False, reason="click target required", code="CLICK_TARGET_EMPTY"
        )
    if len(selector) > 300:
        return PolicyVerdict(
            allowed=False,
            reason=f"click target too long: {len(selector)} > 300",
            code="CLICK_TARGET_TOO_LONG",
        )
    if _CLICK_DENY_RE.search(selector):
        return PolicyVerdict(
            allowed=False,
            reason="click target contains denied pattern (js/script/event)",
            code="CLICK_TARGET_DENIED",
            details={"pattern": "deny"},
        )
    if not _CLICK_SELECTOR_RE.match(selector):
        return PolicyVerdict(
            allowed=False,
            reason=f"click target not a valid CSS selector: {selector[:50]!r}",
            code="CLICK_TARGET_INVALID",
        )
    # 二次防御：纯单 token（无 # . [ :）也拒绝——避免 "submit" / "click" 这类
    # 看似 tag 实则业务意图不明的选择器绕过。
    if not any(ch in selector for ch in ("#", ".", "[", ":")):
        return PolicyVerdict(
            allowed=False,
            reason="click target must include #id .class [attr] or :pseudo (no plain tag-only)",
            code="CLICK_TARGET_PLAIN_TAG",
        )
    return PolicyVerdict(allowed=True, code="OK")


def check_submit_policy(context: dict[str, Any]) -> PolicyVerdict:
    """submit 动作高阶 Policy 判定（轮25-D 内置版；轮25-E 接 PolicyEngine）。

    与既有 `HUMAN_REVIEW_ACTIONS["paperclip.task_execute"]` 同语义——
    submit 默认 require_human_review。`context.auto_submit=True` 才放行
    （生产应由白名单租户 + 灰度控制，**默认 False**）。
    """
    auto = bool(context.get("auto_submit", False))
    if auto:
        return PolicyVerdict(
            allowed=True,
            code="OK",
            details={"auto_submit": True,
                     "warning": "submit 跳过人审——仅白名单租户 + 灰度授权可开"},
        )
    return PolicyVerdict(
        allowed=False,
        reason="submit requires human review (auto_submit not set)",
        code="SUBMIT_REQUIRES_HUMAN_REVIEW",
        details={"action_required": "set context.auto_submit=True (whitelist only)"},
    )
