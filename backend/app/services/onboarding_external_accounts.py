# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""开户第三方账号 / 云存储 — 注册与实名流程编排（平台代开 vs 客户自备）。"""

from __future__ import annotations

import json
from typing import Any, Literal

from app.core.config import settings
from app.models.tenant import Tenant
from app.services.media_cuplayer_service import cuplayer_configured
from app.services.media_qiniu_service import qiniu_configured
from app.services.media_r2_service import r2_configured

Owner = Literal["platform", "tenant"]
Phase = Literal["open", "visible", "contact", "notify"]


def _safe_settings(raw: str | None) -> dict[str, Any]:
    """_safe_settings。

    参数说明：
    :param raw: 参数 raw
    :return: 返回处理结果。
    """
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


# 静态定义：注册 URL、实名说明、谁负责
EXTERNAL_ACCOUNT_SPECS: tuple[dict[str, Any], ...] = (
    {
        "id": "youding_saas",
        "title": "优丁 SaaS 账号",
        "owner": "platform",
        "phase": "open",
        "required": True,
        "register_url": None,
        "portal_url": "/register",
        "summary": "在本站完成邮箱验证即可，无需再去别的网站开户。",
        "steps": [
            "填写公司信息与邮箱",
            "收取并填写 6 位验证码",
            "选择套餐并完成注册",
        ],
    },
    {
        "id": "qiniu_product_images",
        "title": "七牛云 · 产品图片空间（国内）",
        "owner": "platform",
        "phase": "open",
        "required": False,
        "applies_when": {"storage_region": "cn"},
        "register_url": "https://portal.qiniu.com/signup",
        "portal_url": "https://portal.qiniu.com/",
        "summary": "国内产品白底图存储。**由平台统一注册并完成实名**；您开户后直接使用「产品图片空间」，无需单独开七牛。",
        "steps": [
            "【平台运维】注册七牛云并完成企业/个人实名认证（见 docs/PLATFORM-STORAGE-SETUP.md）",
            "【平台运维】运行 scripts/setup-platform-storage.ps1 验密钥并写入 QINIU_*",
            "【平台运维】超管后台 → 系统 → 存储开通 → 验收当前配置",
            "【您】在管理后台上传产品图即可，无需注册七牛",
        ],
        "tenant_action": "none",
    },
    {
        "id": "cloudflare_r2_images",
        "title": "Cloudflare R2 · 产品图片（海外）",
        "owner": "platform",
        "phase": "open",
        "required": False,
        "applies_when": {"storage_region": "global"},
        "register_url": "https://dash.cloudflare.com/sign-up",
        "portal_url": "https://dash.cloudflare.com/",
        "summary": "出海/国际化租户产品图与归档。**由平台统一开通 R2**；您无需注册 Cloudflare 即可上传。",
        "steps": [
            "【平台运维】注册 Cloudflare 并开通 R2",
            "【平台运维】创建 Bucket，配置 MEDIA_R2_* 与可选 CDN 域名",
            "【您】上传产品图，链接可用于海外建站与发布拉源",
        ],
        "tenant_action": "none",
    },
    {
        "id": "cuplayer_video",
        "title": "酷播云 · 视频点播（国内播放）",
        "owner": "tenant",
        "phase": "visible",
        "required": False,
        "register_url": "https://www.cuplayer.com/cloud/",
        "portal_url": "https://www.cuplayer.com/",
        "summary": "发长视频、国内秒开预览前需要。需**您自行**注册酷播并完成实名，再把 API 密钥填到系统设置。",
        "steps": [
            "打开酷播云官网注册账号",
            "完成企业或个人实名认证（上传执照/身份证）",
            "控制台 → API 接口 → 获取 writetoken / secretkey / userid",
            "登录优丁 → 设置 → 视频云存储 → 粘贴密钥并保存",
        ],
        "tenant_action": "register_and_bind",
        "settings_route": "/client/settings",
    },
    {
        "id": "wechat_open",
        "title": "微信开放平台 / 公众号",
        "owner": "tenant",
        "phase": "visible",
        "required": False,
        "applies_when": {"platform_keyword": "微信"},
        "register_url": "https://open.weixin.qq.com/",
        "portal_url": "https://mp.weixin.qq.com/",
        "summary": "绑定微信公众号或扫码登录发布时需要。",
        "steps": [
            "注册微信公众平台或开放平台账号",
            "完成主体认证（企业/个体户/个人订阅号规则不同）",
            "创建应用或公众号，获取 AppID",
            "优丁 → 多平台分发 → 绑定微信并完成 OAuth",
        ],
        "tenant_action": "register_and_bind",
        "settings_route": "/client/distribute",
    },
    {
        "id": "douyin_open",
        "title": "抖音 / 巨量引擎开放平台",
        "owner": "tenant",
        "phase": "visible",
        "required": False,
        "applies_when": {"platform_keyword": "抖音"},
        "register_url": "https://open.douyin.com/",
        "portal_url": "https://creator.douyin.com/",
        "summary": "抖音发文、评论自动谈单需要您自己的企业号或创作者账号。",
        "steps": [
            "注册抖音企业号或创作者账号",
            "完成主体资质认证（营业执照等）",
            "开放平台创建应用（如需 API 发布）",
            "优丁 → SEO 矩阵 / 多平台分发 → 绑定抖音",
        ],
        "tenant_action": "register_and_bind",
        "settings_route": "/client/distribute",
    },
    {
        "id": "youtube_google",
        "title": "Google / YouTube 频道",
        "owner": "tenant",
        "phase": "visible",
        "required": False,
        "applies_when": {"platform_keyword": "YouTube"},
        "register_url": "https://www.youtube.com/create_channel",
        "portal_url": "https://studio.youtube.com/",
        "summary": "海外视频发布需要 Google 账号与 YouTube 频道。",
        "steps": [
            "注册 Google 账号",
            "创建 YouTube 品牌频道",
            "（可选）Google Cloud 项目启用 YouTube Data API",
            "优丁 → 多平台分发 → 绑定 YouTube",
        ],
        "tenant_action": "register_and_bind",
        "settings_route": "/client/distribute",
    },
    {
        "id": "wecom_corp",
        "title": "企业微信",
        "owner": "tenant",
        "phase": "notify",
        "required": False,
        "register_url": "https://work.weixin.qq.com/wework_admin/register_wx",
        "portal_url": "https://work.weixin.qq.com/wework_admin/frame",
        "summary": "销售手机收询盘通知、IM 路由需要企业微信管理后台。",
        "steps": [
            "注册企业微信并完成企业认证",
            "创建自建应用，记录 CorpID / AgentId / Secret",
            "优丁 → 询盘 IM → 填写企微推送配置",
        ],
        "tenant_action": "register_and_bind",
        "settings_route": "/inquiries/im-routing",
    },
)


def _plan_features(tenant: Tenant | None) -> list[str]:
    """_plan_features。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    if not tenant or not tenant.plan or not tenant.plan.features:
        return []
    try:
        raw = json.loads(tenant.plan.features)
        return raw if isinstance(raw, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def _infer_storage_region(tenant: Tenant | None) -> str:
    """_infer_storage_region。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    if not tenant:
        return str(settings.FILE_STORAGE_DEFAULT_REGION or "cn")
    ts = _safe_settings(tenant.settings)
    region = ts.get("storage_region")
    if region in ("cn", "global"):
        return str(region)
    features = _plan_features(tenant)
    if "globalization" in features or "international" in features:
        return "global"
    return "cn"


def _platform_keyword_match(platform_names: list[str], keyword: str) -> bool:
    """_platform_keyword_match。

    参数说明：
    :param platform_names: 参数 platform_names
    :param keyword: 参数 keyword
    :return: 返回处理结果。
    """
    kw = keyword.lower()
    return any(kw in (n or "").lower() for n in platform_names)


def _spec_applies(
    spec: dict[str, Any],
    *,
    storage_region: str,
    platform_names: list[str],
) -> bool:
    """_spec_applies。

    参数说明：
    :param spec: 参数 spec
    :param storage_region: 参数 storage_region
    :param platform_names: 参数 platform_names
    :return: 返回处理结果。
    """
    when = spec.get("applies_when")
    if not when:
        return True
    if when.get("storage_region") and when["storage_region"] != storage_region:
        return False
    pk = when.get("platform_keyword")
    if pk and not _platform_keyword_match(platform_names, str(pk)):
        return False
    return True


def _item_status(spec: dict[str, Any], tenant: Tenant | None) -> str:
    """_item_status。

    参数说明：
    :param spec: 参数 spec
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    sid = spec["id"]
    if sid == "youding_saas":
        return "done" if tenant else "pending"
    if sid == "qiniu_product_images":
        return "done" if qiniu_configured() else "pending"
    if sid == "cloudflare_r2_images":
        return "done" if r2_configured() else "pending"
    if sid == "cuplayer_video":
        ts = _safe_settings(tenant.settings if tenant else None)
        if ts.get("cuplayer_writetoken") or cuplayer_configured():
            return "done"
        return "pending"
    if tenant:
        ts = _safe_settings(tenant.settings)
        bound = ts.get("external_accounts_bound") if isinstance(ts.get("external_accounts_bound"), dict) else {}
        if bound.get(sid):
            return "done"
    return "pending"


def build_external_accounts(
    tenant: Tenant | None = None,
    *,
    platform_names: list[str] | None = None,
    storage_region: str | None = None,
    include_all_specs: bool = False,
) -> list[dict[str, Any]]:
    """生成开户/向导用的第三方账号清单。"""
    names = platform_names or []
    region = storage_region or (_infer_storage_region(tenant) if tenant else "cn")
    out: list[dict[str, Any]] = []
    for spec in EXTERNAL_ACCOUNT_SPECS:
        if not include_all_specs and not _spec_applies(spec, storage_region=region, platform_names=names):
            continue
        row = {
            "id": spec["id"],
            "title": spec["title"],
            "owner": spec["owner"],
            "owner_label": "平台代开" if spec["owner"] == "platform" else "客户自备",
            "phase": spec["phase"],
            "required": bool(spec.get("required")),
            "summary": spec.get("summary") or "",
            "steps": list(spec.get("steps") or []),
            "register_url": spec.get("register_url"),
            "portal_url": spec.get("portal_url"),
            "tenant_action": spec.get("tenant_action") or ("none" if spec["owner"] == "platform" else "register"),
            "settings_route": spec.get("settings_route"),
            "status": _item_status(spec, tenant),
        }
        out.append(row)
    return out


def build_external_accounts_phases(accounts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """build_external_accounts_phases。

    参数说明：
    :param accounts: 参数 accounts
    :return: 返回处理结果。
    """
    phase_meta = {
        "open": {"title": "开户即用", "summary": "平台已代开或注册页已完成"},
        "visible": {"title": "让人看见", "summary": "发内容、存视频、绑平台前准备"},
        "contact": {"title": "客户找得到你", "summary": "联系方式与渠道接入"},
        "notify": {"title": "销售收得到", "summary": "企微等通知渠道"},
    }
    grouped: dict[str, list[dict[str, Any]]] = {k: [] for k in phase_meta}
    for acc in accounts:
        ph = str(acc.get("phase") or "visible")
        grouped.setdefault(ph, []).append(acc)
    result = []
    for pid, meta in phase_meta.items():
        items = grouped.get(pid) or []
        if not items:
            continue
        done = sum(1 for i in items if i.get("status") == "done")
        result.append(
            {
                "id": pid,
                **meta,
                "done": done,
                "total": len(items),
                "completed": done >= len(items),
                "items": items,
            }
        )
    return result


def get_register_external_preview() -> dict[str, Any]:
    """注册页：开户前告知哪些要平台代开、哪些可能要客户自备。"""
    platform_managed = [s for s in EXTERNAL_ACCOUNT_SPECS if s["owner"] == "platform"]
    tenant_managed = [s for s in EXTERNAL_ACCOUNT_SPECS if s["owner"] == "tenant"]
    return {
        "headline": "开户后云存储与第三方账号说明",
        "platform_managed_summary": "产品图片（国内七牛 / 海外 R2）由平台统一注册实名，您无需单独开云存储账号。",
        "tenant_managed_summary": "发长视频（酷播）、绑抖音/微信/YouTube、企业微信通知等，需您按指引在对应官网注册并回填密钥。",
        "platform_items": [
            {"title": s["title"], "summary": s.get("summary", "")[:120]}
            for s in platform_managed
            if s["id"] != "youding_saas"
        ],
        "tenant_items": [
            {"title": s["title"], "summary": s.get("summary", "")[:120]}
            for s in tenant_managed
        ],
    }
