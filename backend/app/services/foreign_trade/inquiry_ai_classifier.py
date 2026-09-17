# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""询盘 AI 智能分级 —— §7 缺口补齐。

在既有 MEDDPICC 规则评分（inquiry_meddpicc_service）之上，做三级评分
+ 自动标签 + 可选 AI 意图增强：

- 纯规则路径（默认，method="rule"）无 LLM 依赖，可离线跑通
- 配置真实 LLM 且 use_ai=True 时，用 get_ai_engine().generate() 做意图增强
  （method="ai"），失败自动降级回规则结果，绝不假成功
- 结果落进 Inquiry.meddpicc_json（沿用 load/save_meddpicc，不新加表）
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field, asdict
from typing import Any, Optional

from app.services.foreign_trade.inquiry_meddpicc_service import score_inquiry_meddpicc

logger = logging.getLogger(__name__)


# ── 数据源可信度（MQL 来源加权）────────────────────────────────
_CHANNEL_CREDIBILITY: dict[str, float] = {
    "whatsapp": 0.9,
    "linkedin": 0.85,
    "email": 0.8,
    "webform": 0.7,
    "chat": 0.75,
    "facebook": 0.6,
    "other": 0.5,
}

# 信息完整度字段（询盘里带了这些才算"有内容"）
_COMPLETENESS_KEYS = (
    "message", "company_name", "country", "quantity",
    "product", "budget", "delivery_date",
)

# 购买意图信号关键词（SQL 强弱）
_INTENT_KEYWORDS: list[tuple[str, int]] = [
    (r"\bMOQ\b|最小起订", 20),
    (r"price|单价|\bUSD\b|报价|quote", 15),
    (r"spec|规格|认证|ISO|CE", 10),
    (r"delivery|交期|ship|发货", 10),
    (r"sample|样品|打样", 8),
    (r"order|订单|采购|purchase|qty|数量", 15),
    (r"contract|合同|PI|PO", 12),
    (r"payment|付款|T/T|信用证", 8),
]

# 紧迫度关键词
_URGENCY_KEYWORDS = [
    "urgent", "ASAP", "immediately", "急需", "尽快", "this week",
    "本周", "急单", "rushed", "expedite",
]

# 行业标签关键词
_INDUSTRY_TAGS: dict[str, list[str]] = {
    "building_materials": ["concrete", "保温", "建材", "insulation", "cement", "瓷砖", "tile", "钢结构"],
    "hardware": ["五金", "hardware", "工具", "tool", "阀门", "valve"],
    "decor": ["装饰", "decor", "窗帘", "curtain", "灯饰", "lighting"],
    "machinery": ["机械", "machinery", "设备", "machine", "equipment"],
    "textile": ["纺织", "textile", "面料", "fabric", "服装", "garment"],
}

# 紧迫度关键词
_LANGUAGE_HINTS: dict[str, re.Pattern] = {
    "en": re.compile(r"[a-zA-Z]{4,}"),
    "zh": re.compile(r"[一-鿿]{2,}"),
}


@dataclass
class Classification:
    """询盘 AI 分级结果。"""
    mql_score: int
    sql_score: int
    priority_tier: str  # hot / warm / cold / nuisance
    industry_tag: str
    urgency_tag: bool
    language_preference: str
    method: str  # "rule" 或 "ai"
    intent_summary: str = ""
    tags: dict[str, Any] = field(default_factory=dict)

    def to_meta(self) -> dict[str, Any]:
        """落库用（存进 meddpicc_json 的 'ai_classify' 子块）。"""
        return {"ai_classify": asdict(self)}


def _extract_text_fields(inquiry) -> tuple[str, dict[str, Any]]:
    """从 Inquiry 或 dict 里取出可用于分级的文本 + 结构化字段。"""
    if isinstance(inquiry, dict):
        return str(inquiry.get("message") or ""), dict(inquiry)
    data: dict[str, Any] = {}
    for k in _COMPLETENESS_KEYS:
        v = getattr(inquiry, k, None)
        if v is not None:
            data[k] = v
    return str(getattr(inquiry, "message", "") or ""), data


def _score_mql(source_channel: Optional[str], data: dict[str, Any]) -> int:
    """MQL：来源可信度(40%) + 信息完整度(60%)，0-100。"""
    cred = _CHANNEL_CREDIBILITY.get((source_channel or "").lower(), 0.5)
    filled = sum(1 for k in _COMPLETENESS_KEYS if str(data.get(k) or "").strip())
    completeness = min(1.0, filled / 5.0)
    return int(round((cred * 0.4 + completeness * 0.6) * 100))


def _score_sql(message: str) -> int:
    """SQL：购买意图信号强度，0-100（关键词命中加权求和封顶）。"""
    text = (message or "")
    total = 0
    for pat, weight in _INTENT_KEYWORDS:
        if re.search(pat, text, re.IGNORECASE):
            total += weight
    return min(100, total)


def _priority_tier(mql: int, sql: int, message: str) -> str:
    """组合 MQL/SQL + 噪音信号 → hot/warm/cold/nuisance。"""
    low = (message or "").lower()
    # 垃圾信号：纯垃圾邮件/招聘/无关
    if re.search(r"(work from home|crypto airdrop|resume|hiring|中奖|lottery)", low):
        return "nuisance"
    if mql >= 60 and sql >= 50:
        return "hot"
    if mql >= 50 or sql >= 40:
        return "warm"
    if mql >= 30 or sql >= 20:
        return "cold"
    return "nuisance"


def _detect_urgency(message: str) -> bool:
    return any(k.lower() in (message or "").lower() for k in _URGENCY_KEYWORDS)


def _detect_industry(message: str, data: dict[str, Any]) -> str:
    text = " ".join([message or ""] + [str(v) for v in data.values() if isinstance(v, str)]).lower()
    best, best_hits = "unknown", 0
    for tag, kws in _INDUSTRY_TAGS.items():
        hits = sum(1 for kw in kws if kw.lower() in text)
        if hits > best_hits:
            best, best_hits = tag, hits
    return best if best_hits else "unknown"


def _detect_language(message: str) -> str:
    zh = len(_LANGUAGE_HINTS["zh"].findall(message or ""))
    en = len(_LANGUAGE_HINTS["en"].findall(message or ""))
    if zh == 0 and en == 0:
        return "unknown"
    return "zh" if zh >= en else "en"


def _classify_by_rule(inquiry, source_channel: Optional[str], use_ai: bool, db=None) -> Classification:
    message, data = _extract_text_fields(inquiry)
    sc = source_channel or (data.get("source_channel") if isinstance(inquiry, dict) else getattr(inquiry, "source_channel", None))

    mql = _score_mql(sc, data)
    sql = _score_sql(message)
    tier = _priority_tier(mql, sql, message)
    urgency = _detect_urgency(message)
    industry = _detect_industry(message, data)
    lang = _detect_language(message)

    # MEDDPICC 规则分（既有能力，作为补充）
    med = score_inquiry_meddpicc(inquiry, auto_extract=True)
    med_score = int(med.get("score") or 0)
    sql = max(sql, med_score)  # 取两者较强

    # 可选 AI 意图增强（失败降级，绝不假成功）
    method = "rule"
    intent_summary = ""
    if use_ai:
        method, intent_summary = _ai_enhance(message, db=db)

    return Classification(
        mql_score=mql,
        sql_score=min(100, sql),
        priority_tier=tier,
        industry_tag=industry,
        urgency_tag=urgency,
        language_preference=lang,
        method=method,
        intent_summary=intent_summary,
        tags={
            "meddpicc_level": med.get("level"),
            "meddpicc_fields_filled": med.get("fields_filled", 0),
        },
    )


def _ai_enhance(message: str, *, db=None) -> tuple[str, str]:
    """尝试 AI 意图提取；返回 (method, intent_summary)。任何异常都降级为 rule。"""
    try:
        import asyncio
        from app.services.ai_engine import get_ai_engine

        engine = get_ai_engine()
        if not engine.is_available():
            return "rule", ""
        prompt = (
            "你是外贸询盘意图分析助手。判断这条询盘的核心意图与优先处理理由，"
            "一句话中文总结（<=40字）。若信息太少就如实说明。\n询盘原文：\n"
            f"{(message or '')[:800]}"
        )
        resp = asyncio.run(engine.generate(prompt, model="general", max_tokens=80))
        text = str(resp).strip()
        if text:
            return "ai", text[:120]
        return "rule", ""
    except Exception as exc:  # noqa: BLE001 — AI 失败必须降级，不得阻断分级
        logger.warning("[InquiryAI] ai enhance failed, fallback to rule: %s", exc)
        return "rule", ""


def classify_inquiry(
    inquiry,
    *,
    use_ai: bool = False,
    db=None,
    source_channel: Optional[str] = None,
) -> Classification:
    """对外入口：对单条询盘做智能分级。

    :param inquiry: Inquiry 实例或 dict（含 message/source_channel 等）
    :param use_ai: 是否启用 LLM 意图增强（默认关，纯规则）
    :param db: 供 AI 增强使用（可选）
    """
    return _classify_by_rule(inquiry, source_channel=source_channel, use_ai=use_ai, db=db)


def persist_classification(inquiry, classification: Classification, db) -> dict[str, Any]:
    """把分级结果写进 Inquiry.meddpicc_json 的 'ai_classify' 块（复用既有存法）。"""
    from app.services.foreign_trade.inquiry_meddpicc_service import load_meddpicc, save_meddpicc

    meta = load_meddpicc(inquiry)
    meta["ai_classify"] = classification.to_meta()["ai_classify"]
    return save_meddpicc(db, inquiry, meta)


def get_classification(inquiry) -> Optional[Classification]:
    """从已存 meddpicc_json 读回分级结果。"""
    from app.services.foreign_trade.inquiry_meddpicc_service import load_meddpicc

    raw = load_meddpicc(inquiry).get("ai_classify")
    if not raw or not isinstance(raw, dict):
        return None
    valid = {k: raw.get(k) for k in Classification.__dataclass_fields__ if k in raw}
    return Classification(**valid)
