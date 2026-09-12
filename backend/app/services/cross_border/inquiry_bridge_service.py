"""询盘语言桥 — 外文询盘→中文摘要；老板中文→英文回复草稿（W2 / XF-C1/C2）。"""

from __future__ import annotations

import json
import re
from typing import Any

from sqlalchemy.orm import Session

from app.core.no_fake_delivery import is_mock_payload
from app.models.inquiry import Inquiry
from app.models.tenant import Tenant
from app.services.ai_invocation_service import invoke_llm
from app.services.cross_border.glossary_helper import build_glossary_prompt_block
from app.services.tenant_product_profile_service import get_tenant_product_profile

_JSON_BLOCK = re.compile(r"\{[\s\S]*\}")


def _parse_json(text: str) -> dict[str, Any]:
    """实现 解析JSON 的功能。
    
    :param text: 参数 text（类型: str）
    :return: 返回 dict[str, Any] 结果
    """
    raw = (text or "").strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        pass
    match = _JSON_BLOCK.search(raw)
    if match:
        try:
            data = json.loads(match.group(0))
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            pass
    return {}


def _inquiry_context(inquiry: Inquiry) -> str:
    """实现 inquirycontext 的功能。
    
    :param inquiry: 参数 inquiry（类型: Inquiry）
    :return: 返回 str 结果
    """
    parts = [
        f"联系人: {inquiry.name or '—'}",
        f"邮箱: {inquiry.email or '—'}",
        f"电话: {inquiry.phone or '—'}",
        f"意向产品: {inquiry.product or '—'}",
        f"来源: {inquiry.source_channel or '—'}",
        f"留言:\n{inquiry.message or ''}",
    ]
    return "\n".join(parts)


async def summarize_inquiry_zh(
    db: Session,
    tenant: Tenant,
    inquiry: Inquiry,
) -> dict[str, Any]:
    """把外文/混合语种询盘翻成老板能看的中文摘要。"""
    profile = get_tenant_product_profile(db, str(tenant.id))
    glossary = build_glossary_prompt_block(db)
    prompt = (
        "你是河北大城/河间保温建材厂的外贸助理。老板不懂英文，需要中文摘要。\n"
        f"工厂主营: {profile.get('primary_product') or tenant.name}\n"
        f"产业带: {profile.get('region_label_zh') or '廊坊大城'}\n"
        f"术语对照: {glossary}\n\n"
        "询盘原文:\n"
        f"{_inquiry_context(inquiry)}\n\n"
        "请输出 JSON（不要 markdown 代码块）:\n"
        '{"summary_zh":"3-5句中文摘要","buyer_language":"en|zh|mixed|other",'
        '"intent_level":"高|中|低","key_asks":["买家要什么1","2"],'
        '"suggested_next":"24小时内建议动作（中文）","needs_phone_call":true}'
    )
    result = await invoke_llm(
        db,
        prompt=prompt,
        scenario="inference",
        max_tokens=900,
        tenant_id=str(tenant.id),
        lane="customer",
    )
    if is_mock_payload(result):
        return {
            "summary_zh": (
                "[dev mock · 未接 LLM] "
                f"联系人 {inquiry.name or '—'}；留言节选：{(inquiry.message or '')[:280]}"
            ),
            "buyer_language": "unknown",
            "intent_level": "待评估",
            "key_asks": ["请配置 AI Key 后重新生成真实摘要"],
            "suggested_next": "配置 AI_NVIDIA_API_KEY 或 DeepSeek Key 后点击「中文摘要」",
            "needs_phone_call": False,
            "human_confirm_required": True,
            "mode": "mock",
            "mock_reason": result.get("mock_reason") or "ai_engine_not_configured",
            "disclaimer": "此为占位摘要，非真实翻译；禁止当作已读懂外商询盘。",
        }
    parsed = _parse_json(str(result.get("content") or ""))
    if not parsed.get("summary_zh"):
        parsed["summary_zh"] = str(result.get("content") or "")[:800]
    parsed["human_confirm_required"] = True
    parsed["model"] = result.get("model")
    if result.get("mode"):
        parsed["mode"] = result.get("mode")
    return parsed


async def draft_reply_en(
    db: Session,
    tenant: Tenant,
    inquiry: Inquiry,
    *,
    boss_reply_zh: str,
    tone: str = "professional",
) -> dict[str, Any]:
    """老板用中文说要点 → 生成英文回复草稿（发送前须人工确认）。"""
    profile = get_tenant_product_profile(db, str(tenant.id))
    glossary = build_glossary_prompt_block(db)
    prompt = (
        "你是建材出口业务员，帮老板写英文邮件回复。老板只懂中文。\n"
        f"工厂: {tenant.name}\n"
        f"主营: {profile.get('primary_product') or '—'}\n"
        f"产地: {profile.get('region_label_zh') or 'Langfang, Hebei, China'}\n"
        f"术语: {glossary}\n\n"
        "询盘背景:\n"
        f"{_inquiry_context(inquiry)}\n\n"
        f"老板要说的中文要点:\n{boss_reply_zh.strip()}\n\n"
        f"语气: {tone}\n"
        "要求: 诚实不夸大；MOQ/交期/认证没给的不编造；可礼貌追问缺失信息。\n"
        "输出 JSON:\n"
        '{"subject_en":"邮件主题","body_en":"英文正文（分段）",'
        '"body_zh_backtranslation":"中文回译供老板核对","missing_info":["还缺什么"]}'
    )
    result = await invoke_llm(
        db,
        prompt=prompt,
        scenario="inference",
        max_tokens=1200,
        tenant_id=str(tenant.id),
        lane="customer",
    )
    if is_mock_payload(result):
        return {
            "subject_en": f"Re: {inquiry.product or 'your inquiry'}",
            "body_en": (
                "[dev mock · AI not configured]\n"
                "Please configure an AI provider key to generate a real English draft.\n"
                f"Boss notes (ZH): {boss_reply_zh.strip()[:500]}"
            ),
            "body_zh_backtranslation": boss_reply_zh.strip()[:500],
            "missing_info": ["AI Key", "MOQ", "lead time"],
            "human_confirm_required": True,
            "mode": "mock",
            "mock_reason": result.get("mock_reason") or "ai_engine_not_configured",
            "disclaimer": "占位草稿，禁止直接发送；配置 AI Key 后重新生成。",
        }
    parsed = _parse_json(str(result.get("content") or ""))
    if not parsed.get("body_en"):
        parsed["body_en"] = str(result.get("content") or "")
    parsed["human_confirm_required"] = True
    parsed["disclaimer"] = "发送前请老板核对英文，平台不代发。"
    parsed["model"] = result.get("model")
    if result.get("mode"):
        parsed["mode"] = result.get("mode")
    return parsed


def _key_configured(value: str | None) -> bool:
    """实现 键configured 的功能。
    
    :param value: 参数 value（类型: str | None）
    :return: 返回 bool 结果
    """
    raw = (value or "").strip()
    if not raw:
        return False
    if raw.startswith("__SET") or raw.startswith("__PLACEHOLDER"):
        return False
    return True


def inquiry_bridge_status() -> dict[str, Any]:
    """XF-C1/C2 语言桥 LLM 就绪态（只读）。"""
    from app.core.config import settings
    from app.services.ubrain.imap_inquiry_sidecar import imap_inquiry_sidecar_status
    providers: list[str] = []
    checks = (
        ("nvidia", settings.AI_NVIDIA_API_KEY),
        ("deepseek", settings.AI_DEEPSEEK_API_KEY),
        ("openai", settings.AI_OPENAI_API_KEY),
        ("anthropic", settings.AI_ANTHROPIC_API_KEY),
        ("gemini", settings.AI_GEMINI_API_KEY),
        ("siliconflow", settings.AI_SILICONFLOW_API_KEY),
    )
    for name, key in checks:
        if _key_configured(key):
            providers.append(name)
    configured = bool(providers)
    imap_st = imap_inquiry_sidecar_status()
    return {
        "configured": configured,
        "providers_available": providers,
        "mode": "live" if configured else "mock",
        "features": ["bridge_summary", "reply_draft"],
        "human_confirm_required": True,
        "imap_inquiry": imap_st,
        "disclaimer": (
            None
            if configured
            else "未检测到可用 AI Key；摘要/英文草稿为 dev mock，禁止当作真实翻译发送。"
        ),
        "env_hints": [
            "AI_NVIDIA_API_KEY",
            "AI_DEEPSEEK_API_KEY",
            "AI_OPENAI_API_KEY",
        ],
    }
