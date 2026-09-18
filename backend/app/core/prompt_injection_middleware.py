# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Prompt 注入检测 ASGI 中间件。

功能：
- 拦截 POST/PUT 请求，扫描 body 中的注入模式
- 命中则记录安全事件审计日志并返回 403
- 通过环境变量 PROMPT_INJECTION_MID_ENABLED 控制开关（默认 dev 开启）
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger(__name__)


# ── 正则模式（从 negotiation.py 复制并扩展 3 条）──────────────────────
_PROMPT_INJECTION_PATTERNS: list = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|system)\s+(instructions|rules|prompts|constraints)", re.IGNORECASE),
    re.compile(r"(reveal|tell\s+me|output|leak|disclose)\s+.*?(system\s*prompt|floor\s*price|bottom\s*price|cost|margin)", re.IGNORECASE),
    re.compile(r"(jailbreak|dan\s+mode|developer\s+mode|act\s+as\s+unrestricted)", re.IGNORECASE),
    re.compile(r"忽略.*?(规则|提示词|指令|约束|设定)", re.IGNORECASE),
    re.compile(r"(告诉我|透露|坦白|输出|提供).*?(底价|成本|内部价格|利润率|系统提示词)", re.IGNORECASE),
    re.compile(r"(突破限制|解除权限|无视设定|越狱模式)", re.IGNORECASE),
    # 新增 3 条
    re.compile(r"(pretend\s+you\s+are|roleplay\s+as|fake\s+as)\s+.*(admin|root|superuser|administrator)", re.IGNORECASE),
    re.compile(r"(encrypt|encode|base64|hexdump)\s+.*?(prompt|instructions|system|content)", re.IGNORECASE),
    re.compile(r"(detailed?\s+instruction|full\s+prompt|complete\s+text)\s*[:：]\s*\n?(\[|^|[\u4e00-\u9fff])", re.IGNORECASE),
]

_ACTION = "PROMPT_INJECTION_BLOCKED"
_RESOURCE_TYPE = "security_event"


def _should_run() -> bool:
    """判断当前环境是否启用中间件。"""
    import os
    flag = "PROMPT_INJECTION_MID_ENABLED"
    raw = os.environ.get(flag)
    if raw is not None:
        return raw.strip().lower() in ("1", "true", "yes", "y")
    env = os.environ.get("ENVIRONMENT", "development").lower()
    return env in ("development", "test", "dev")


def detect_injection(text: str) -> bool:
    """对外暴露的纯函数：判断一段文本是否命中 Prompt 注入模式。

    供中间件、单测、以及其它 AI 入口（谈判/聊天）复用，避免逻辑散落。
    """
    if not text:
        return False
    return any(p.search(text) for p in _PROMPT_INJECTION_PATTERNS)


class PromptInjectionMiddleware:
    """ASGI 中间件：检测并拦截 Prompt 注入攻击。"""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if _should_run() is False:
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "").upper()
        if method not in ("POST", "PUT"):
            await self.app(scope, receive, send)
            return

        # 读取 body
        body_bytes = b""
        body_parts: list = []
        more_body = True
        while more_body:
            message = await receive()
            body_parts.append(message.get("body", b""))
            more_body = message.get("more_body", False)
        body_bytes = b"".join(body_parts)

        # 无论是否命中，都必须把 body 回放给下游——
        # 否则空 body / 非字符串 JSON 在已抽干 receive 后，带 Body 参数的路由会永久挂起。
        async def _replay_receive() -> dict:
            return {
                "type": "http.request",
                "body": body_bytes,
                "more_body": False,
            }

        # 解析内容
        text_to_scan: str = ""
        try:
            parsed = json.loads(body_bytes) if body_bytes else {}
            if isinstance(parsed, dict):
                text_to_scan = " ".join(
                    str(v) for v in parsed.values()
                    if isinstance(v, (str, int, float, bool))
                )
            elif isinstance(parsed, str):
                text_to_scan = parsed
        except Exception:
            text_to_scan = body_bytes.decode("utf-8", errors="replace")

        if not text_to_scan:
            await self.app(scope, _replay_receive, send)
            return

        # 扫描注入模式（复用对外纯函数 detect_injection，避免逻辑散落）
        if detect_injection(text_to_scan):
            hit_patterns = [p.pattern[:80] for p in _PROMPT_INJECTION_PATTERNS if p.search(text_to_scan)]
            logger.warning(
                "[Security] 拦截 Prompt 注入 path=%s patterns=%s",
                scope.get("path"),
                hit_patterns[:2],
            )
            try:
                from app.core.database import SessionLocal
                from app.services.security_event_service import log_security_event
                db = SessionLocal()
                try:
                    log_security_event(
                        db,
                        action=_ACTION,
                        detail={
                            "path": scope.get("path", ""),
                            "method": method,
                            "matched_patterns": hit_patterns,
                        },
                    )
                    db.commit()
                finally:
                    db.close()
            except Exception as exc:
                logger.warning("[Security] 写入安全审计日志失败: %s", exc)

            resp_body = json.dumps({"detail": "Prompt injection detected and blocked"}).encode()
            await send({
                "type": "http.response.start",
                "status": 403,
                "headers": [(b"content-type", b"application/json")],
            })
            await send({
                "type": "http.response.body",
                "body": resp_body,
            })
            return

        await self.app(scope, _replay_receive, send)
