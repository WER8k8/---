# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""获客回复意图判断 — 规则优先，诚实 unknown。

傻子都行：给意图 + 建议阶段 + 下一步；不编造。
"""
from __future__ import annotations

import re
from typing import Any

# 意图 → (stage, next_action, talk_track, keywords)
_INTENT_RULES: list[tuple[str, str, str, str, list[str]]] = [
    (
        "reject_competitor",
        "lost_risk",
        "标记流失风险；1–2 周后再触达或换联系人",
        "勿刷屏降价；问清输给谁、哪一项，记录流失因果。",
        ["别家", "已订", "已采购", "不要了", "不需要", "competitor", "already ordered", "not interested"],
    ),
    (
        "payment_discuss",
        "negotiating",
        "确认付款方式与定金比例；写入 PI 条款",
        "新客常见 T/T 定金；全款需核验实力；条款进书面。",
        ["付款", "定金", "t/t", "tt ", "信用证", "l/c", "lc ", "payment", "deposit", "账期", "全款"],
    ),
    (
        "cert_insist",
        "qualifying",
        "确认认证清单（SASO/CE等）并准备资质文件",
        "无证不宣称有证；发已有证书扫描件与检测报告。",
        ["认证", "saso", "ce ", "iso", "证书", "检测", "certificate", "compliance"],
    ),
    (
        "request_sample",
        "sampling",
        "确认样品规格/费用/快递；登记寄样",
        "先确认样品规格再寄样；样品费用与运费归属写清楚。",
        ["样品", "sample", "寄样", "打样", "免费样"],
    ),
    (
        "request_quote",
        "quoted",
        "补齐资格四问后出正式报价（量/港/术语/认证）",
        "无数量港口只报区间；有数据再出明细报价。",
        ["报价", "价格", "多少钱", "quote", "price", "cost", "offer", "cif", "fob"],
    ),
    (
        "price_haggling",
        "negotiating",
        "压价换条件（量/付款/交期），勿白降价",
        "用条件换让步：量↑、付款更安全、交期放宽。",
        ["便宜", "降价", "折扣", "discount", "贵了", "太高", "lower price"],
    ),
    (
        "quantity_port",
        "qualifying",
        "确认数量与港口后进入报价",
        "数量港口是报价前提，先问清再报。",
        ["多少", "吨", "平方", "柜", "港口", "吉达", "jeddah", "quantity", "container", "port", "moq"],
    ),
    (
        "generic_interest",
        "engaged",
        "24h 内专业回复：资格四问 + 一页产品证据",
        "先问量/港/认证/付款，再给针对性资料。",
        ["感兴趣", "合作", "采购", "进口", "import", "buy", "interested", "cooperation", "询价"],
    ),
]


def classify_reply(text: str, country: str = "") -> dict[str, Any]:
    """规则意图分类。无命中 → unknown，不编造。"""
    raw = (text or "").strip()
    low = raw.lower()
    if not low:
        return {
            "intent": "unknown",
            "stage_suggestion": "engaged",
            "confidence": 0.0,
            "reason": "空消息",
            "next_action": "请补充客户原话后再判断",
            "talk_track": "资格四问：数量 / 港口 / 认证 / 付款。",
        }

    best = None
    best_hits = 0
    best_kw: list[str] = []
    for intent, stage, action, track, kws in _INTENT_RULES:
        hits = [k for k in kws if k.lower() in low]
        if len(hits) > best_hits:
            best = (intent, stage, action, track)
            best_hits = len(hits)
            best_kw = hits
        elif len(hits) == best_hits and hits and best is None:
            best = (intent, stage, action, track)
            best_kw = hits

    if not best:
        return {
            "intent": "unknown",
            "stage_suggestion": "engaged",
            "confidence": 0.2,
            "reason": "未命中已知意图关键词",
            "next_action": "24h 内回复：资格四问（数量/港口/认证/付款）",
            "talk_track": "先确认需求细节，再谈价格与交期。",
        }

    intent, stage, action, track = best
    conf = min(0.95, 0.45 + 0.15 * best_hits)
    return {
        "intent": intent,
        "stage_suggestion": stage,
        "confidence": round(conf, 2),
        "reason": f"命中关键词: {', '.join(best_kw[:5])}",
        "next_action": action,
        "talk_track": track,
    }
