# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""编排词典 v1（P1-9）— 已验证 abc 航道（≥8 条）。

每条 = 意图 + 节点顺序(abc) + 必选节点 + 人审点 + 大白话用途。
与 hermes planner L1 模板对齐，作作战台「智能拆解」旁的词典。
"""
from __future__ import annotations

from typing import Any

DICTIONARY: list[dict[str, Any]] = [
    {
        "id": "route-find-leads",
        "name": "主动拓客开发信",
        "intent": "find_leads",
        "order": "abc",
        "order_label": "a找线索 → b背调评分 → c开发信(人审)",
        "nodes": ["lead.search", "prospect.enrich", "lead.score", "outreach.letter"],
        "must": ["prospect.enrich", "lead.score", "outreach.letter"],
        "human_review": ["outreach.letter"],
        "scene": "建材外贸主动获客主航道",
        "plain": "先找到人，查清楚再写信；首封必须人审，禁止无背调个性化。",
    },
    {
        "id": "route-fulfillment",
        "name": "履约闭环：询盘到尾款",
        "intent": "fulfillment",
        "order": "abcd",
        "order_label": "a询盘 → b报价/PI → c定金跟单 → d物流尾款",
        "nodes": [
            "inquiry.capture",
            "quote.boq",
            "pi.generate",
            "crm.stage",
            "logistics.track",
            "payment.balance",
        ],
        "must": ["quote.boq", "pi.generate", "payment.balance"],
        "human_review": ["pi.generate"],
        "scene": "成交后七步履约节点进跟单卡",
        "plain": "报价→PI→定金→生产→发货→尾款；节点状态进跟单卡并提醒到期。",
    },
    {
        "id": "route-whatsapp-social",
        "name": "社媒/WhatsApp 拓客",
        "intent": "whatsapp",
        "order": "abc",
        "order_label": "a采集 → b背调 → cWA触达(人审)+意图",
        "nodes": ["prospect.scrape", "prospect.enrich", "outreach.whatsapp", "intent.classify"],
        "must": ["prospect.enrich", "outreach.whatsapp"],
        "human_review": ["outreach.whatsapp"],
        "scene": "社媒与 WA 矩阵拓客",
        "plain": "先采线索再背调，WA 外发人审；回复进意图分类与跟单卡。",
    },
    {
        "id": "route-inquiry-reply",
        "name": "询盘秒回转化",
        "intent": "inquiry_reply",
        "order": "abc",
        "order_label": "a捕获进线 → b买家背调 → c回复草稿(人审)",
        "nodes": ["inquiry.capture", "prospect.enrich", "outreach.reply"],
        "must": ["inquiry.capture", "outreach.reply"],
        "human_review": ["outreach.reply"],
        "scene": "被动询盘转化",
        "plain": "进线先建档背调，再出回复草稿；身份锁保证全渠道同一个人设。",
    },
    {
        "id": "route-sample-flow",
        "name": "样品跟进航道",
        "intent": "sample_followup",
        "order": "abc",
        "order_label": "a要样 → b费用/规格确认 → c寄样追踪",
        "nodes": ["ops.sample_request", "ops.sample_confirm", "ops.sample_ship", "ops.sample_chase"],
        "must": ["ops.sample_confirm", "ops.sample_ship"],
        "human_review": ["ops.sample_ship"],
        "scene": "客户索样后的标准动作",
        "plain": "样品规格费用先写清，再寄；单号进跟单卡，防样品黑洞。",
    },
    {
        "id": "route-price-negotiation",
        "name": "议价换条件",
        "intent": "price_haggling",
        "order": "abc",
        "order_label": "a识别压价 → b条件交换清单 → c重报/坚持",
        "nodes": ["intent.classify", "negotiation.conditions", "quote.revise"],
        "must": ["intent.classify", "negotiation.conditions"],
        "human_review": ["quote.revise"],
        "scene": "客户嫌贵时的标准应对",
        "plain": "勿白降价；用数量/付款/交期换让步，改价仍要人审。",
    },
    {
        "id": "route-loss-winback",
        "name": "流失挽回",
        "intent": "winback",
        "order": "abc",
        "order_label": "a记流失原因 → b冷却期 → c轻触达",
        "nodes": ["ops.loss_reason", "experience.feed", "outreach.winback"],
        "must": ["ops.loss_reason", "experience.feed"],
        "human_review": ["outreach.winback"],
        "scene": "丢单后经验反哺与再触达",
        "plain": "先写清为什么丢，经验环记下来；冷却后再轻触达，勿刷屏。",
    },
    {
        "id": "route-content-inquiry",
        "name": "内容获客回流",
        "intent": "content_acquisition",
        "order": "abc",
        "order_label": "a内容生产 → b多平台分发 → c询盘归因",
        "nodes": ["content.generate", "publish.multi", "inquiry.capture", "attribution.content"],
        "must": ["content.generate", "publish.multi", "attribution.content"],
        "human_review": ["publish.multi"],
        "scene": "官网/文章/视频 → 询盘",
        "plain": "内容发出去要能追到询盘；未配置引擎时诚实降级不报假成功。",
    },
    {
        "id": "route-dealer-tender",
        "name": "经销商/招投标大单",
        "intent": "dealer_tender",
        "order": "abcd",
        "order_label": "a识别大单特征 → b资质/案例包 → c账期风险闸 → d深跟+PI",
        "nodes": [
            "intent.classify",
            "prospect.enrich",
            "docs.qual_pack",
            "payment.risk_gate",
            "quote.boq",
            "pi.generate",
        ],
        "must": ["prospect.enrich", "docs.qual_pack", "payment.risk_gate"],
        "human_review": ["pi.generate", "quote.boq"],
        "scene": "经销商/工程招投标（建材大单）",
        "plain": "大单先核资质与账期风险，再出报价/PI；账期长必须人审+风控。",
    },
]


def list_dictionary() -> list[dict[str, Any]]:
    return [dict(r) for r in DICTIONARY]


def dictionary_plain_summary() -> str:
    return (
        f"编排词典 v1：{len(DICTIONARY)} 条已验证航道"
        "（含主动拓客、履约、社媒、询盘、样品、议价、挽回、内容）。"
    )