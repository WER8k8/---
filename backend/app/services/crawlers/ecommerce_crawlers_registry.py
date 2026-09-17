# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""ECommerceCrawlers 爬虫配方注册表 — 映射 GitHub 子项目到本系统能力。

来源：https://github.com/DropsDevopsOrg/ECommerceCrawlers
原则：Sidecar 外置；无 forbidden（社媒改 social_restricted + 门禁）；黑帽 SEO 永久 platform_blocked。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ComplianceTier = Literal[
    "allowed_sidecar",
    "human_review",
    "restricted",
    "social_restricted",
    "platform_blocked",
]

ProductLane = Literal[
    "seo_matrix",
    "osint",
    "competitor_intel",
    "international_inquiry",
    "growth_tools",
    "market_intel",
    "reference_only",
]


@dataclass(frozen=True)
class SpiderRecipe:
    id: str
    name: str
    repo_path: str
    lane: ProductLane
    compliance: ComplianceTier
    summary: str
    compliance_note: str = ""
    requires_purpose: bool = False
    max_items_per_run: int = 50


def _r(
    id: str,
    name: str,
    repo_path: str,
    lane: ProductLane,
    compliance: ComplianceTier,
    summary: str,
    *,
    compliance_note: str = "",
    requires_purpose: bool = False,
    max_items: int = 50,
) -> SpiderRecipe:
    """实现 r 的功能。
    
    :param id: 参数 id（类型: str）
    :param name: 参数 name（类型: str）
    :param repo_path: 参数 repo_path（类型: str）
    :param lane: 参数 lane（类型: ProductLane）
    :param compliance: 参数 compliance（类型: ComplianceTier）
    :param summary: 参数 summary（类型: str）
    :param compliance_note: 参数 compliance_note（类型: str）
    :param requires_purpose: 参数 requires_purpose（类型: bool）
    :param max_items: 参数 max_items（类型: int）
    :return: 返回 SpiderRecipe 结果
    """
    return SpiderRecipe(
        id=id,
        name=name,
        repo_path=repo_path,
        lane=lane,
        compliance=compliance,
        summary=summary,
        compliance_note=compliance_note,
        requires_purpose=requires_purpose,
        max_items_per_run=max_items,
    )


SPIDER_RECIPES: tuple[SpiderRecipe, ...] = (
    # ── SEO / 增长 ──
    _r(
        "baidu_keyword",
        "百度关键词收录",
        "OthertCrawler/0x10baidu",
        "seo_matrix",
        "allowed_sidecar",
        "SEO 矩阵：站点/词在百度收录与展现信号",
        requires_purpose=True,
        max_items=30,
    ),
    _r(
        "baidu_tieba",
        "百度贴吧",
        "OthertCrawler/0x01baidutieba",
        "growth_tools",
        "restricted",
        "公开帖舆情/关键词讨论监测",
        compliance_note="仅公开帖；禁止登录态爬私信",
        requires_purpose=True,
        max_items=20,
    ),
    _r(
        "spider_flood_dir",
        "蜘蛛泛目录",
        "OthertCrawler/0x11zzc",
        "seo_matrix",
        "platform_blocked",
        "黑帽泛目录 — 平台永久禁用",
        compliance_note="违反合规与送检要求，不得启用",
    ),
    # ── OSINT / 背调 ──
    _r(
        "qichacha",
        "企查查企业信息",
        "QiChaCha",
        "osint",
        "human_review",
        "国内企业背调 enrichment",
        compliance_note="须人工核实，不可作为终态风控通过",
        requires_purpose=True,
        max_items=10,
    ),
    _r(
        "fofa",
        "FOFA 资产探测",
        "OthertCrawler/0x08fofa",
        "osint",
        "restricted",
        "企业对外资产指纹（安全研究）",
        compliance_note="须 FOFA 账号授权；仅安全合规用途",
        requires_purpose=True,
        max_items=15,
    ),
    # ── 竞品 / 市场 ──
    _r(
        "taobao",
        "淘宝/天猫商品",
        "TaobaoCrawler",
        "competitor_intel",
        "restricted",
        "国内竞品价盘监测",
        compliance_note="租户授权 + Sidecar 独立 Cookie；禁止默认全开",
        requires_purpose=True,
        max_items=30,
    ),
    _r(
        "xianyu",
        "闲鱼二手价盘",
        "XianyuCrawler",
        "competitor_intel",
        "restricted",
        "二手/尾货价格参考",
        requires_purpose=True,
        max_items=20,
    ),
    _r(
        "zhaopin",
        "招聘网站信号",
        "ZhaopinCrawler",
        "competitor_intel",
        "allowed_sidecar",
        "区域招聘热度 / 扩产信号",
        requires_purpose=True,
        max_items=25,
    ),
    _r(
        "autohome",
        "汽车之家",
        "OthertCrawler/0x09autohome",
        "market_intel",
        "human_review",
        "汽配/建材周边行业资讯",
        requires_purpose=True,
    ),
    _r(
        "dianping",
        "大众点评",
        "DianpingCrawler",
        "market_intel",
        "human_review",
        "本地商户公开评价图谱",
        requires_purpose=True,
    ),
    # ── 内容 / 资讯 ──
    _r(
        "sohu_news",
        "搜狐新闻",
        "SohuNewCrawler",
        "growth_tools",
        "allowed_sidecar",
        "行业新闻监测",
        requires_purpose=True,
        max_items=20,
    ),
    _r(
        "toutiao",
        "今日头条",
        "OthertCrawler/0x12toutiao",
        "growth_tools",
        "restricted",
        "公开资讯/行业动态",
        compliance_note="仅公开内容；禁止私信/用户画像批量导出",
        requires_purpose=True,
        max_items=20,
    ),
    _r(
        "cnblog",
        "博客园",
        "cnblog",
        "growth_tools",
        "allowed_sidecar",
        "技术/行业博客 RSS 式监测",
        max_items=20,
    ),
    _r(
        "douban_movie",
        "豆瓣电影",
        "OthertCrawler/0x02doubanmovie",
        "reference_only",
        "human_review",
        "参考：公开评分数据（非主业务）",
        requires_purpose=True,
    ),
    # ── 应用商店 / 垂直 ──
    _r(
        "xiaomi_app",
        "小米应用商店",
        "OthertCrawler/0x15xiaomiappshop",
        "market_intel",
        "allowed_sidecar",
        "App 竞品监测",
        requires_purpose=True,
    ),
    _r(
        "kuan_app",
        "酷安应用",
        "OthertCrawler/0x16kuanappshop",
        "market_intel",
        "allowed_sidecar",
        "App 评论/竞品",
        requires_purpose=True,
    ),
    _r(
        "ctrip",
        "携程",
        "OthertCrawler/0x14ctrip_crawler",
        "reference_only",
        "human_review",
        "差旅/工程参考（非核心）",
        requires_purpose=True,
    ),
    _r(
        "anjuke",
        "安居客",
        "OthertCrawler/0x19anjuke",
        "reference_only",
        "human_review",
        "工程/建材区域参考",
        requires_purpose=True,
    ),
    # ── 社媒（原 forbidden → social_restricted + 三重门禁）──
    _r(
        "wechat",
        "微信公众号",
        "WechatCrawler",
        "growth_tools",
        "social_restricted",
        "公众号公开文章监测",
        compliance_note="仅公开文章；禁止采集私信/粉丝列表/自动推送",
        requires_purpose=True,
        max_items=15,
    ),
    _r(
        "weibo",
        "微博",
        "WeiboCrawler",
        "growth_tools",
        "social_restricted",
        "微博公开帖监测",
        compliance_note="禁止账号池/批量触达/登录态私信",
        requires_purpose=True,
        max_items=20,
    ),
    _r(
        "zhihu",
        "知乎",
        "OthertCrawler/0x17zhihu",
        "growth_tools",
        "social_restricted",
        "知乎公开问答/文章监测",
        compliance_note="仅公开页；禁止批量私信",
        requires_purpose=True,
        max_items=20,
    ),
    # ── MediaCrawler（NanmiCoder）海外社媒 / 黄页 ──
    _r(
        "media_facebook",
        "Facebook 公开商家页",
        "NanmiCoder/MediaCrawler/platform/facebook",
        "social_lead_intel",
        "social_restricted",
        "Facebook 公开页商家信息（非私信）",
        compliance_note="MEDIA_CRAWLER_URL Sidecar；禁止账号池/自动触达",
        requires_purpose=True,
        max_items=15,
    ),
    _r(
        "media_instagram",
        "Instagram 公开主页",
        "NanmiCoder/MediaCrawler/platform/instagram",
        "social_lead_intel",
        "social_restricted",
        "Instagram 公开商家主页",
        compliance_note="仅公开内容；ECOMMERCE_SOCIAL_SPIDERS_ENABLED=1",
        requires_purpose=True,
        max_items=15,
    ),
    _r(
        "media_youtube",
        "YouTube 频道/商家",
        "NanmiCoder/MediaCrawler/platform/youtube",
        "social_lead_intel",
        "social_restricted",
        "YouTube 公开频道联系信息",
        requires_purpose=True,
        max_items=10,
    ),
    _r(
        "media_europages",
        "Europages 黄页",
        "NanmiCoder/MediaCrawler/custom/europages",
        "international_inquiry",
        "restricted",
        "欧洲 B2B 黄页公开企业页",
        compliance_note="须 tenant_consent + purpose",
        requires_purpose=True,
        max_items=20,
    ),
    _r(
        "media_thomasnet",
        "Thomasnet 工业黄页",
        "NanmiCoder/MediaCrawler/custom/thomasnet",
        "international_inquiry",
        "restricted",
        "北美工业采购商黄页",
        requires_purpose=True,
        max_items=20,
    ),
)


def recipe_by_id(spider_id: str) -> SpiderRecipe | None:
    """实现 recipebyID 的功能。
    
    :param spider_id: 参数 spider_id（类型: str）
    :return: 返回 SpiderRecipe | None 结果
    """
    key = (spider_id or "").strip().lower()
    for r in SPIDER_RECIPES:
        if r.id == key:
            return r
    return None


def recipes_for_lane(lane: ProductLane) -> list[SpiderRecipe]:
    """实现 recipesforlane 的功能。
    
    :param lane: 参数 lane（类型: ProductLane）
    :return: 返回 list[SpiderRecipe] 结果
    """
    return [r for r in SPIDER_RECIPES if r.lane == lane]


def callable_recipes() -> list[SpiderRecipe]:
    """实现 callablerecipes 的功能。
    
    :return: 返回 list[SpiderRecipe] 结果
    """
    return [r for r in SPIDER_RECIPES if r.compliance != "platform_blocked"]


def registry_payload() -> dict:
    """实现 registrypayload 的功能。
    
    :return: 返回 dict 结果
    """
    tiers = {
        "allowed_sidecar": "Sidecar + purpose；结果须 evidence",
        "human_review": "须 purpose；人工核实后方可引用",
        "restricted": "平台开关 + tenant_consent + compliance_ack + purpose",
        "social_restricted": "ECOMMERCE_SOCIAL_SPIDERS_ENABLED + 上述全部 + 禁 bulk_outreach",
        "platform_blocked": "永久禁用（黑帽 SEO 等）",
    }
    return {
        "github": "https://github.com/DropsDevopsOrg/ECommerceCrawlers",
        "gitee_mirror": "https://gitee.com/AJay13/ECommerceCrawlers",
        "integration": "sidecar_http",
        "compliance_tiers": tiers,
        "env_platform_switches": [
            "ECOMMERCE_CRAWLERS_URL",
            "ECOMMERCE_CRAWLERS_TOKEN",
            "ECOMMERCE_SOCIAL_SPIDERS_ENABLED",
            "ECOMMERCE_SPIDERS_ENABLE_ALL",
            "ECOMMERCE_SPIDER_ENABLE_<SPIDER_ID>",
        ],
        "items": [
            {
                "id": r.id,
                "name": r.name,
                "repo_path": r.repo_path,
                "lane": r.lane,
                "compliance": r.compliance,
                "summary": r.summary,
                "compliance_note": r.compliance_note,
                "requires_purpose": r.requires_purpose,
                "max_items_per_run": r.max_items_per_run,
                "callable": r.compliance != "platform_blocked",
            }
            for r in SPIDER_RECIPES
        ],
    }
