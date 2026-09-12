"""40 平台主数据目录（国内 20 + 海外 20）。"""

from __future__ import annotations

import logging
from typing import Iterable

from sqlalchemy.orm import Session

from app.models.content import Platform
logger = logging.getLogger(__name__)

# 海外十大综合社交 / IM（与用户清单一致）
CORE_GLOBAL_SOCIAL_10: tuple[str, ...] = (
    "Facebook",
    "Instagram",
    "X",
    "YouTube",
    "TikTok",
    "LinkedIn",
    "Reddit",
    "Pinterest",
    "Snapchat",
    "WhatsApp",
)

# 历史名称 → 现行 catalog 名（seed 时自动迁移 DB）
PLATFORM_NAME_ALIASES: dict[str, str] = {
    "X (Twitter)": "X",
    "Twitter / X": "X",
    "Twitter": "X",
    "WhatsApp Business": "WhatsApp",
}

GLOBAL_PLATFORM_URLS: dict[str, str] = {
    "Facebook": "https://www.facebook.com",
    "Instagram": "https://www.instagram.com",
    "X": "https://x.com",
    "YouTube": "https://www.youtube.com",
    "TikTok": "https://www.tiktok.com",
    "LinkedIn": "https://www.linkedin.com",
    "Reddit": "https://www.reddit.com",
    "Pinterest": "https://www.pinterest.com",
    "Snapchat": "https://www.snapchat.com",
    "WhatsApp": "https://www.whatsapp.com",
}

# (name, platform_type, region, content_type)
PLATFORMS_CN: list[tuple[str, str, str, str]] = [
    ("微信公众号", "wechat", "cn", "article"),
    ("抖音", "byte", "cn", "short_video"),
    ("快手", "byte", "cn", "short_video"),
    ("小红书", "social", "cn", "article"),
    ("百家号", "baidu", "cn", "article"),
    ("微博", "social", "cn", "article"),
    ("哔哩哔哩", "video", "cn", "long_video"),
    ("知乎", "social", "cn", "article"),
    ("头条号", "byte", "cn", "article"),
    ("企鹅号", "tencent", "cn", "article"),
    ("网易号", "portal", "cn", "article"),
    ("搜狐号", "portal", "cn", "article"),
    ("一点资讯", "portal", "cn", "article"),
    ("大鱼号", "byte", "cn", "article"),
    ("简书", "blog", "cn", "article"),
    ("脉脉", "social", "cn", "article"),
    ("微信视频号", "wechat", "cn", "short_video"),
    ("淘宝逛逛", "ecommerce", "cn", "short_video"),
    ("1688", "b2b", "cn", "article"),
    ("慧聪网", "b2b", "cn", "article"),
]

PLATFORMS_GLOBAL: list[tuple[str, str, str, str]] = [
    ("YouTube", "video", "global", "long_video"),
    ("TikTok", "byte", "global", "short_video"),
    ("LinkedIn", "social", "global", "article"),
    ("Facebook", "social", "global", "article"),
    ("Instagram", "social", "global", "short_video"),
    ("X", "social", "global", "article"),
    ("Pinterest", "social", "global", "article"),
    ("Reddit", "social", "global", "article"),
    ("Snapchat", "social", "global", "short_video"),
    ("Medium", "blog", "global", "article"),
    ("Tumblr", "blog", "global", "article"),
    ("Telegram Channel", "social", "global", "article"),
    ("WhatsApp", "social", "global", "article"),
    ("LINE Official", "social", "global", "article"),
    ("Zalo", "social", "global", "article"),
    ("VK", "social", "global", "article"),
    ("Quora", "social", "global", "article"),
    ("Blogger", "blog", "global", "article"),
    ("WordPress.com", "blog", "global", "article"),
    ("Amazon Seller", "ecommerce", "global", "article"),
    ("Alibaba.com", "b2b", "global", "article"),
]

# 外贸扩展：B2B 批发 + B2C 跨境（注册 / SEO 矩阵可选）
PLATFORMS_B2B_GLOBAL: list[tuple[str, str, str, str]] = [
    ("Global Sources", "b2b", "global", "article"),
    ("Made-in-China.com", "b2b", "global", "article"),
    ("TradeKey", "b2b", "global", "article"),
    ("Kompass", "b2b", "global", "article"),
    ("Thomasnet", "b2b", "global", "article"),
]

PLATFORMS_B2C_GLOBAL: list[tuple[str, str, str, str]] = [
    ("AliExpress", "ecommerce", "global", "article"),
    ("eBay", "ecommerce", "global", "article"),
    ("Shopee", "ecommerce", "global", "article"),
    ("Lazada", "ecommerce", "global", "article"),
]

PILOT_CN_NAMES: tuple[str, ...] = (
    "微信公众号",
    "抖音",
    "快手",
    "小红书",
    "百家号",
)

PILOT_GLOBAL_NAMES: tuple[str, ...] = CORE_GLOBAL_SOCIAL_10

PILOT_NAMES = {*PILOT_CN_NAMES, *PILOT_GLOBAL_NAMES}


def migrate_legacy_platform_names(db: Session) -> dict[str, int]:
    """将旧平台名合并为现行 catalog 名（X / WhatsApp 等）。"""
    renamed = deactivated = 0
    for old, new in PLATFORM_NAME_ALIASES.items():
        legacy = db.query(Platform).filter(Platform.name == old).first()
        if not legacy:
            continue
        target = db.query(Platform).filter(Platform.name == new).first()
        if target and str(target.id) != str(legacy.id):
            legacy.is_active = False
            deactivated += 1
        else:
            legacy.name = new
            if new in GLOBAL_PLATFORM_URLS:
                legacy.base_url = GLOBAL_PLATFORM_URLS[new]
            renamed += 1
    if renamed or deactivated:
        db.commit()
    return {"renamed": renamed, "deactivated": deactivated}


def all_catalog_rows() -> list[tuple[str, str, str, str]]:
    """all_catalog_rows。
    :return: 返回处理结果。
    """
    return PLATFORMS_CN + PLATFORMS_GLOBAL + PLATFORMS_B2B_GLOBAL + PLATFORMS_B2C_GLOBAL


def upsert_platforms(db: Session, rows: Iterable[tuple[str, str, str, str]]) -> dict[str, int]:
    """upsert_platforms。

    参数说明：
    :param db: 参数 db
    :param rows: 参数 rows
    :return: 返回处理结果。
    """
    migrate_legacy_platform_names(db)
    created = updated = 0
    names = [name for name, _, _, _ in rows]
    existing_map = {}
    if names:
        existing_map = {
            p.name: p
            for p in db.query(Platform).filter(Platform.name.in_(names)).all()
        }
    for name, ptype, region, ctype in rows:
        row = existing_map.get(name)
        base_url = GLOBAL_PLATFORM_URLS.get(name)
        if row:
            row.platform_type = ptype
            row.region = region
            row.content_type = ctype
            row.is_active = True
            if base_url:
                row.base_url = base_url
            updated += 1
        else:
            db.add(
                Platform(
                    name=name,
                    platform_type=ptype,
                    region=region,
                    content_type=ctype,
                    base_url=base_url,
                    is_active=True,
                )
            )
            created += 1
    db.commit()
    return {"created": created, "updated": updated, "total": created + updated}


def resolve_or_create_platform_by_name(
    db: Session,
    name: str,
    *,
    region: str = "cn",
    content_type: str = "article",
) -> Platform:
    """按名称查找或创建平台（客户自填入口，不锁死在预置 40 平台）。"""
    from app.services.platform_sync_service import infer_platform_type
    label = (name or "").strip()
    if not label:
        raise ValueError("平台名称不能为空")
    reg = "global" if (region or "cn").lower() in ("global", "intl", "overseas") else "cn"
    row = db.query(Platform).filter(Platform.name == label).first()
    if row:
        row.is_active = True
        row.region = reg
        if not row.platform_type or row.platform_type == "custom":
            row.platform_type = infer_platform_type(label, content_type)
        return row
    ptype = infer_platform_type(label, content_type)
    row = Platform(
        name=label,
        platform_type=ptype,
        region=reg,
        content_type=content_type or "article",
        has_api=False,
        is_active=True,
    )
    db.add(row)
    db.flush()
    return row


def catalog_summary(db: Session) -> dict:
    """catalog_summary。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    cn = db.query(Platform).filter(Platform.is_active, Platform.region == "cn").count()
    gl = db.query(Platform).filter(Platform.is_active, Platform.region == "global").count()
    pilot = (
        db.query(Platform)
        .filter(Platform.is_active, Platform.name.in_(PILOT_NAMES))
        .count()
    )
    target_cn = len(PLATFORMS_CN)
    target_global = len(PLATFORMS_GLOBAL) + len(PLATFORMS_B2B_GLOBAL) + len(PLATFORMS_B2C_GLOBAL)
    return {
        "cn": cn,
        "global": gl,
        "total": cn + gl,
        "pilot": pilot,
        "target_cn": target_cn,
        "target_global": target_global,
        "target_b2b": len(PLATFORMS_B2B_GLOBAL),
        "target_b2c": len(PLATFORMS_B2C_GLOBAL),
        "ready": cn >= target_cn and gl >= target_global,
    }
