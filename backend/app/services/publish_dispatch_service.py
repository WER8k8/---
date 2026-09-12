"""SEO 矩阵图文发布：平台适配器 + PublishService 异步回退。"""

from __future__ import annotations

import asyncio
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
}


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
    """_publisher_key。

    参数说明：
    :param platform: 参数 platform
    :return: 返回处理结果。
    """
    if platform.name in _NAME_PUBLISHER_KEY:
        key = _NAME_PUBLISHER_KEY[platform.name]
        if key in PUBLISHER_MAP:
            return key
    ptype = (platform.platform_type or "").strip().lower()
    if ptype in PUBLISHER_MAP:
        return ptype
    if ptype == "video":
        return "youtube"
    if ptype == "byte":
        return "douyin"
    return "zhihu"


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
            url = adapter_cls(self.db).publish(platform, account, gc)
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
        result = asyncio.run(self._async_svc.publish(pub_key, payload))
        if result.get("status") != "success":
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
            url = adapter.publish(platform, account, content)
            if not (url or "").strip():
                raise RuntimeError(f"{platform.name} 发布未返回作品链接，视为失败")
            return url

        pub_key = _publisher_key(platform)
        result = asyncio.run(self._async_svc.publish(pub_key, _content_payload(content)))
        if result.get("status") != "success":
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

