# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""平台凭证指引 —— 「凭证去哪申请 / 拿到后填到哪」的系统内单一真源。

全平台分发每个渠道都要商家侧凭据（Cookie / access_token / API key）。本模块把三件事
收在一处，不让它们散落在代码、文档和运维脑子里：

  1. 需要哪些字段：PLATFORM_CREDENTIAL_REQUIREMENTS（被 B2B 适配器与账号 API 共用）；
  2. 平台侧申请入口与操作步骤：GUIDES（前端照着渲染，不靠人记）；
  3. 落在我们系统哪个位置：platform_accounts.token_data / cookie_data、
     platform_configs、或 backend/.env 环境变量兜底。

诚实边界：只写平台官方真实入口；平台没有公开自助 API 的（如 GlobalSources、
阿里国际站商品发布需 ISV 授权）如实写进 caveats，不承诺「填了就能发」。
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings

# 巡检老化时限，供下方指引文案如实引用（改配置即改文案，不写死数字）
_COOKIE_STALE_DAYS = int(settings.PLATFORM_COOKIE_STALE_DAYS)

# ---------------------------------------------------------------------------
# 1) 凭证字段要求（每个平台 = 若干「必填组」，组内任一字段满足即通过）
#    这是真发链路的唯一判定口径，b2b_global 与账号 API 都从这里取。
# ---------------------------------------------------------------------------
PLATFORM_CREDENTIAL_REQUIREMENTS: Dict[str, Tuple[Tuple[str, ...], ...]] = {
    # 阿里国际站：商家 ID 必填，会话凭证二选一（开放平台 access_token 或后台 Cookie）
    "alibaba": (
        ("alibaba_member_id",),
        ("alibaba_access_token", "alibaba_session_cookie"),
    ),
    "made_in_china": (("mic_access_token",),),
    "globalsources": (("gs_api_key",),),
}

# 字段 → 落库位置。cookie 类落 cookie_data（同时镜像进 token_data 便于统一读取），
# 其余落 token_data JSON；configs 类由调用方显式走 platform_configs。
CREDENTIAL_STORAGE: Dict[str, str] = {
    "alibaba_session_cookie": "cookie",
    "zhihu_cookies": "cookie",
    "baijiahao_cookies": "cookie",
    "toutiao_cookies": "cookie",
    "xiaohongshu_cookies": "cookie",
    "weibo_cookies": "cookie",
}


def requirements_for(platform_key: str) -> Tuple[Tuple[str, ...], ...]:
    """取某平台的必填组；未登记的平台返回空元组（不臆造要求）。"""
    return PLATFORM_CREDENTIAL_REQUIREMENTS.get((platform_key or "").strip(), ())


def all_credential_fields(platform_key: str) -> Tuple[str, ...]:
    """某平台全部可用凭证字段名（按必填组顺序展平）。"""
    out: List[str] = []
    for group in requirements_for(platform_key):
        for name in group:
            if name not in out:
                out.append(name)
    return tuple(out)


def missing_from(values: Dict[str, Any], platform_key: str) -> List[str]:
    """按必填组算缺哪些凭证；未满足的组回报组内全部候选字段名。

    values 里值为 None/空串视为缺；组内任一字段有值即算满足（宁松勿严口径）。
    回报整组而不是单个字段，是因为「二选一」的凭证对使用者是替代关系，
    只报第一个会让人以为必须申请那个（例：阿里开放平台 token 与后台 Cookie 等价）。
    """
    values = values or {}
    missing: List[str] = []
    for group in requirements_for(platform_key):
        if any(str(values.get(field) or "").strip() for field in group):
            continue
        for field in group:
            if field not in missing:
                missing.append(field)
    return missing


# ---------------------------------------------------------------------------
# 2) 指引数据：申请入口 + 步骤 + 落库位置 + 风险提示
# ---------------------------------------------------------------------------
# storage: account = 填在平台账号凭证；env = 填在 backend/.env
GUIDES: List[Dict[str, Any]] = [
    {
        "key": "alibaba",
        "label": "阿里巴巴国际站 Alibaba.com",
        "platform_names": ["Alibaba.com"],
        "storage": "account",
        "fields": [
            {
                "name": "alibaba_member_id",
                "label": "商家账号 ID（memberId / 登录账号）",
                "apply": "登录 My Alibaba，右上角账号信息或店铺后台 URL 里可见",
                "apply_url": "https://i.alibaba.com/",
            },
            {
                "name": "alibaba_access_token",
                "label": "开放平台 access_token（合规路径，推荐）",
                "apply": "阿里国际站开放平台建应用 → 商家 OAuth 授权 → 换 access_token",
                "apply_url": "https://open.alibaba.com/",
            },
            {
                "name": "alibaba_session_cookie",
                "label": "卖家后台会话 Cookie（兜底路径）",
                "apply": "浏览器登录 My Alibaba → F12 → Network → 任一请求的 Request Headers 里整条 cookie",
                "apply_url": "https://i.alibaba.com/",
            },
        ],
        "steps": [
            "有国际站卖家账号（出口通/金品诚企），完成企业实名与类目准入",
            "走开放平台：在 open.alibaba.com 建应用取 app_key/app_secret，申请商品发布权限，商家授权后回填 access_token",
            "走 Cookie 兜底：登录卖家后台复制 cookie 与 member_id 填入平台账号（会随登录过期，需定期更新）",
        ],
        "caveats": [
            "国际站商品发布 API 需 ISV 应用资质与商家授权，个人卖家不一定能自助开通",
            "Cookie 直连属非官方自动化，有风控与封号风险，先用测试账号验证",
            "平台侧有商品审核，提交成功不等于上架成功",
        ],
    },
    {
        "key": "made_in_china",
        "label": "中国制造网 Made-in-China.com",
        "platform_names": ["Made-in-China.com"],
        "storage": "account",
        "fields": [
            {
                "name": "mic_access_token",
                "label": "开放接口 access_token",
                "apply": "供应商后台 → 接口/授权管理生成；无自助入口时向 MIC 客户经理或工单申请开通",
                "apply_url": "https://seller.made-in-china.com/",
            },
        ],
        "steps": [
            "需为 MIC 付费供应商（金牌/认证供应商）账号",
            "后台申请开放接口权限，拿到 access_token",
            "填入平台账号凭证（token_data.mic_access_token）",
        ],
        "caveats": [
            "MIC 开放接口按账号与套餐授权，未开通时接口返回权限错误——系统如实报失败，不会假装发布成功",
        ],
    },
    {
        "key": "globalsources",
        "label": "环球资源 GlobalSources",
        "platform_names": ["Global Sources"],
        "storage": "account",
        "fields": [
            {
                "name": "gs_api_key",
                "label": "卖家 API Key",
                "apply": "GlobalSources 卖家中心（Supplier Center）→ 数据/接口服务；通常需向客户成功经理申请开通产品上传接口",
                "apply_url": "https://www.globalsources.com/",
            },
        ],
        "steps": [
            "需为 GlobalSources 付费卖家",
            "联系客户成功经理开通产品数据上传（feed/API）权限，拿到 api key",
            "填入平台账号凭证（token_data.gs_api_key）",
        ],
        "caveats": [
            "GlobalSources 无公开自助 API，多数卖家的商品上传走后台批量模板（CSV/feed）而非接口——该渠道可用性以是否开通为准",
        ],
    },
    {
        "key": "gsc",
        "label": "谷歌 Search Console（收录与曝光真值回收）",
        "platform_names": [],
        "storage": "env",
        "env": ["GSC_SERVICE_ACCOUNT_JSON", "GSC_API_KEY", "GSC_ALLOW_MOCK"],
        "fields": [
            {
                "name": "GSC_SERVICE_ACCOUNT_JSON",
                "label": "服务账号 JSON（整段粘贴）",
                "apply": "Google Cloud Console → API 与服务 → 启用 Search Console API → 凭据 → 创建服务账号 → 密钥 → 下载 JSON",
                "apply_url": "https://console.cloud.google.com/apis/library/searchconsole.googleapis.com",
            },
        ],
        "steps": [
            "先在 GSC 添加并验证站点资源（域名前缀或网址前缀属性）",
            "Cloud 项目启用 Search Console API，创建服务账号并下载 JSON",
            "把服务账号 client_email 作为用户加进 GSC 资源权限（完整权限），否则查询返回 403",
            "JSON 内容写入 backend/.env 的 GSC_SERVICE_ACCOUNT_JSON，不提交进 git",
        ],
        "caveats": [
            "searchAnalytics/query 只接受 OAuth，纯 API Key 查不到数据；API Key 分支仅作历史兼容保留",
            "GSC 数据有 1-2 天延迟，对外表述用「已回收」而不是「已提升」",
        ],
    },
    {
        "key": "baidu_webmaster",
        "label": "百度站长平台（主动推送与收录回收）",
        "platform_names": [],
        "storage": "env",
        "env": ["BAIDU_SITE_TOKEN"],
        "fields": [
            {
                "name": "BAIDU_SITE_TOKEN",
                "label": "站点 site_token",
                "apply": "百度搜索资源平台 → 资源管理 → 我的站点 → 站点属性 / 链接提交，复制该站 token",
                "apply_url": "https://ziyuan.baidu.com/site/index",
            },
        ],
        "steps": [
            "站点已在百度资源平台完成所有权验证（文件/CNAME/标签三选一）",
            "开通普通收录-主动推送，拿到配额与 token",
            "token 写 backend/.env（BAIDU_SITE_TOKEN），或在调用时按 query 参数传入",
        ],
        "caveats": [
            "推送配额按站点历史质量分配，配额为 0 时会被拒——系统如实回执，不报已收录",
        ],
    },
    {
        "key": "wechat_mp",
        "label": "微信公众号",
        "platform_names": ["微信公众号"],
        "storage": "account",
        "fields": [
            {
                "name": "appid",
                "label": "AppID",
                "apply": "微信公众平台 → 设置与开发 → 基本配置",
                "apply_url": "https://mp.weixin.qq.com/",
            },
            {
                "name": "appsecret",
                "label": "AppSecret",
                "apply": "同页生成/重置（只显示一次），并把服务器出口 IP 加进白名单",
                "apply_url": "https://mp.weixin.qq.com/",
            },
        ],
        "steps": [
            "需认证服务号（草稿箱/发布接口对订阅号与未认证号受限）",
            "后台取 AppID + AppSecret，填入平台账号 configs",
            "服务器出口 IP 加白名单，否则换取 token 报 40164",
        ],
        "caveats": ["草稿到发布是两步，接口只到草稿箱时系统不会当作已公开作品"],
    },
    {
        "key": "cn_cookie_platforms",
        "label": "知乎 / 百家号 / 头条号 / 小红书 / 微博（Cookie 会话类）",
        "platform_names": ["知乎", "百家号", "头条号", "小红书", "微博"],
        "storage": "account",
        "fields": [
            {
                "name": "cookie",
                "label": "登录 Cookie 串",
                "apply": "浏览器登录该平台 → F12 → Network → 任一 XHR 请求 → Request Headers → 复制整条 cookie",
                "apply_url": "",
            },
        ],
        "steps": [
            "用真实发布账号登录（别拿主账号做风控测试）",
            "复制 cookie 整串填入平台账号凭证（cookie_data）",
            "知乎另需 x_zse_93 / x_zse_96 / x_zse_99 反爬参数，放 configs",
        ],
        "caveats": [
        "Cookie 有效期通常 7-30 天，过期后需重新抓取并回填。"
        "系统有三条自动判定路径：① 每日会话巡检按 token_expire_at 与 cookie 老化时限"
        f"（PLATFORM_COOKIE_STALE_DAYS，当前 {_COOKIE_STALE_DAYS} 天）把明显过期的号置 expired；"
        "② 真发布报鉴权类错误时当场置 expired；③ 也可手动 POST /seo-matrix/platform-session-patrol"
        "（dry_run 先看命中名单）。置 expired 后不会自动恢复，须重绑后人工置回 logged_in",
            "内容型平台有风控与审核，频率过高会掉登录或封号",
        ],
    },
    {
        "key": "aitoearn_social",
        "label": "海外社媒与短视频矩阵（YouTube / Facebook / Instagram / LinkedIn / X / TikTok）",
        "platform_names": ["YouTube", "Facebook", "Instagram", "LinkedIn", "X", "TikTok"],
        "storage": "env",
        "env": ["AITOEARN_API_KEY"],
        "fields": [
            {
                "name": "AITOEARN_API_KEY",
                "label": "AiToEarn 出站通道 key",
                "apply": "自部署或订阅 AiToEarn（也可用 SAU / xhs-mcp / biliup 等出站执行器），在控制台生成 API key",
                "apply_url": "https://aitoearn.ai/",
            },
        ],
        "steps": [
            "先把出站通道跑起来（AiToEarn / SAU），在通道内完成各社媒 OAuth 授权",
            "把通道 key 写入 backend/.env 的 AITOEARN_API_KEY",
            "系统按通道可用性放行；无 key 时相关平台报未配置，不冒充发布成功",
        ],
        "caveats": [
            "各社媒的 OAuth 凭据在出站通道侧管理，本系统只持有通道 key",
        ],
    },
]

# 平台显示名 → 指引（反向索引，避免各处硬编码 if-else）
_GUIDE_BY_PLATFORM_NAME: Dict[str, Dict[str, Any]] = {
    str(name).strip().lower(): guide
    for guide in GUIDES
    for name in guide.get("platform_names", [])
}


def guides_payload() -> List[Dict[str, Any]]:
    """给前端的完整指引（不含任何密钥值）。"""
    return [dict(guide) for guide in GUIDES]


def guide_for_platform(platform_name: Optional[str]) -> Optional[Dict[str, Any]]:
    """按 platforms.name 找指引；找不到返回 None（不猜）。"""
    if not platform_name:
        return None
    return _GUIDE_BY_PLATFORM_NAME.get(str(platform_name).strip().lower())


def required_platform_key(platform_name: Optional[str]) -> str:
    """平台显示名 → 有字段级门禁的凭证要求 key（alibaba / made_in_china / globalsources）。

    未登记指引、或登记了但无必填组的平台返回空串，调用方据此判「无字段级门禁」。
    """
    guide = guide_for_platform(platform_name)
    if not guide:
        return ""
    key = str(guide.get("key") or "")
    return key if key in PLATFORM_CREDENTIAL_REQUIREMENTS else ""


def env_credential_status() -> List[Dict[str, Any]]:
    """环境变量类凭证的配置状态。只回布尔，绝不回值本身。"""
    names: List[str] = []
    for guide in GUIDES:
        for name in guide.get("env", []):
            if name not in names:
                names.append(name)
    return [
        {"env": name, "configured": bool(os.getenv(name, "").strip())}
        for name in names
    ]


__all__ = [
    "CREDENTIAL_STORAGE",
    "GUIDES",
    "PLATFORM_CREDENTIAL_REQUIREMENTS",
    "all_credential_fields",
    "env_credential_status",
    "guide_for_platform",
    "guides_payload",
    "missing_from",
    "required_platform_key",
    "requirements_for",
]
