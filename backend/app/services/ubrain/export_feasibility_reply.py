# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""出口可行性回复：避免重复提问时机械复读同一模板。"""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
import re
from typing import Any

from app.services.trade_intel_service import DISCLAIMER, FeasibilityResult

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

_SHALLOW_REPEAT_RE = re.compile(
    r"^(还是|再问|上次|刚才|能吗|可以吗|确定吗|真的吗|有没有|行不行|再说|重复)",
    re.I,
)
_EXPORT_TOPIC_IN_TEXT = re.compile(
    r"(出口|外销|卖到|发往|能出口|能不能出口|可行性)",
    re.I,
)


def _session_already_answered_export(
    recent_turns: list[dict[str, Any]] | None,
    fr: FeasibilityResult,
) -> bool:
    """_session_already_answered_export。

    参数说明：
    :param recent_turns: 参数 recent_turns
    :param fr: 参数 fr
    :return: 返回处理结果。
    """
    if not recent_turns:
        return False
    code = (fr.country_code or "").upper()
    cat = fr.category or ""
    hs = fr.hs_chapter or ""
    user_asked_export = any(
        _EXPORT_TOPIC_IN_TEXT.search(str(t.get("text") or ""))
        for t in recent_turns[-8:]
        if str(t.get("role")) == "user"
    )
    for turn in reversed(recent_turns[-8:]):
        if str(turn.get("role")) != "assistant":
            continue
        text = str(turn.get("text") or "")
        upper = text.upper()
        answered_export = bool(
            _EXPORT_TOPIC_IN_TEXT.search(text)
            or (hs and f"HS 第{hs}" in text)
            or (hs and f"第{hs}章" in text)
            or "谨慎做" in text
            or "可做" in text
            or "难度高" in text
        )
        if not answered_export and not user_asked_export:
            continue
        if code and (code in upper or f"→ {code}" in upper):
            return True
        if cat and cat in text:
            return True
    return False


def _is_shallow_repeat(message: str, last: dict[str, Any]) -> bool:
    """_is_shallow_repeat。

    参数说明：
    :param message: 参数 message
    :param last: 参数 last
    :return: 返回处理结果。
    """
    m = message.strip()
    if len(m) <= 12 and _SHALLOW_REPEAT_RE.match(m):
        return True
    prev = str(last.get("last_message") or "").strip()
    if prev and m == prev:
        return True
    return False


def _first_time_reply(fr: FeasibilityResult, *, source_note: str) -> str:
    """_first_time_reply。

    参数说明：
    :param fr: 参数 fr
    :param source_note: 参数 source_note
    :return: 返回处理结果。
    """
    certs = "、".join(fr.certs) or "见当地法规"
    lines = [
        f"【{fr.category} → {fr.country_code}】{fr.verdict_label}。",
        f"海关大类建议先按 HS 第 {fr.hs_chapter} 章核查具体税号（以材质规格为准）。",
        fr.summary.strip(),
        f"常见证照/材料：{certs}。",
    ]
    if fr.growth and fr.growth not in ("N/A", "unknown", ""):
        lines.append(f"市场体感：增速约 {fr.growth}，竞争 {fr.competition}。")
    if source_note:
        lines.append(source_note)
    lines.append("若您要往下做，可说「找该国采购商」或「写 5 封开发信」。")
    return "\n".join(line for line in lines if line)


def _followup_reply(
    message: str,
    fr: FeasibilityResult,
    *,
    ask_count: int,
    last: dict[str, Any],
) -> str:
    """_followup_reply。

    参数说明：
    :param message: 参数 message
    :param fr: 参数 fr
    :param ask_count: 参数 ask_count
    :param last: 参数 last
    :return: 返回处理结果。
    """
    code = fr.country_code or last.get("country_code") or "该国"
    verdict = fr.verdict_label or last.get("verdict_label") or "谨慎做"
    brief = (fr.summary or last.get("summary") or "")[:120]
    if _is_shallow_repeat(message, last) or len(message.strip()) <= 14:
        return (
            f"您刚问过【{fr.category} → {code}】，结论没变：{verdict}。"
            f"{brief} "
            "您更想推进哪一步？回 **1** 查证照清单，**2** 找当地采购商，**3** 生成开发信草稿（均需您确认后再对外）。"
        )

    if ask_count >= 3:
        return (
            f"关于 {code} 出口，核心仍是 {verdict}（HS 第{fr.hs_chapter}章）。"
            "为避免重复铺陈，您直接说关心「认证 / 找买家 / 报价话术」中的哪一块，我按块展开。"
        )

    return (
        f"您再次问到 {code}，和上次一致：{verdict}。"
        f"{brief} "
        "这次我可以帮您细化：① 证照与合规步骤 ② 采购商线索画像 ③ 英文开发信草稿。回复数字即可。"
    )


def _llm_polish_followup(
    message: str,
    fr: FeasibilityResult,
    draft: str,
    *,
    ask_count: int,
    last: dict[str, Any],
    recent_turns: list[dict[str, Any]] | None,
) -> str | None:
    """_llm_polish_followup。

    参数说明：
    :param message: 参数 message
    :param fr: 参数 fr
    :param draft: 参数 draft
    :param ask_count: 参数 ask_count
    :param last: 参数 last
    :param recent_turns: 参数 recent_turns
    :return: 返回处理结果。
    """
    from app.services.ai_engine import get_ai_engine
    engine = get_ai_engine()
    if not engine.is_available():
        return None

    history = ""
    if recent_turns:
        bits = []
        for t in recent_turns[-4:]:
            role = "用户" if t.get("role") == "user" else "助手"
            bits.append(f"{role}：{str(t.get('text') or '')[:200]}")
        history = "\n".join(bits)

    prompt = f"""你是建材外贸卖货助手，客户第 {ask_count} 次问同一出口话题，请不要逐字重复上一轮长文。

【上轮要点】
品类 {fr.category} → {fr.country_code}，{fr.verdict_label}，HS {fr.hs_chapter}章。
{fr.summary[:180]}

【对话摘录】
{history or "（无）"}

【客户本轮】
{message.strip()}

【草稿回复（可改写，勿加长）】
{draft}

要求：
1. 先一句承认「您刚问过/结论未变」，再给 2～3 条可选下一步（证照/找客/开发信）。
2. 语气像业务员，不要列功能菜单，不要提 UBrain/DeerFlow/Accio。
3. 120～220 字，中文。"""

    try:
        result = _safe_asyncio_run(
            engine.generate(
                prompt,
                model="chinese",
                max_tokens=400,
                task_complexity="simple",
                max_retries=1,
            )
        )
        text = str(result.get("content") or "").strip()
        return text if len(text) >= 40 else None
    except Exception as exc:
        logger.warning("export feasibility followup polish failed: %s", exc)
        return None


def build_export_feasibility_reply(
    message: str,
    fr: FeasibilityResult,
    *,
    memory: dict[str, Any] | None = None,
    recent_turns: list[dict[str, Any]] | None = None,
) -> tuple[str, dict[str, Any]]:
    """生成对用户可读回复；重复话题用跟进话术 + 可选 LLM 润色。"""
    memory = memory or {}
    last = memory.get("last_export_feasibility") or {}
    if not isinstance(last, dict):
        last = {}

    same_topic = (
        last.get("country_code") == fr.country_code
        and last.get("category") == fr.category
        and bool(fr.country_code)
    )
    session_repeat = _session_already_answered_export(recent_turns, fr)
    shallow = _is_shallow_repeat(message, last)
    ask_count = int(last.get("ask_count", 0)) + 1 if same_topic else 1
    if session_repeat and ask_count == 1:
        ask_count = 2

    source_note = (
        "（规则库暂无该国明细，以下为 AI 根据公开贸易常识补充，签约前请报关/律师确认。）"
        if fr.llm_supplemented
        else ""
    )
    is_followup = ask_count >= 2 or session_repeat or shallow
    meta: dict[str, Any] = {
        "reply_mode": "followup" if is_followup else "first",
        "ask_count": ask_count,
        "is_repeat_topic": same_topic or session_repeat or shallow,
    }
    if is_followup:
        reply = _followup_reply(message, fr, ask_count=ask_count, last=last)
        polished = _llm_polish_followup(
            message,
            fr,
            reply,
            ask_count=ask_count,
            last=last,
            recent_turns=recent_turns,
        )
        if polished:
            reply = polished
            meta["reply_mode"] = "followup_llm"
    else:
        reply = _first_time_reply(fr, source_note=source_note)

    if DISCLAIMER not in reply and (fr.llm_supplemented or not fr.matrix_hit):
        reply = f"{reply}\n\n{DISCLAIMER}"

    return reply.strip(), meta


def memory_patch_after_export(
    message: str,
    fr: FeasibilityResult,
    *,
    ask_count: int,
) -> dict[str, Any]:
    """memory_patch_after_export。

    参数说明：
    :param message: 参数 message
    :param fr: 参数 fr
    :param ask_count: 参数 ask_count
    :return: 返回处理结果。
    """
    return {
        "last_export_feasibility": {
            "category": fr.category,
            "country_code": fr.country_code,
            "verdict": fr.verdict,
            "verdict_label": fr.verdict_label,
            "hs_chapter": fr.hs_chapter,
            "summary": (fr.summary or "")[:240],
            "ask_count": ask_count,
            "last_message": message.strip()[:120],
        },
    }
