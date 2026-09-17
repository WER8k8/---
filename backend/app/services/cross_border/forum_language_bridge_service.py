# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""论坛语言桥 — 英文问→中文摘要；老板中文答→英文发布草稿（FORUM-05）。"""

from __future__ import annotations

import json
import re
from typing import Any

from sqlalchemy.orm import Session

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


async def summarize_forum_question_zh(
    db: Session,
    tenant: Tenant,
    *,
    question_text: str,
    question_title: str | None = None,
) -> dict[str, Any]:
    """买家英文提问 → 老板能看的中文摘要。"""
    profile = get_tenant_product_profile(db, str(tenant.id))
    glossary = build_glossary_prompt_block(db)
    title = (question_title or "").strip()
    body = (question_text or "").strip()
    prompt = (
        "你是河北大城/河间保温建材厂的外贸助理。老板不懂英文，需要看懂论坛里的买家提问。\n"
        f"工厂: {tenant.name}\n"
        f"主营: {profile.get('primary_product') or '—'}\n"
        f"产业带: {profile.get('region_label_zh') or '廊坊大城'}\n"
        f"术语: {glossary}\n\n"
        f"问题标题: {title or '—'}\n"
        f"问题正文:\n{body}\n\n"
        "输出 JSON（无 markdown）:\n"
        '{"summary_zh":"3-5句中文摘要","detected_language":"en|zh|mixed|other",'
        '"intent_level":"高|中|低","key_asks":["要点1","2"],'
        '"suggested_reply_points":["建议回复要点（中文）"],"needs_human_review":true}'
    )
    result = await invoke_llm(
        db,
        prompt=prompt,
        scenario="inference",
        max_tokens=900,
        tenant_id=str(tenant.id),
        lane="customer",
    )
    parsed = _parse_json(str(result.get("content") or ""))
    if not parsed.get("summary_zh"):
        parsed["summary_zh"] = str(result.get("content") or "")[:800]
    parsed["human_confirm_required"] = True
    parsed["model"] = result.get("model")
    return parsed


async def draft_forum_answer_en(
    db: Session,
    tenant: Tenant,
    *,
    question_title: str,
    question_body: str,
    boss_answer_zh: str,
    tone: str = "helpful",
) -> dict[str, Any]:
    """老板中文要点 → 论坛英文回答草稿（发布前须人工确认）。"""
    profile = get_tenant_product_profile(db, str(tenant.id))
    glossary = build_glossary_prompt_block(db)
    prompt = (
        "你是建材出口业务员，帮老板在买家问答论坛写英文回复。老板只懂中文。\n"
        f"工厂: {tenant.name}\n"
        f"主营: {profile.get('primary_product') or '—'}\n"
        f"产地: {profile.get('region_label_zh') or 'Langfang, Hebei, China'}\n"
        f"术语: {glossary}\n\n"
        f"买家问题标题: {question_title.strip()}\n"
        f"买家问题正文:\n{(question_body or '').strip()}\n\n"
        f"老板要说的中文要点:\n{boss_answer_zh.strip()}\n\n"
        f"语气: {tone}，像真实工厂技术销售，诚实不夸大。\n"
        "输出 JSON:\n"
        '{"title_en":"可选短标题","body_en":"英文回答（分段）",'
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
    parsed = _parse_json(str(result.get("content") or ""))
    if not parsed.get("body_en"):
        parsed["body_en"] = str(result.get("content") or "")
    parsed["human_confirm_required"] = True
    parsed["disclaimer"] = "复制到 Answer 前请老板核对英文；平台不自动发帖。"
    parsed["model"] = result.get("model")
    return parsed
