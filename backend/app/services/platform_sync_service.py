"""客户新增平台 → 超管审计、默认养号模板、指纹模板（客户无感）。"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.content import Platform
from app.models.egress import BrowserProfile
from app.models.platform_registry import PlatformTenantOrigin
from app.models.tenant import Tenant

SOURCE_CUSTOM = "customer_custom"
SOURCE_CONNECT = "customer_connect"

# 国内常见平台养号模板（含客户自填时按名称匹配）
_CN_OVERRIDES: dict[str, dict[str, Any]] = {
    "微信公众号": {"warmup_days": 7, "daily_posts": 1, "daily_likes": 3, "daily_comments": 1},
    "抖音": {"warmup_days": 14, "daily_posts": 2, "daily_likes": 30, "daily_comments": 5},
    "快手": {"warmup_days": 14, "daily_posts": 2, "daily_likes": 25, "daily_comments": 4},
    "小红书": {"warmup_days": 10, "daily_posts": 1, "daily_likes": 15, "daily_comments": 3},
    "微博": {"warmup_days": 7, "daily_posts": 3, "daily_likes": 20, "daily_comments": 5},
    "哔哩哔哩": {"warmup_days": 21, "daily_posts": 1, "weekly_videos": 1, "daily_likes": 10},
    "知乎": {"warmup_days": 14, "daily_posts": 1, "daily_answers": 2, "daily_likes": 8},
    "百家号": {"warmup_days": 7, "daily_posts": 2, "daily_likes": 5, "daily_comments": 2},
    "头条号": {"warmup_days": 7, "daily_posts": 2, "daily_likes": 8, "daily_comments": 2},
}

_INTL_OVERRIDES: dict[str, dict[str, Any]] = {
    "LinkedIn": {"warmup_days": 21, "daily_posts": 1, "daily_connections": 5},
    "X": {"warmup_days": 10, "daily_posts": 3, "daily_likes": 15},
    "Instagram": {"warmup_days": 14, "daily_posts": 1, "daily_stories": 2},
    "YouTube": {"warmup_days": 30, "daily_posts": 0, "weekly_videos": 1},
    "TikTok": {"warmup_days": 14, "daily_posts": 2, "daily_likes": 20},
    "Facebook": {"warmup_days": 14, "daily_posts": 1, "daily_likes": 8},
    "Reddit": {"warmup_days": 21, "daily_posts": 1, "daily_comments": 5},
    "Threads": {"warmup_days": 10, "daily_posts": 2, "daily_likes": 15, "daily_comments": 3},
    "Pinterest": {"warmup_days": 14, "daily_posts": 3, "daily_likes": 10},
}


def infer_platform_type(name: str, content_type: str = "article") -> str:
    """未知平台：按名称/内容形态推断类型，供指纹与养号模板选用。"""
    n = (name or "").lower()
    if any(k in n for k in ("抖音", "tiktok", "快手", "short", "reels")):
        return "short_video"
    if any(k in n for k in ("youtube", "bilibili", "哔哩", "视频号")):
        return "video"
    if any(k in n for k in ("淘宝", "京东", "amazon", "1688", "shop", "电商")):
        return "ecommerce"
    if any(k in n for k in ("linkedin", "facebook", "微博", "weibo", "twitter", "x.com")):
        return "social"
    if content_type in ("short_video", "long_video"):
        return "video" if content_type == "long_video" else "byte"
    return "custom"


def default_nurture_rules(platform_name: str, region: str) -> dict[str, Any]:
    """default_nurture_rules。

    参数说明：
    :param platform_name: 参数 platform_name
    :param region: 参数 region
    :return: 返回处理结果。
    """
    base = (
        {
            "warmup_days": 7,
            "daily_posts": 2,
            "daily_likes": 10,
            "daily_comments": 3,
            "status": "warming",
        }
        if region == "cn"
        else {
            "warmup_days": 14,
            "daily_posts": 1,
            "daily_likes": 5,
            "daily_comments": 2,
            "status": "warming",
        }
    )
    table = _CN_OVERRIDES if region == "cn" else _INTL_OVERRIDES
    merged = {**base, **table.get(platform_name, {})}
    # 自填平台：按名称关键词微调（无需客户感知）
    n = platform_name.lower()
    if "video" in n or "视频" in platform_name:
        merged.setdefault("daily_posts", 1)
        merged.setdefault("warmup_days", max(int(merged.get("warmup_days", 14)), 14))
    if "blog" in n or "博客" in platform_name or "简书" in platform_name:
        merged.setdefault("daily_posts", 1)
        merged.setdefault("warmup_days", 10)
    return merged


def default_fingerprint(region: str, platform_type: str) -> dict[str, Any]:
    """default_fingerprint。

    参数说明：
    :param region: 参数 region
    :param platform_type: 参数 platform_type
    :return: 返回处理结果。
    """
    return {
        "timezone": "Asia/Shanghai" if region == "cn" else "UTC",
        "locale": "zh-CN" if region == "cn" else "en-US",
        "platform_type": platform_type or "custom",
        "proxy_mode": "egress_pool",
        "canvas_noise": "standard",
        "webrtc_mode": "proxy_only",
    }


def ensure_browser_profile(
    db: Session,
    *,
    tenant_id: str,
    platform: Platform,
    label: str = "auto",
) -> str:
    """ensure_browser_profile。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param platform: 参数 platform
    :param label: 参数 label
    :return: 返回处理结果。
    """
    profile_name = f"{platform.name}-{label}"[:180]
    profile = BrowserProfile(
        name=profile_name,
        tenant_id=tenant_id,
        fingerprint=default_fingerprint(
            platform.region or "cn",
            platform.platform_type or "custom",
        ),
    )
    db.add(profile)
    db.flush()
    return str(profile.id)


def record_tenant_platform_origin(
    db: Session,
    *,
    tenant_id: str,
    platform: Platform,
    source: str,
    is_new_platform: bool = False,
    nurture_rules: dict | None = None,
    browser_profile_id: str | None = None,
) -> PlatformTenantOrigin:
    """record_tenant_platform_origin。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param platform: 参数 platform
    :param source: 参数 source
    :param is_new_platform: 参数 is_new_platform
    :param nurture_rules: 参数 nurture_rules
    :param browser_profile_id: 参数 browser_profile_id
    :return: 返回处理结果。
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    region = platform.region or "cn"
    rules = nurture_rules or default_nurture_rules(platform.name, region)
    row = PlatformTenantOrigin(
        tenant_id=tenant_id,
        platform_id=str(platform.id),
        source=source,
        tenant_name=tenant.name if tenant else None,
        platform_name=platform.name,
        is_new_platform=is_new_platform,
        nurture_rules=rules,
        browser_profile_id=browser_profile_id,
    )
    db.add(row)
    db.flush()
    return row


def apply_account_provision_defaults(
    account: dict,
    platform: Platform,
    *,
    tenant_id: str | None,
    db: Session,
) -> None:
    """连接账号时注入默认养号与指纹（原地修改 account dict）。"""
    region = platform.region or "cn"
    if not account.get("nurture"):
        account["nurture"] = default_nurture_rules(platform.name, region)
    if tenant_id and not account.get("browser_profile_id"):
        label = account.get("username") or account.get("account_name") or "auto"
        account["browser_profile_id"] = ensure_browser_profile(
            db,
            tenant_id=tenant_id,
            platform=platform,
            label=str(label),
        )


def sync_customer_platform_to_admin(
    db: Session,
    *,
    tenant_id: str | None,
    platform: Platform,
    source: str,
    is_new_platform: bool = False,
    nurture_rules: dict | None = None,
    browser_profile_id: str | None = None,
) -> PlatformTenantOrigin | None:
    """客户侧操作 → 超管审计表（客户 API 不返回此记录）。"""
    if not tenant_id:
        return None
    rules = nurture_rules or default_nurture_rules(
        platform.name, platform.region or "cn"
    )
    return record_tenant_platform_origin(
        db,
        tenant_id=tenant_id,
        platform=platform,
        source=source,
        is_new_platform=is_new_platform,
        nurture_rules=rules,
        browser_profile_id=browser_profile_id,
    )
