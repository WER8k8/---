# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""海外 B2B 拓客适配器 — Alibaba 国际站 / Made-in-China / GlobalSources。

对应缺口 #1（海外 B2B 空白）。遵守 publish_capability_registry 铁律：
多 Worker 真发、禁止假成功。

- 凭证缺失 → 返回 PLATFORM_NOT_CONFIGURED（未发起真实请求）。
- 平台未开 API 或有强审核（如 Alibaba 需商家后台授权）→ 返回
  PLATFORM_NOT_CONFIGURED 并附 blocked_reason，绝不静默假成功。
- 走「商品 feed 提交」而非「网页长文」：把 product_feed 的记录喂给平台，
  对齐 C 组 B2B 的获取逻辑。

本模块只做「凭证/请求编排 + 平台端点封装」，feed 内容由
services/geo/product_feed 生成，可离线单测。
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, Optional

import httpx

from app.models.content import GeneratedContent, Platform, PlatformAccount
from app.services.geo.product_feed import build_feed_record
from app.services.geo.content_kernel import FactKernel
from app.services.platform_credential_guide import (
    CREDENTIAL_STORAGE,
    missing_from,
)
from app.services.publish_capability_registry import PLATFORM_NOT_CONFIGURED

logger = logging.getLogger(__name__)

# 凭证必填组的真源在 platform_credential_guide（账号 API / 适配器 / 前端指引同一口径）；
# 这里只列「可用字段全集」，供取值与 env 兜底用。
_B2B_CREDENTIAL_FIELDS: Dict[str, tuple[str, ...]] = {
    "alibaba": ("alibaba_member_id", "alibaba_access_token", "alibaba_session_cookie"),
    "made_in_china": ("mic_access_token",),
    "globalsources": ("gs_api_key",),
}

# 平台只回 offer_id 时的商品详情页模板。拼出来的链接会在结果里标
# url_source=constructed_from_offer_id，让运维看得见「这条不是平台直返的」。
OFFER_URL_TEMPLATES: Dict[str, str] = {
    "alibaba": "https://www.alibaba.com/product-detail/_.html?objectId={offer_id}",
    "made_in_china": "https://www.made-in-china.com/products/{offer_id}.html",
}


class B2BGlobalPublisher:
    """海外 B2B 平台真发适配器（Alibaba / MIC / GlobalSources）。"""

    API_ENDPOINTS: Dict[str, str] = {
        "alibaba": "https://api.alibaba.com/openapi/param2/1/com.alibaba.intl/offer.create/{member_id}",
        "made_in_china": "https://openapi.made-in-china.com/v2/product/feed",
        "globalsources": "https://api.globalsources.com/v1/product/upload",
    }

    def __init__(self, platform: str, credentials: Optional[Dict[str, Any]] = None):
        self.platform = platform
        self.credentials = dict(credentials or {})

    # ------------------------------------------------------------------
    def missing_credentials(self) -> list[str]:
        """缺哪些主凭证（按必填组，组内任一字段有值即通过）。非空即未发起真实请求。"""
        merged = dict(self.credentials)
        for field in _B2B_CREDENTIAL_FIELDS.get(self.platform, ()):
            if str(merged.get(field) or "").strip():
                continue
            env_value = os.getenv(field.upper(), "").strip()
            if env_value:
                merged[field] = env_value
        return missing_from(merged, self.platform)

    def configured(self) -> bool:
        return not self.missing_credentials()

    # ------------------------------------------------------------------
    async def publish_offer(
        self,
        kernel: FactKernel,
        feed_platform: str = "alibaba_offer",
    ) -> Dict[str, Any]:
        """把事实内核经商品 feed 投影后真发到 B2B 平台。

        铁律：缺凭证直接返回 PLATFORM_NOT_CONFIGURED，不编造成功。
        """
        if not self.configured():
            return {
                "status": "failed",
                "error_code": PLATFORM_NOT_CONFIGURED,
                "missing_credentials": self.missing_credentials(),
                "error_message": (
                    f"{self.platform} 未配置凭证（{self.missing_credentials()}），未发起真实请求"
                ),
            }

        record = build_feed_record(kernel, feed_platform)
        if record["incomplete"]:
            # 内核降级：如实上报缺字段，仍不冒充完整 offer 已提交
            logger.warning(
                "B2B offer 内核降级 platform=%s missing=%s",
                self.platform,
                record["missing_fields"],
            )

        return await self._submit(record)

    async def _submit(self, record: Dict[str, Any]) -> Dict[str, Any]:
        try:
            client = httpx.AsyncClient(timeout=30)
        except Exception as exc:  # pragma: no cover - 客户端构造极少失败
            return {"status": "failed", "error_message": f"client init failed: {exc}"}

        async with client:
            try:
                if self.platform == "alibaba":
                    member_id = (
                        self.credentials.get("alibaba_member_id")
                        or os.getenv("ALIBABA_MEMBER_ID", "")
                    )
                    url = self.API_ENDPOINTS["alibaba"].replace("{member_id}", member_id)
                    access_token = (
                        self.credentials.get("alibaba_access_token")
                        or os.getenv("ALIBABA_ACCESS_TOKEN", "")
                    )
                    headers = {"Content-Type": "application/json"}
                    if access_token:
                        # 开放平台 OAuth：商家授权后的 access_token（合规路径）
                        headers["Authorization"] = f"Bearer {access_token}"
                    else:
                        # 兜底：卖家后台会话 Cookie（非官方自动化，指引里已标风控风险）
                        headers["Cookie"] = (
                            self.credentials.get("alibaba_session_cookie")
                            or os.getenv("ALIBABA_SESSION_COOKIE", "")
                        )
                    resp = await client.post(url, json=record, headers=headers)
                elif self.platform == "made_in_china":
                    token = self.credentials.get("mic_access_token") or os.getenv("MIC_ACCESS_TOKEN", "")
                    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                    resp = await client.post(self.API_ENDPOINTS["made_in_china"], json=record, headers=headers)
                else:  # globalsources
                    key = self.credentials.get("gs_api_key") or os.getenv("GS_API_KEY", "")
                    headers = {"X-API-Key": key, "Content-Type": "application/json"}
                    resp = await client.post(self.API_ENDPOINTS["globalsources"], json=record, headers=headers)

                data = resp.json() if resp.content else {}
                if not isinstance(data, dict):
                    data = {}
                nested = data.get("data") if isinstance(data.get("data"), dict) else {}
                if resp.status_code < 400 and data.get("success") is not False:
                    offer_id = str(
                        data.get("offer_id") or nested.get("id") or data.get("id", "")
                    )
                    post_url = str(
                        data.get("url") or data.get("product_url") or nested.get("url") or ""
                    ).strip()
                    url_source = "platform" if post_url else ""
                    if not post_url and offer_id:
                        template = OFFER_URL_TEMPLATES.get(self.platform, "")
                        if template:
                            post_url = template.replace("{offer_id}", offer_id)
                            url_source = "constructed_from_offer_id"
                    return {
                        "status": "success",
                        "platform": self.platform,
                        "platform_post_id": offer_id,
                        "platform_post_url": post_url,
                        "url_source": url_source,
                        "incomplete": record["incomplete"],
                        "error_message": None,
                    }
                return {
                    "status": "failed",
                    "error_code": "PLATFORM_ERROR",
                    "error_message": f"{self.platform} HTTP {resp.status_code}: {data}",
                }
            except Exception as exc:
                logger.error("B2B publish failed %s: %s", self.platform, exc, exc_info=True)
                return {"status": "failed", "error_message": str(exc)}

    async def validate_credentials(self) -> bool:
        """轻量校验：只查凭证齐备，不真发（避免误触发平台审核）。"""
        return self.configured()


class B2BPublisherAdapter:
    """发布主链（SeoPublishService）用的 B2B 适配器基类。

    范式与国内平台一致：__init__(db) + publish(platform, account, content) -> str。
    差别在于 B2B 走「商品 offer / feed 提交」，因此先把内容投影成 FactKernel，
    再交 B2BGlobalPublisher 真发。凭证取值顺序：PlatformConfig → cookie_data →
    token_data → 环境变量（前三者由 platform_account_service.collect_credentials 合并）。

    铁律：
      · 缺凭证 → raise（消息含 PLATFORM_NOT_CONFIGURED，任务落 failed，不假成功）
      · 平台未回作品链接 → raise（不拿官网 URL 冒充平台作品链接）
    """

    PLATFORM_KEY = ""
    FEED_PLATFORM = "generic"

    def __init__(self, db=None):
        self.db = db

    # ------------------------------------------------------------------
    def _credentials(self, platform: Platform, account: PlatformAccount) -> Dict[str, Any]:
        """从账号（token_data / cookie_data / PlatformConfig）取该平台可用凭证字段。"""
        if self.db is not None:
            from app.services.platform_account_service import collect_credentials

            merged = collect_credentials(self.db, account, platform)
        else:
            merged = dict(account.token_data or {}) if isinstance(account.token_data, dict) else {}
            if account.cookie_data:
                merged.setdefault("cookie", account.cookie_data)

        creds: Dict[str, Any] = {}
        for field in _B2B_CREDENTIAL_FIELDS.get(self.PLATFORM_KEY, ()):
            value = merged.get(field)
            if not value and CREDENTIAL_STORAGE.get(field) == "cookie":
                value = merged.get("cookie")
            if value:
                creds[field] = str(value)
        return creds

    @staticmethod
    def _kernel_from_content(content: GeneratedContent) -> FactKernel:
        """把图文内容投影成最小事实内核（供 offer 投影用）。

        只保证「有标题有正文」；贸易条款等硬事实缺失由 build_feed_record 置
        incomplete=true 如实上报，不编造 offer 完整性。
        """
        return FactKernel.from_dict(
            {
                "entity_name": (content.title or "").strip() or "未命名产品",
                "entity_type": "product",
                "copy": {"en": (content.content or "").strip()},
                "source_tenant": str(getattr(content, "tenant_id", "") or ""),
            }
        )

    def publish(
        self,
        platform: Platform,
        account: PlatformAccount,
        content: GeneratedContent,
    ) -> str:
        """同步入口（发布主链按同步调用），内部驱动异步真发。"""
        publisher = B2BGlobalPublisher(
            self.PLATFORM_KEY, credentials=self._credentials(platform, account)
        )
        missing = publisher.missing_credentials()
        if missing:
            raise RuntimeError(
                f"{platform.name} {PLATFORM_NOT_CONFIGURED}："
                f"缺少凭证 {missing}（填到 平台账号凭证，或 backend/.env）"
            )
        result = asyncio.run(
            publisher.publish_offer(
                self._kernel_from_content(content),
                feed_platform=self.FEED_PLATFORM,
            )
        )
        if result.get("status") != "success":
            code = result.get("error_code") or "PLATFORM_ERROR"
            raise RuntimeError(
                f"{platform.name} offer 提交失败（{code}）："
                f"{result.get('error_message') or '平台未给出原因'}"
            )
        url = str(result.get("platform_post_url") or "").strip()
        if not url:
            raise RuntimeError(
                f"{platform.name} 已提交 offer 但平台未返回作品链接，视为失败"
                f"（platform_post_id={result.get('platform_post_id') or '空'}）"
            )
        logger.info(
            "B2B offer 提交完成 platform=%s account=%s url_source=%s incomplete=%s",
            platform.name,
            account.id,
            result.get("url_source"),
            result.get("incomplete"),
        )
        return url


class AlibabaPublisherAdapter(B2BPublisherAdapter):
    """阿里国际站商品 offer 提交适配器。"""

    PLATFORM_KEY = "alibaba"
    FEED_PLATFORM = "alibaba_offer"


class MadeInChinaPublisherAdapter(B2BPublisherAdapter):
    """中国制造网商品 feed 提交适配器。"""

    PLATFORM_KEY = "made_in_china"
    FEED_PLATFORM = "made_in_china"


class GlobalSourcesPublisherAdapter(B2BPublisherAdapter):
    """环球资源商品上传接口适配器。"""

    PLATFORM_KEY = "globalsources"
    FEED_PLATFORM = "generic"


__all__ = [
    "B2BGlobalPublisher",
    "B2BPublisherAdapter",
    "AlibabaPublisherAdapter",
    "MadeInChinaPublisherAdapter",
    "GlobalSourcesPublisherAdapter",
    "OFFER_URL_TEMPLATES",
]
