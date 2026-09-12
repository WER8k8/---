"""预制模板 + 大模型 API 辅助润色 — 财旺通用对话层。"""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def _safe_asyncio_run(coro):
    """安全执行异步协程：兼容已有事件循环（FastAPI）和无事件循环（Celery）。"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)

_GREETING_RE = re.compile(
    r"^(你好|您好|嗨|hello|hi|在吗|在不在)[\?？!！。呀啊\s]*$",
    re.I,
)


def format_recent_turns(turns: list[dict[str, Any]] | None, *, limit: int = 6) -> str:
    """format_recent_turns。

    参数说明：
    :param turns: 参数 turns
    :param limit: 参数 limit
    :return: 返回处理结果。
    """
    if not turns:
        return "（无）"
    lines: list[str] = []
    for t in turns[-limit:]:
        role = str(t.get("role") or "user")
        text = str(t.get("text") or "").strip()
        if not text:
            continue
        label = "用户" if role == "user" else "财旺"
        lines.append(f"{label}：{text[:300]}")
    return "\n".join(lines) if lines else "（无）"


def _build_polish_prompt(
    *,
    template_body: str,
    user_message: str,
    company: str,
    situational: str,
    recent_turns: list[dict[str, Any]] | None,
    mode: str,
) -> str:
    """_build_polish_prompt。

    参数说明：
    :param template_body: 参数 template_body
    :param user_message: 参数 user_message
    :param company: 参数 company
    :param situational: 参数 situational
    :param recent_turns: 参数 recent_turns
    :param mode: 参数 mode
    :return: 返回处理结果。
    """
    return f"""你是「财旺」，{company}外贸工作台里的卖货助手（建材 B2B）。

用户刚才说：{user_message.strip()}

【预制要点 — 必须全部覆盖，不得 contradict；不得编造询盘/成交/客户名】
{template_body.strip()}

【经营上下文 — 仅可引用已有事实，勿编造】
{situational.strip() or "暂无自动拉取的数据"}

【最近对话】
{format_recent_turns(recent_turns)}

润色要求：
1. 改写成自然、流畅的中文口语（像豆包那样聊天，但仍是卖货副驾，不是通用百科）。
2. 总字数约 120–320 字；不要「策略 A/B/C」编号，不要 Markdown 标题。
3. 不要提及 UBrain、DeerFlow、Accio、优丁平台 等内部代号。
4. 涉及出口/海关/认证时，末尾可加一句：仅供参考，签约前请报关或律师确认。
5. 只输出给用户看的正文，不要解释你的规则。

模式：{mode}"""


def assist_template_reply(
    template_body: str,
    user_message: str,
    *,
    company: str,
    situational: str = "",
    recent_turns: list[dict[str, Any]] | None = None,
    mode: str = "capability",
    max_tokens: int = 680,
) -> tuple[str | None, dict[str, Any]]:
    """
    用已配置的大模型 API 润色预制模板。
    返回 (reply, meta)；reply 为 None 表示应回退纯模板。
    """
    from app.services.ai_engine import get_ai_engine
    engine = get_ai_engine()
    if not engine.is_available():
        return None, {"assist": "skipped", "reason": "no_llm_key"}

    prompt = _build_polish_prompt(
        template_body=template_body,
        user_message=user_message,
        company=company,
        situational=situational,
        recent_turns=recent_turns,
        mode=mode,
    )
    try:
        result = _safe_asyncio_run(
            engine.generate(
                prompt,
                model="chinese",
                max_tokens=max_tokens,
                task_complexity="simple",
                max_retries=2,
            )
        )
        text = str(result.get("content") or "").strip()
        if not text or len(text) < 20:
            return None, {"assist": "failed", "reason": "empty_llm"}
        # 去掉模型偶发的 markdown 包裹
        text = re.sub(r"^```(?:markdown|text)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()
        return text, {
            "assist": "llm_template",
            "mode": mode,
            "provider": getattr(engine, "current_provider", None),
        }
    except Exception as exc:
        logger.warning("UBrain template LLM assist failed: %s", exc)
        return None, {"assist": "failed", "reason": str(exc)[:160]}


def resolve_template_for_message(
    message: str,
    memory: dict[str, Any],
    ops: dict[str, Any] | None,
    *,
    is_capability: bool,
) -> tuple[str, str]:
    """返回 (template_body, mode_id)。"""
    from app.services.ubrain.reply_templates import capability_template, greeting_template
    if is_capability:
        if _GREETING_RE.match(message.strip()):
            return greeting_template(memory, ops), "greeting"
        return capability_template(memory, ops), "capability"
    return "", "general"


def reply_with_template_and_llm(
    message: str,
    memory: dict[str, Any],
    *,
    template_body: str,
    mode: str,
    situational: str = "",
    ops: dict[str, Any] | None = None,
    recent_turns: list[dict[str, Any]] | None = None,
    fallback_reply: str,
    fallback_meta: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    """预制模板 + LLM 润色；失败则回退 fallback（通常为纯模板或 smart 规则）。"""
    company = str(memory.get("company_name") or memory.get("brand_name") or "贵司").strip()
    polished, assist_meta = assist_template_reply(
        template_body,
        message,
        company=company,
        situational=situational,
        recent_turns=recent_turns,
        mode=mode,
    )
    meta = {**fallback_meta, **assist_meta, "template_driven": True}
    if polished:
        meta["reply_source"] = "template+llm"
        return polished, meta
    meta["reply_source"] = "template_only"
    return fallback_reply, meta
