# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""SEO 矩阵图文发布：平台适配器 + PublishService 异步回退。"""

from __future__ import annotations

import asyncio
import re
from typing import Any

from sqlalchemy.orm import Session

from app.models.content import GeneratedContent, Platform, PlatformAccount
from app.services.publish_capability_registry import publish_block_reason
from app.services.publish_service import PUBLISHER_MAP, PublishService

_PLATFORM_NAME_ADAPTERS: dict[str, type] | None = None

# 平台显示名 → 国内适配器（同步 publish，返回 URL）
_NAME_ADAPTER_IMPORTS: dict[str, tuple[str, str]] = {
    "微信公众号": ("app.services.platforms.wechat", "WeChatPublisherAdapter"),
    "百家号": ("app.services.platforms.baijiahao", "BaijiahaoPublisherAdapter"),
    "小红书": ("app.services.platforms.xiaohongshu", "XiaohongshuPublisherAdapter"),
    "知乎": ("app.services.platforms.zhihu", "ZhihuPublisherAdapter"),
    "微博": ("app.services.platforms.weibo", "WeiboPublisherAdapter"),
    "头条号": ("app.services.platforms.toutiao", "ToutiaoPublisherAdapter"),
    "CSDN": ("app.services.platforms.csdn", "CSDNPublisherAdapter"),
    "Alibaba.com": ("app.services.platforms.b2b_global", "AlibabaPublisherAdapter"),
    "Made-in-China.com": ("app.services.platforms.b2b_global", "MadeInChinaPublisherAdapter"),
    "Global Sources": ("app.services.platforms.b2b_global", "GlobalSourcesPublisherAdapter"),
}

# 平台名 → PublishService PUBLISHER_MAP 键
_NAME_PUBLISHER_KEY: dict[str, str] = {
    "抖音": "douyin",
    "快手": "kuaishou",
    "哔哩哔哩": "bilibili",
    "YouTube": "youtube",
    "Facebook": "facebook",
    "Instagram": "instagram",
    "LinkedIn": "linkedin",
    "Twitter": "twitter",
    "TikTok": "douyin",
    "X": "twitter",
    "Telegram Channel": "telegram",
    "WhatsApp": "whatsapp_business",
    # 中文平台名 slug 化后为空，只能靠这里的显式映射；缺失即解析失败（宁缺不借）。
    "微信公众号": "wechat",
    "头条号": "toutiao",
    "知乎": "zhihu",
    "微博": "weibo",
    "微信视频号": "wechat_channels",
    "企鹅号": "qieehao",
    "网易号": "wangyi_hao",
    "搜狐号": "sohu_hao",
    "一点资讯": "yidianzixun",
    "大鱼号": "dayuhao",
    "简书": "jianshu",
    "脉脉": "maimai",
    "淘宝逛逛": "taobao_guangguang",
    "1688": "ali1688",
    "慧聪网": "huizhong",
}


def _name_slug_key(name: str) -> str:
    """平台显示名 → PUBLISHER_MAP 键（仅当该键真的存在时）。

    例：Reddit → reddit、Medium → medium、VK → vk。命中不了返回空串，交由调用方判失败。
    """
    slug = re.sub(r"[^a-z0-9]+", "_", str(name or "").strip().lower()).strip("_")
    if not slug:
        return ""
    candidates = (slug, slug.replace("_", "-"), slug.replace("-", "_"))
    for candidate in candidates:
        if candidate in PUBLISHER_MAP:
            return candidate
    return ""


def _load_name_adapters() -> dict[str, type]:
    """_load_name_adapters。
    :return: 返回处理结果。
    """
    global _PLATFORM_NAME_ADAPTERS
    if _PLATFORM_NAME_ADAPTERS is not None:
        return _PLATFORM_NAME_ADAPTERS
    mapping: dict[str, type] = {}
    for name, (module_path, class_name) in _NAME_ADAPTER_IMPORTS.items():
        import importlib
        mod = importlib.import_module(module_path)
        mapping[name] = getattr(mod, class_name)
    _PLATFORM_NAME_ADAPTERS = mapping
    return mapping


def publisher_key_for_platform(platform: Platform) -> str:
    """publisher_key_for_platform。

    参数说明：
    :param platform: 参数 platform
    :return: 返回处理结果。
    """
    return _publisher_key(platform)


def _publisher_key(platform: Platform) -> str:
    """平台 → PublishService 的 PUBLISHER_MAP 键；解析不出返回空串。

    历史 P0：末尾曾以 ``return "zhihu"`` 兜底，导致 Alibaba.com / Reddit / Medium 等
    30 个无键平台全部解析成 zhihu，而 zhihu 在 PUBLISHER_MAP 里是真 ZhihuPublisher，
    于是「发海外平台」实际会把内容发到知乎。现在宁缺不借：返回空串，由调用方判失败
    （见 publish_service.py:1055「禁止借用 ZhihuPublisher 占位假发」）。

    P1 补刀（09-13）：曾保留的 ``platform_type`` 兜底是同一个 bug 的另一半，实测误路由：
      · 微信视频号(type=wechat) → wechat = WeChatPublisher（微信公众号发布器）→ 串号真发
      · 头条号(type=byte) → douyin，而 douyin 在 STUB_PUBLISHER_KEYS 里，
        于是 publish_block_reason 先把「有真适配器」的头条号判成未接入，图文永远发不出去
      · 大鱼号(type=byte) → douyin，同理被冒名挡下
    现在只认两件事：显式平台名映射、以及平台名本身能 slug 成真实存在的键。
    platform_type 是粗分类（wechat/byte/social/b2b…），不允许再当作发布器键。
    """
    name = str(getattr(platform, "name", "") or "").strip()
    if name in _NAME_PUBLISHER_KEY:
        key = _NAME_PUBLISHER_KEY[name]
        if key in PUBLISHER_MAP:
            return key
    return _name_slug_key(name)


def _require_publisher_key(platform: Platform, pub_key: str) -> str:
    """无发布器键 → 明确失败，绝不改投其它平台。"""
    if not pub_key:
        raise RuntimeError(
            f"PLATFORM_NOT_IMPLEMENTED: {platform.name} 尚无可用发布器"
            "（PUBLISHER_MAP 无对应键，且未提供平台适配器），不会代发至其它平台"
        )
    return pub_key


def _note_publish_auth_failure(db: Session, account: PlatformAccount, error_text: str) -> None:
    """发布报鉴权失败时，顺手把账号置为 expired（PC-04）。"""
    from app.services.platform_session_patrol_service import note_publish_failure

    try:
        note_publish_failure(db, account, error_text, commit=True)
    except Exception:  # noqa: BLE001 — 巡检回写失败绝不影响发布结果传播
        return


def _content_payload(content: GeneratedContent) -> dict[str, Any]:
    """_content_payload。

    参数说明：
    :param content: 参数 content
    :return: 返回处理结果。
    """
    return {
        "title": content.title or "发布内容",
        "body": content.content or "",
        "content": content.content or "",
    }


class SeoPublishService:
    """seo_matrix 一键群发使用的 DB 感知发布服务。"""
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.db = db
        self._async_svc = PublishService()

    def _gate_check(
        self,
        account: PlatformAccount,
        content_text: str,
        title: str,
        chain: str = "multi_channel",
    ) -> None:
        """多平台链路双关卡（总纲 §6.4；开关默认关/异常→off，零回归）。

        清洗关硬拦截 → raise RuntimeError（与既有 publish_block_reason 拦截语义一致，
        调用方已按异常处理单渠道失败，不影响其他渠道）。复核关为标记语义（不阻断）。
        """
        tenant_id = str(getattr(account, "tenant_id", "") or "")
        if not tenant_id:
            return
        try:
            from app.services.pipeline.chains import gate_content  # noqa: PLC0415
            report = gate_content(
                self.db,
                tenant_id=tenant_id,
                title=title,
                content=content_text,
                chain=chain,
            )
        except Exception:  # noqa: BLE001 — 关卡故障不得阻断发布流（零回归）
            return
        if report.blocked:
            reasons = "; ".join(i["message"] for i in report.issues[:2])
            raise RuntimeError(f"gate_blocked: 多平台链路清洗关拦截（{reasons}）")

    def dispatch_media_content(
        self,
        platform: Platform,
        account: PlatformAccount,
        content: dict[str, Any],
    ) -> str | None:
        """视频/引流发布：携带 video_url，优先租户已绑定账号。"""
        self._gate_check(
            account,
            content.get("body") or content.get("title") or "",
            content.get("title") or "视频",
        )
        blocked = publish_block_reason(
            platform_name=platform.name,
            publisher_key=_publisher_key(platform),
            content=content,
        )
        if blocked:
            raise RuntimeError(blocked)

        gc = GeneratedContent(
            title=content.get("title") or "视频",
            content=content.get("body") or "",
            word_count=len(content.get("body") or ""),
            status="draft",
        )
        adapters = _load_name_adapters()
        adapter_cls = adapters.get(platform.name)
        if adapter_cls is not None:
            try:
                url = adapter_cls(self.db).publish(platform, account, gc)
            except Exception as exc:  # noqa: BLE001 — 原样抛出，只顺手记一次会话失效
                _note_publish_auth_failure(self.db, account, f"{type(exc).__name__}: {exc}")
                raise
            if not (url or "").strip():
                raise RuntimeError(f"{platform.name} 发布未返回作品链接，视为失败")
            return url

        pub_key = _publisher_key(platform)
        payload = {
            "title": content.get("title") or "视频",
            "body": content.get("body") or "",
            "content": content.get("body") or "",
            "video_url": content.get("video_url") or "",
            "tags": content.get("tags") or [],
        }
        _require_publisher_key(platform, pub_key)
        result = asyncio.run(self._async_svc.publish(pub_key, payload))
        if result.get("status") != "success":
            _note_publish_auth_failure(
                self.db,
                account,
                result.get("error_message") or result.get("error_code") or "",
            )
            raise RuntimeError(result.get("error_message") or f"发布到 {platform.name} 失败")
        url = (result.get("platform_post_url") or "").strip()
        if not url and not (result.get("platform_post_id") or "").strip():
            raise RuntimeError(f"{platform.name} 发布未返回作品链接，视为失败")
        return url or None

    def _dispatch_to_platform(
        self,
        platform: Platform,
        account: PlatformAccount,
        content: GeneratedContent,
    ) -> str | None:
        """_dispatch_to_platform。

        参数说明：
        :param self: 参数 self
        :param platform: 参数 platform
        :param account: 参数 account
        :param content: 参数 content
        :return: 返回处理结果。
        """
        self._gate_check(account, content.content or "", content.title or "")
        blocked = publish_block_reason(
            platform_name=platform.name,
            publisher_key=_publisher_key(platform),
            content=_content_payload(content),
        )
        if blocked:
            raise RuntimeError(blocked)

        adapters = _load_name_adapters()
        adapter_cls = adapters.get(platform.name)
        if adapter_cls is not None:
            adapter = adapter_cls(self.db)
            try:
                url = adapter.publish(platform, account, content)
            except Exception as exc:  # noqa: BLE001 — 原样抛出，只顺手记一次会话失效
                _note_publish_auth_failure(self.db, account, f"{type(exc).__name__}: {exc}")
                raise
            if not (url or "").strip():
                raise RuntimeError(f"{platform.name} 发布未返回作品链接，视为失败")
            return url

        pub_key = _publisher_key(platform)
        _require_publisher_key(platform, pub_key)
        result = asyncio.run(self._async_svc.publish(pub_key, _content_payload(content)))
        if result.get("status") != "success":
            _note_publish_auth_failure(
                self.db,
                account,
                result.get("error_message") or result.get("error_code") or "",
            )
            raise RuntimeError(result.get("error_message") or f"发布到 {platform.name} 失败")
        url = (result.get("platform_post_url") or "").strip()
        if not url and not (result.get("platform_post_id") or "").strip():
            raise RuntimeError(f"{platform.name} 发布未返回作品链接，视为失败")
        return url or None


class PublishDispatchService(SeoPublishService):
    """商业闭环与多渠道分发调度服务。"""

    async def distribute(
        self,
        tenant_id: str,
        content: dict[str, Any],
        channels: list[str] | None = None,
    ) -> dict[str, Any]:
        """多平台内容分发。

        ⚠️ 本方法此前是**假成功**：只对 channels 循环计数（`published += 1`），
           从未调用任何发布器，却恒返回 `status:"success"`。已改为调用真实的
           `_dispatch_to_platform`（跑 gate 检查 → 查平台适配器 → 真发布器 → 失败即抛错）。

        真实行为：
            · channels 必填（不再默认编造 website/blog/social_media 三个渠道）
            · 每个渠道都要在 DB 里查到 `Platform` 与租户的 `PlatformAccount`，否则该渠道判失败
            · 任一渠道失败都如实计入 failed，**不掩盖**
            · 全部失败时 `status="failed"`
        """
        if not tenant_id:
            raise ValueError("tenant_id 必填（多租户隔离红线）")
        chans = [str(c).strip() for c in (channels or []) if str(c).strip()]
        if not chans:
            raise ValueError("channels 必填：需显式指定分发渠道（不支持默认渠道）")
        if not content:
            raise ValueError("content 必填")

        # 组装 GeneratedContent（真发布链路需要）
        gen = self._build_generated_content(tenant_id, content)

        results: dict[str, Any] = {}
        succeeded = failed = 0
        for name in chans:
            platform = (
                self.db.query(Platform)
                .filter(Platform.name == name, Platform.is_active == True)  # noqa: E712
                .first()
            )
            if platform is None:
                results[name] = {"status": "failed", "error_message": f"平台未登记或已停用: {name}"}
                failed += 1
                continue

            account = (
                self.db.query(PlatformAccount)
                .filter(
                    PlatformAccount.tenant_id == tenant_id,
                    PlatformAccount.platform_id == platform.id,
                    PlatformAccount.is_active == True,  # noqa: E712
                )
                .first()
            )
            if account is None:
                results[name] = {
                    "status": "failed",
                    "error_message": f"租户未绑定该平台账号: {name}（需先在平台账号页绑定）",
                }
                failed += 1
                continue

            try:
                url = self._dispatch_to_platform(platform, account, gen)
                if not (url or "").strip():
                    raise RuntimeError("发布未返回作品链接，视为失败")
                results[name] = {"status": "success", "platform_post_url": url}
                succeeded += 1
            except Exception as exc:  # noqa: BLE001 — 单渠道失败不阻断其他渠道
                results[name] = {"status": "failed", "error_message": f"{type(exc).__name__}: {exc}"}
                failed += 1

        return {
            "channels": chans,
            "results": results,
            "published": succeeded,
            "published_count": succeeded,
            "failed_count": failed,
            "partial": 0 < succeeded < len(chans),
            # 只有真有渠道成功才算 success；否则 failed（不再恒报 success）
            "status": "success" if succeeded > 0 else "failed",
        }

    def _build_generated_content(self, tenant_id: str, content: dict[str, Any]) -> GeneratedContent:
        """由入参构造 GeneratedContent；缺必填字段即抛错（不编造占位内容）。"""
        title = str(content.get("title") or "").strip()
        body = str(content.get("body") or content.get("content") or "").strip()
        if not title:
            raise ValueError("content.title 必填")
        gen = GeneratedContent(
            tenant_id=tenant_id,
            title=title,
            content=body,
        )
        # 可选字段按需回填，缺失不编造
        for attr, key in (("summary", "summary"), ("cover_url", "cover_url")):
            val = content.get(key)
            if val is not None and hasattr(gen, attr):
                setattr(gen, attr, str(val))
        return gen

