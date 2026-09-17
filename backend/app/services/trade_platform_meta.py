# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""外贸平台分类元数据 — 注册 / 开户指引展示用。"""

from __future__ import annotations

from typing import Any

# category_key → 中文名 + 适用说明
TRADE_PLATFORM_CATEGORIES: dict[str, dict[str, str]] = {
    "social_global": {
        "label": "海外社交媒体",
        "hint": "Facebook / LinkedIn / YouTube / TikTok 等引流与品牌",
    },
    "im_global": {
        "label": "即时通讯（外贸标配）",
        "hint": "WhatsApp / Telegram / LINE — 海外客户沟通第一入口",
    },
    "b2b": {
        "label": "B2B 大宗批发平台",
        "hint": "Alibaba / Made-in-China / Global Sources 找采购商",
    },
    "b2c": {
        "label": "B2C 跨境零售",
        "hint": "Amazon / 速卖通 / Shopee 小批量与终端零售",
    },
    "social_cn": {
        "label": "国内内容平台",
        "hint": "公众号 / 抖音 / 小红书 等",
    },
    "regional": {
        "label": "区域专项",
        "hint": "VK（俄语区）/ Zalo（越南）等单一市场",
    },
}

# 平台名 → 分类 + 一句话用途（注册页分组）
PLATFORM_TRADE_META: dict[str, dict[str, str]] = {
    "LinkedIn": {"category": "social_global", "use": "B2B 首选 · 精准找采购经理"},
    "Facebook": {"category": "social_global", "use": "全品类 · 全球覆盖率最高"},
    "Instagram": {"category": "social_global", "use": "视觉种草 · 高颜值快消"},
    "YouTube": {"category": "social_global", "use": "工厂实拍 · 信任背书第一平台"},
    "X": {"category": "social_global", "use": "行业快讯 · 展会与进口商动态"},
    "TikTok": {"category": "social_global", "use": "新兴流量 · 东南亚/中东/拉美"},
    "Pinterest": {"category": "social_global", "use": "欧美家居建材 · 图片引流"},
    "Reddit": {"category": "social_global", "use": "海外兴趣论坛 · 垂直社群"},
    "Snapchat": {"category": "social_global", "use": "欧美年轻群体社交"},
    "WhatsApp": {"category": "im_global", "use": "全球外贸沟通标配"},
    "Telegram Channel": {"category": "im_global", "use": "频道广播 · 俄语/中东常用"},
    "LINE Official": {"category": "im_global", "use": "日本/泰国/台湾市场"},
    "Zalo": {"category": "im_global", "use": "越南本土 IM"},
    "VK": {"category": "regional", "use": "俄罗斯/中亚第一社交"},
    "Alibaba.com": {"category": "b2b", "use": "全品类 B2B · 中小工厂起步首选"},
    "Global Sources": {"category": "b2b", "use": "电子/礼品 · 中高端采购商"},
    "Made-in-China.com": {"category": "b2b", "use": "机械五金建材 · 制造业优选"},
    "TradeKey": {"category": "b2b", "use": "中东/土耳其/东南亚 B2B"},
    "Kompass": {"category": "b2b", "use": "欧洲企业库 · 工业采购"},
    "Thomasnet": {"category": "b2b", "use": "美国工业采购平台"},
    "1688": {"category": "b2b", "use": "国内批发源头"},
    "Amazon Seller": {"category": "b2c", "use": "欧美中高端消费品"},
    "AliExpress": {"category": "b2c", "use": "俄/南美/欧洲平价小商品"},
    "eBay": {"category": "b2c", "use": "汽配/二手/小众品类"},
    "Shopee": {"category": "b2c", "use": "东南亚本土电商"},
    "Lazada": {"category": "b2c", "use": "东南亚跨境零售"},
    "微信公众号": {"category": "social_cn", "use": "国内私域与文章"},
    "抖音": {"category": "social_cn", "use": "国内短视频直播"},
    "小红书": {"category": "social_cn", "use": "种草与品牌"},
}


def enrich_platform_row(name: str, region: str, content_type: str, platform_id: str | None = None) -> dict[str, Any]:
    """enrich_platform_row。

    参数说明：
    :param name: 参数 name
    :param region: 参数 region
    :param content_type: 参数 content_type
    :param platform_id: 参数 platform_id
    :return: 返回处理结果。
    """
    meta = PLATFORM_TRADE_META.get(name, {})
    cat = meta.get("category") or ("social_cn" if region == "cn" else "social_global")
    return {
        "name": name,
        "platform_id": platform_id,
        "region": region,
        "content_type": content_type,
        "category": cat,
        "category_label": TRADE_PLATFORM_CATEGORIES.get(cat, {}).get("label", cat),
        "use_hint": meta.get("use", ""),
        "default_selected": False,
    }


def group_platforms_for_register(platforms: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """按外贸分类分组供注册页展示。"""
    buckets: dict[str, list[dict[str, Any]]] = {}
    for p in platforms:
        cat = p.get("category") or "social_global"
        buckets.setdefault(cat, []).append(p)
    order = ["im_global", "social_global", "b2b", "b2c", "regional", "social_cn"]
    out: list[dict[str, Any]] = []
    for key in order:
        items = buckets.pop(key, [])
        if not items:
            continue
        out.append(
            {
                "category": key,
                "label": TRADE_PLATFORM_CATEGORIES.get(key, {}).get("label", key),
                "hint": TRADE_PLATFORM_CATEGORIES.get(key, {}).get("hint", ""),
                "platforms": items,
            }
        )
    for key, items in buckets.items():
        out.append({"category": key, "label": key, "hint": "", "platforms": items})
    return out
