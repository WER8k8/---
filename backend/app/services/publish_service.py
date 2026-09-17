# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Publish Service - handles content publishing to various platforms.

Implements real API integration for:
- WeChat Official Account (微信公众号)
- Toutiao (头条号)
- Zhihu (知乎专栏)
- Facebook, Instagram, Twitter/X, LinkedIn, YouTube
"""
import asyncio
import hashlib
import hmac
import json
import os
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple

import httpx

# TODO: 高频场景改用共享 httpx.AsyncClient 实例复用连接池

from app.core.logging import get_logger
from app.data import load_platforms

logger = get_logger(__name__)

# Retry configuration
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2


async def _retry_request(
    method: str,
    url: str,
    client: httpx.AsyncClient,
    max_retries: int = MAX_RETRIES,
    **kwargs: Any,
) -> httpx.Response:
    """Execute an HTTP request with exponential backoff retry."""
    last_exc: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            response = await client.request(method, url, **kwargs)
            if response.status_code < 500:
                return response
            logger.warning(
                "Server error %d on %s, retry %d/%d",
                response.status_code, url, attempt + 1, max_retries,
            )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            last_exc = exc
            logger.warning(
                "Connection error on %s, retry %d/%d: %s",
                url, attempt + 1, max_retries, exc,
            )
        delay = RETRY_BASE_DELAY * (2 ** attempt)
        await asyncio.sleep(delay)
    if last_exc:
        raise last_exc
    msg = f"Request failed after {max_retries} retries: {url}"
    raise RuntimeError(msg)


class BasePublisher(ABC):
    """Base class for platform publishers."""

    # 子类声明本平台"真发所必需"的凭证属性名（只列主凭证，宁松勿严：
    # 宁可放行让平台真报错，也不要把其实能发的渠道误判成未配置）。
    CREDENTIAL_FIELDS: Tuple[str, ...] = ()

    def __init__(self, platform_config: Dict[str, Any]):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param platform_config: 参数 platform_config
        :return: 返回处理结果。
        """
        self.platform_config = platform_config

    def missing_credentials(self) -> list[str]:
        """返回缺失的主凭证名；非空即"渠道未配置"（尚未发起任何真实请求）。

        凭证取值口径与各 Publisher 的 __init__ 一致：先看实例属性，再看
        ``platform_config["credentials"]``（Facebook/Instagram 走后者）。
        """
        if not self.CREDENTIAL_FIELDS:
            return []
        raw = self.platform_config.get("credentials") or {}
        missing: list[str] = []
        for field in self.CREDENTIAL_FIELDS:
            if getattr(self, field, None):
                continue
            if isinstance(raw, dict) and raw.get(field):
                continue
            missing.append(field)
        return missing

    @abstractmethod
    async def publish(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Publish content to the platform.

        Args:
            content: Content data (title, body, media_urls, etc.)

        Returns:
            dict: {'status': 'success'|'failed', 'platform_post_id': str, 'platform_post_url': str, 'error_message': str}
        """
        pass

    @abstractmethod
    async def validate_credentials(self) -> bool:
        """Validate platform credentials."""
        pass


class UnimplementedPublisher(BasePublisher):
    """未接入平台 — 明确失败，禁止借用其它 Publisher 冒充成功。"""
    async def publish(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """publish。

        参数说明：
        :param self: 参数 self
        :param content: 参数 content
        :return: 返回处理结果。
        """
        platform_id = self.platform_config.get("id") or "unknown"
        from app.services.publish_capability_registry import (
            PLATFORM_NOT_IMPLEMENTED,
            publish_block_reason,
        )
        reason = publish_block_reason(
            publisher_key=str(platform_id),
            content=content,
        )
        return {
            "status": "failed",
            "error_message": reason
            or f"平台 {platform_id} 尚未接入真实发布（PLATFORM_NOT_IMPLEMENTED）",
            "error_code": PLATFORM_NOT_IMPLEMENTED,
            "configured": False,
        }

    async def validate_credentials(self) -> bool:
        """validate_credentials。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return False


# ======================================================================
# WeChat Official Account Publisher (微信公众号)
# ======================================================================

class WeChatPublisher(BasePublisher):
    """WeChat Official Account publisher — 草稿箱→发布流程.

    Uses WeChat MP API with AppID/AppSecret for access_token,
    then publishes articles as permanent materials (永久素材).
    """
    API_BASE = "https://api.weixin.qq.com"
    CREDENTIAL_FIELDS = ("appid", "appsecret")

    def __init__(self, platform_config: Dict[str, Any]):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param platform_config: 参数 platform_config
        :return: 返回处理结果。
        """
        super().__init__(platform_config)
        credentials = platform_config.get("credentials", {})
        self.appid = credentials.get("appid") or os.getenv("WECHAT_MP_APPID", "")
        self.appsecret = credentials.get("appsecret") or os.getenv("WECHAT_MP_APPSECRET", "")
        self._token: Optional[str] = None
        self._token_expires: float = 0

    async def _get_access_token(self) -> str:
        """Obtain or refresh WeChat access_token (2h TTL, refresh 5min early)."""
        now = time.time()
        if self._token and now < self._token_expires - 300:
            return self._token

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await _retry_request(
                "GET",
                f"{self.API_BASE}/cgi-bin/token",
                client,
                params={
                    "grant_type": "client_credential",
                    "appid": self.appid,
                    "secret": self.appsecret,
                },
            )
            data = resp.json()

        if "access_token" not in data:
            raise RuntimeError(
                f"WeChat access_token failed: {data.get('errmsg', 'unknown')} "
                f"(errcode={data.get('errcode')})"
            )

        self._token = data["access_token"]
        self._token_expires = now + float(data.get("expires_in", 7200))
        logger.info("WeChat access_token obtained")
        return self._token

    async def _upload_image(self, image_url: str) -> str:
        """Upload an image as permanent material, return media_id."""
        token = await self._get_access_token()
        async with httpx.AsyncClient(timeout=30) as client:
            # Download the image first
            img_resp = await _retry_request("GET", image_url, client)
            img_bytes = img_resp.content
            # Upload to WeChat
            resp = await _retry_request(
                "POST",
                f"{self.API_BASE}/cgi-bin/material/add_material",
                client,
                params={"access_token": token, "type": "image"},
                files={"media": ("image.jpg", img_bytes, "image/jpeg")},
            )
            data = resp.json()

        if "media_id" not in data:
            raise RuntimeError(f"WeChat image upload failed: {data.get('errmsg', 'unknown')}")
        return data["media_id"]

    @staticmethod
    def _to_wechat_html(content: str) -> str:
        """Convert plain/Markdown text to WeChat-compatible HTML."""
        paragraphs = content.strip().split("\n\n")
        html_parts: list[str] = []
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if para.startswith("## "):
                html_parts.append(f"<h2>{para[3:]}</h2>")
            elif para.startswith("# "):
                html_parts.append(f"<h1>{para[2:]}</h1>")
            else:
                lines = para.split("\n")
                html_parts.extend(f"<p>{line}</p>" for line in lines if line.strip())
        return "".join(html_parts)

    async def publish(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Publish article to WeChat Official Account (永久素材→群发)."""
        if not self.appid or not self.appsecret:
            return {"status": "failed", "error_message": "WeChat AppID/AppSecret not configured"}

        try:
            token = await self._get_access_token()
            title = content.get("title", "")
            body = content.get("body", "")
            html_body = self._to_wechat_html(body)
            digest = body[:120].replace("\n", " ").strip()
            media_urls = content.get("media_urls", [])
            # Upload cover image if provided
            thumb_media_id = ""
            if media_urls:
                try:
                    thumb_media_id = await self._upload_image(media_urls[0])
                except Exception as e:
                    logger.warning("WeChat cover image upload failed: %s", e)

            # Create permanent article material
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await _retry_request(
                    "POST",
                    f"{self.API_BASE}/cgi-bin/material/add_news",
                    client,
                    params={"access_token": token},
                    json={
                        "articles": [{
                            "title": title,
                            "thumb_media_id": thumb_media_id,
                            "author": content.get("author", ""),
                            "digest": digest,
                            "content": html_body,
                            "content_source_url": content.get("source_url", ""),
                            "need_open_comment": 0,
                            "only_fans_can_comment": 0,
                        }]
                    },
                )
                data = resp.json()

            if "media_id" not in data:
                return {
                    "status": "failed",
                    "error_message": f"WeChat publish failed: {data.get('errmsg', 'unknown')}",
                }

            media_id = data["media_id"]
            # Optionally mass-send (群发)
            if content.get("mass_send", False):
                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await _retry_request(
                        "POST",
                        f"{self.API_BASE}/cgi-bin/message/mass/sendall",
                        client,
                        params={"access_token": token},
                        json={
                            "filter": {"is_to_all": True},
                            "mpnews": {"media_id": media_id},
                            "msgtype": "mpnews",
                            "send_ignore_reprint": 0,
                        },
                    )
                    send_data = resp.json()
                    if send_data.get("errcode", 0) != 0:
                        logger.warning("WeChat mass send failed: %s", send_data.get("errmsg"))

            return {
                "status": "success",
                "platform_post_id": media_id,
                "platform_post_url": f"https://mp.weixin.qq.com/s?__biz=mid={media_id}",
                "error_message": None,
            }

        except Exception as e:
            logger.error("WeChat publish failed: %s", e, exc_info=True)
            return {"status": "failed", "error_message": str(e)}

    async def validate_credentials(self) -> bool:
        """Validate WeChat AppID/AppSecret by obtaining access_token."""
        if not self.appid or not self.appsecret:
            return False
        try:
            await self._get_access_token()
            return True
        except Exception:
            return False


# ======================================================================
# Toutiao Publisher (头条号)
# ======================================================================

class ToutiaoPublisher(BasePublisher):
    """Toutiao (头条号) publisher — 图文发布 via 头条号开放平台.

    Uses Cookie-based authentication or OAuth2.0.
    Official docs: https://mp.toutiao.com/
    """
    API_BASE = "https://mp.toutiao.com"
    OPEN_API_BASE = "https://open.toutiao.com"
    CREDENTIAL_FIELDS = ("cookies",)

    def __init__(self, platform_config: Dict[str, Any]):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param platform_config: 参数 platform_config
        :return: 返回处理结果。
        """
        super().__init__(platform_config)
        credentials = platform_config.get("credentials", {})
        self.cookies = credentials.get("cookies") or os.getenv("TOUTIAO_COOKIES", "")
        self.access_token = credentials.get("access_token") or os.getenv("TOUTIAO_ACCESS_TOKEN", "")
        self.client_key = credentials.get("client_key") or os.getenv("TOUTIAO_CLIENT_KEY", "")
        self.client_secret = credentials.get("client_secret") or os.getenv("TOUTIAO_CLIENT_SECRET", "")

    @staticmethod
    def _to_toutiao_html(content: str) -> str:
        """Convert content to Toutiao-compatible HTML."""
        paragraphs = content.strip().split("\n")
        return "".join(f"<p>{p.strip()}</p>" for p in paragraphs if p.strip())

    async def _oauth_authorize_url(self, redirect_uri: str, state: str = "") -> str:
        """Generate OAuth2.0 authorization URL for Toutiao."""
        if not self.client_key:
            raise RuntimeError("Toutiao client_key not configured")
        params = {
            "client_key": self.client_key,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": "article_write",
            "state": state or "toutiao_auth",
        }
        return f"{self.OPEN_API_BASE}/oauth2/authorize?{'&'.join(f'{k}={v}' for k, v in params.items())}"

    async def _exchange_token(self, code: str, redirect_uri: str) -> str:
        """Exchange authorization code for access_token."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await _retry_request(
                "POST",
                f"{self.OPEN_API_BASE}/oauth2/access_token",
                client,
                json={
                    "client_key": self.client_key,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                },
            )
            data = resp.json()

        if "access_token" not in data:
            raise RuntimeError(f"Toutiao token exchange failed: {data}")
        self.access_token = data["access_token"]
        return self.access_token

    async def publish(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Publish article to Toutiao (图文发布)."""
        try:
            title = content.get("title", "")
            body = content.get("body", "")
            html_body = self._to_toutiao_html(body)
            media_urls = content.get("media_urls", [])
            is_original = content.get("is_original", True)
            category = content.get("category", "科技")
            headers: Dict[str, str] = {"Content-Type": "application/json"}
            if self.cookies:
                headers["Cookie"] = self.cookies

            params: Dict[str, Any] = {}
            if self.access_token:
                params["access_token"] = self.access_token

            payload = {
                "title": title[:30],
                "content": html_body,
                "is_original": int(is_original),
                "category": category,
            }
            if media_urls:
                payload["cover_image"] = media_urls[0]

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await _retry_request(
                    "POST",
                    f"{self.API_BASE}/api/article/publish",
                    client,
                    params=params,
                    headers=headers,
                    json=payload,
                )
                data = resp.json()

            # Check response — Toutiao returns different formats depending on auth method
            if data.get("error_code", 0) != 0 or data.get("code", 0) != 0:
                error_msg = data.get("message") or data.get("error_message") or data.get("msg", "unknown")
                return {
                    "status": "failed",
                    "error_message": f"Toutiao publish failed: {error_msg}",
                }

            article_id = data.get("data", {}).get("article_id") or data.get("article_id", "")
            if not article_id:
                # If no article_id but no error either, treat as success with pending review
                article_id = str(data.get("data", {}).get("id", "pending"))

            return {
                "status": "success",
                "platform_post_id": str(article_id),
                "platform_post_url": f"https://www.toutiao.com/article/{article_id}/",
                "error_message": None,
            }

        except Exception as e:
            logger.error("Toutiao publish failed: %s", e, exc_info=True)
            return {"status": "failed", "error_message": str(e)}

    async def validate_credentials(self) -> bool:
        """Validate Toutiao credentials."""
        if not self.cookies and not self.access_token:
            return False
        try:
            headers: Dict[str, str] = {}
            if self.cookies:
                headers["Cookie"] = self.cookies
            params: Dict[str, Any] = {}
            if self.access_token:
                params["access_token"] = self.access_token

            async with httpx.AsyncClient(timeout=10) as client:
                resp = await _retry_request(
                    "GET",
                    f"{self.API_BASE}/api/user/info",
                    client,
                    params=params,
                    headers=headers,
                )
                data = resp.json()
                return data.get("error_code", -1) == 0 or "data" in data
        except Exception:
            return False


# ======================================================================
# Zhihu Publisher (知乎专栏)
# ======================================================================

class ZhihuPublisher(BasePublisher):
    """Zhihu (知乎专栏) publisher — 文章发布 via 知乎专栏 API.

    Uses Cookie-based authentication.
    Official docs: https://www.zhihu.com/
    """
    API_BASE = "https://www.zhihu.com/api/v4"
    ZHUANLAN_API = "https://zhuanlan.zhihu.com/api"
    CREDENTIAL_FIELDS = ("cookies",)

    def __init__(self, platform_config: Dict[str, Any]):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param platform_config: 参数 platform_config
        :return: 返回处理结果。
        """
        super().__init__(platform_config)
        credentials = platform_config.get("credentials", {})
        self.cookies = credentials.get("cookies") or os.getenv("ZHIHU_COOKIES", "")
        self.x_zse_93 = credentials.get("x_zse_93") or os.getenv("ZHIHU_X_ZSE_93", "")
        self.x_zse_96 = credentials.get("x_zse_96") or os.getenv("ZHIHU_X_ZSE_96", "")
        self.x_zse_99 = credentials.get("x_zse_99") or os.getenv("ZHIHU_X_ZSE_99", "")

    def _build_headers(self) -> Dict[str, str]:
        """Build request headers with Zhihu anti-scraping tokens."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Origin": "https://zhuanlan.zhihu.com",
            "Referer": "https://zhuanlan.zhihu.com",
        }
        if self.cookies:
            headers["Cookie"] = self.cookies
        if self.x_zse_93:
            headers["x-zse-93"] = self.x_zse_93
        if self.x_zse_96:
            headers["x-zse-96"] = self.x_zse_96
        if self.x_zse_99:
            headers["x-zse-99"] = self.x_zse_99
        return headers

    @staticmethod
    def _to_zhihu_markdown(content: str) -> str:
        """Convert content to Zhihu-compatible Markdown."""
        return content.strip()

    async def publish(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Publish article to Zhihu column (专栏文章)."""
        try:
            title = content.get("title", "")
            body = content.get("body", "")
            column_id = content.get("column_id", "")
            tags = content.get("tags", [])
            cover_image_url = content.get("cover_image_url", "")
            md_body = self._to_zhihu_markdown(body)
            headers = self._build_headers()
            payload: Dict[str, Any] = {
                "title": title,
                "content": md_body,
                "comment_permission": "all",
            }
            if cover_image_url:
                payload["title_image"] = cover_image_url
            if tags:
                payload["topics"] = tags

            # Choose endpoint based on whether a column is specified
            if column_id:
                url = f"{self.ZHUANLAN_API}/columns/{column_id}/articles"
            else:
                url = f"{self.API_BASE}/articles"

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await _retry_request(
                    "POST",
                    url,
                    client,
                    headers=headers,
                    json=payload,
                )
                data = resp.json()

            if resp.status_code not in (200, 201):
                error_msg = data.get("error", {}).get("message", "") or data.get("message", "unknown")
                return {
                    "status": "failed",
                    "error_message": f"Zhihu publish failed: {error_msg}",
                }

            article_id = data.get("id", "")
            slug = data.get("url", "").split("/")[-1] if data.get("url") else str(article_id)
            article_url = data.get("url") or f"https://zhuanlan.zhihu.com/p/{article_id}"
            return {
                "status": "success",
                "platform_post_id": str(article_id),
                "platform_post_url": article_url,
                "error_message": None,
            }

        except Exception as e:
            logger.error("Zhihu publish failed: %s", e, exc_info=True)
            return {"status": "failed", "error_message": str(e)}

    async def validate_credentials(self) -> bool:
        """Validate Zhihu credentials by fetching user info."""
        if not self.cookies:
            return False
        try:
            headers = self._build_headers()
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await _retry_request(
                    "GET",
                    f"{self.API_BASE}/me",
                    client,
                    headers=headers,
                )
                return resp.status_code == 200 and "id" in resp.json()
        except Exception:
            return False


# ======================================================================
# Facebook Publisher
# ======================================================================

class FacebookPublisher(BasePublisher):
    """Facebook publisher via Graph API."""

    CREDENTIAL_FIELDS = ("page_access_token",)

    async def publish(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Publish to Facebook page via Graph API."""
        page_access_token = self.platform_config.get("credentials", {}).get("page_access_token")
        if not page_access_token:
            return {"status": "failed", "error_message": "Missing page_access_token"}

        message = content.get("body", "")
        media_urls = content.get("media_urls", [])
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                if media_urls:
                    resp = await _retry_request(
                        "POST",
                        "https://graph.facebook.com/v18.0/me/photos",
                        client,
                        data={"access_token": page_access_token, "message": message, "url": media_urls[0]},
                    )
                else:
                    resp = await _retry_request(
                        "POST",
                        "https://graph.facebook.com/v18.0/me/feed",
                        client,
                        data={"access_token": page_access_token, "message": message},
                    )

                result = resp.json()
                if "id" in result:
                    post_id = result["id"]
                    return {
                        "status": "success",
                        "platform_post_id": post_id,
                        "platform_post_url": f"https://www.facebook.com/{post_id}",
                        "error_message": None,
                    }
                else:
                    return {"status": "failed", "error_message": result.get("error", {}).get("message", "Unknown error")}

        except Exception as e:
            logger.error("Facebook publish failed: %s", e, exc_info=True)
            return {"status": "failed", "error_message": str(e)}

    async def validate_credentials(self) -> bool:
        """Validate Facebook credentials."""
        page_access_token = self.platform_config.get("credentials", {}).get("page_access_token")
        if not page_access_token:
            return False
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://graph.facebook.com/v18.0/me",
                    params={"access_token": page_access_token},
                )
                return resp.status_code == 200
        except Exception:
            return False


# ======================================================================
# Instagram Publisher
# ======================================================================

class InstagramPublisher(BasePublisher):
    """Instagram publisher via Graph API."""

    CREDENTIAL_FIELDS = ("access_token",)

    async def publish(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Publish to Instagram via Graph API."""
        access_token = self.platform_config.get("credentials", {}).get("access_token")
        if not access_token:
            return {"status": "failed", "error_message": "Missing access_token"}

        media_urls = content.get("media_urls", [])
        if not media_urls:
            return {"status": "failed", "error_message": "Instagram requires media"}

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Step 1: Create media object
                media_resp = await _retry_request(
                    "POST",
                    "https://graph.facebook.com/v18.0/me/media",
                    client,
                    data={
                        "access_token": access_token,
                        "image_url": media_urls[0],
                        "caption": content.get("body", ""),
                    },
                )
                media_result = media_resp.json()
                if "id" not in media_result:
                    return {"status": "failed", "error_message": media_result.get("error", {}).get("message")}

                media_id = media_result["id"]
                # Step 2: Publish media
                publish_resp = await _retry_request(
                    "POST",
                    "https://graph.facebook.com/v18.0/me/media_publish",
                    client,
                    data={"access_token": access_token, "creation_id": media_id},
                )
                publish_result = publish_resp.json()
                if "id" in publish_result:
                    post_id = publish_result["id"]
                    return {
                        "status": "success",
                        "platform_post_id": post_id,
                        "platform_post_url": f"https://www.instagram.com/p/{post_id}",
                        "error_message": None,
                    }
                else:
                    return {
                        "status": "failed",
                        "error_message": publish_result.get("error", {}).get("message"),
                    }

        except Exception as e:
            logger.error("Instagram publish failed: %s", e, exc_info=True)
            return {"status": "failed", "error_message": str(e)}

    async def validate_credentials(self) -> bool:
        """Validate Instagram credentials."""
        access_token = self.platform_config.get("credentials", {}).get("access_token")
        if not access_token:
            return False
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://graph.facebook.com/v18.0/me",
                    params={"access_token": access_token, "fields": "id"},
                )
                return resp.status_code == 200
        except Exception:
            return False


# ======================================================================
# Twitter/X Publisher
# ======================================================================

class TwitterPublisher(BasePublisher):
    """Twitter/X publisher via API v2 with OAuth 2.0."""
    API_BASE = "https://api.twitter.com/2"
    UPLOAD_BASE = "https://upload.twitter.com/1.1"
    CREDENTIAL_FIELDS = ("access_token",)

    def __init__(self, platform_config: Dict[str, Any]):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param platform_config: 参数 platform_config
        :return: 返回处理结果。
        """
        super().__init__(platform_config)
        credentials = platform_config.get("credentials", {})
        self.access_token = credentials.get("access_token") or os.getenv("TWITTER_ACCESS_TOKEN", "")
        self.api_key = credentials.get("api_key") or os.getenv("TWITTER_API_KEY", "")
        self.api_secret = credentials.get("api_secret") or os.getenv("TWITTER_API_SECRET", "")
        self.access_token_secret = credentials.get("access_token_secret") or os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")

    async def publish(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Publish tweet via Twitter API v2."""
        if not self.access_token:
            return {"status": "failed", "error_message": "Twitter access_token not configured"}

        try:
            body_text = content.get("body", "")
            media_urls = content.get("media_urls", [])
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }
            tweet_data: Dict[str, Any] = {"text": body_text[:280]}
            # If media, upload first and attach media_id
            if media_urls:
                async with httpx.AsyncClient(timeout=30) as client:
                    img_resp = await _retry_request("GET", media_urls[0], client)
                    img_bytes = img_resp.content
                    upload_headers = {"Authorization": f"Bearer {self.access_token}"}
                    upload_resp = await client.post(
                        f"{self.UPLOAD_BASE}/media/upload.json",
                        headers=upload_headers,
                        files={"media": ("image.jpg", img_bytes)},
                    )
                    upload_data = upload_resp.json()
                    if "media_id_string" in upload_data:
                        tweet_data["media"] = {"media_ids": [upload_data["media_id_string"]]}

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await _retry_request(
                    "POST",
                    f"{self.API_BASE}/tweets",
                    client,
                    headers=headers,
                    json=tweet_data,
                )
                data = resp.json()

            tweet_data_resp = data.get("data", {})
            tweet_id = tweet_data_resp.get("id", "")
            if tweet_id:
                return {
                    "status": "success",
                    "platform_post_id": tweet_id,
                    "platform_post_url": f"https://twitter.com/i/status/{tweet_id}",
                    "error_message": None,
                }
            else:
                error_detail = data.get("detail", data.get("title", "unknown"))
                return {"status": "failed", "error_message": f"Twitter publish failed: {error_detail}"}

        except Exception as e:
            logger.error("Twitter publish failed: %s", e, exc_info=True)
            return {"status": "failed", "error_message": str(e)}

    async def validate_credentials(self) -> bool:
        """Validate Twitter credentials."""
        if not self.access_token:
            return False
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self.API_BASE}/users/me",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                )
                return resp.status_code == 200
        except Exception:
            return False


# ======================================================================
# LinkedIn Publisher
# ======================================================================

class LinkedInPublisher(BasePublisher):
    """LinkedIn publisher via Share on LinkedIn API."""
    API_BASE = "https://api.linkedin.com/v2"
    CREDENTIAL_FIELDS = ("access_token",)

    def __init__(self, platform_config: Dict[str, Any]):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param platform_config: 参数 platform_config
        :return: 返回处理结果。
        """
        super().__init__(platform_config)
        credentials = platform_config.get("credentials", {})
        self.access_token = credentials.get("access_token") or os.getenv("LINKEDIN_ACCESS_TOKEN", "")
        self.person_urn = credentials.get("person_urn") or os.getenv("LINKEDIN_PERSON_URN", "")

    async def publish(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Publish post to LinkedIn."""
        if not self.access_token:
            return {"status": "failed", "error_message": "LinkedIn access_token not configured"}

        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            }
            body_text = content.get("body", "")
            person_urn = self.person_urn or "urn:li:person:me"
            payload = {
                "author": person_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": body_text},
                        "shareMediaCategory": "NONE",
                    }
                },
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
            }
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await _retry_request(
                    "POST",
                    f"{self.API_BASE}/ugcPosts",
                    client,
                    headers=headers,
                    json=payload,
                )
                data = resp.json()

            post_id = data.get("id", "")
            if post_id:
                return {
                    "status": "success",
                    "platform_post_id": post_id,
                    "platform_post_url": f"https://www.linkedin.com/feed/update/{post_id}",
                    "error_message": None,
                }
            else:
                return {"status": "failed", "error_message": f"LinkedIn publish failed: {data.get('message', 'unknown')}"}

        except Exception as e:
            logger.error("LinkedIn publish failed: %s", e, exc_info=True)
            return {"status": "failed", "error_message": str(e)}

    async def validate_credentials(self) -> bool:
        """Validate LinkedIn credentials."""
        if not self.access_token:
            return False
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self.API_BASE}/me",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                )
                return resp.status_code == 200
        except Exception:
            return False


# ======================================================================
# YouTube Publisher
# ======================================================================

class YouTubePublisher(BasePublisher):
    """YouTube publisher via Data API v3."""
    API_BASE = "https://www.googleapis.com/youtube/v3"
    UPLOAD_BASE = "https://www.googleapis.com/upload/youtube/v3"
    CREDENTIAL_FIELDS = ("access_token",)

    def __init__(self, platform_config: Dict[str, Any]):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param platform_config: 参数 platform_config
        :return: 返回处理结果。
        """
        super().__init__(platform_config)
        credentials = platform_config.get("credentials", {})
        self.access_token = credentials.get("access_token") or os.getenv("YOUTUBE_ACCESS_TOKEN", "")

    async def publish(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Publish video to YouTube."""
        if not self.access_token:
            return {"status": "failed", "error_message": "YouTube access_token not configured"}

        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "snippet": {
                    "title": content.get("title", ""),
                    "description": content.get("body", ""),
                    "tags": content.get("tags", []),
                },
                "status": {"privacyStatus": content.get("privacy", "public")},
            }
            # Note: Real video upload requires multipart/resumable upload
            # This creates the video metadata; actual video file upload needs the resumable endpoint
            video_url = content.get("video_url", "")
            if not video_url:
                return {"status": "failed", "error_message": "YouTube requires a video_url"}

            async with httpx.AsyncClient(timeout=60) as client:
                # Download video
                vid_resp = await _retry_request("GET", video_url, client)
                vid_bytes = vid_resp.content
                # Upload with metadata
                upload_resp = await client.post(
                    f"{self.UPLOAD_BASE}/videos?uploadType=multipart&part=snippet,status",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    files={
                        "metadata": (None, json.dumps(payload).encode(), "application/json"),
                        "media": ("video.mp4", vid_bytes, "video/mp4"),
                    },
                )
                data = upload_resp.json()

            video_id = data.get("id", "")
            if video_id:
                return {
                    "status": "success",
                    "platform_post_id": video_id,
                    "platform_post_url": f"https://youtube.com/watch?v={video_id}",
                    "error_message": None,
                }
            else:
                return {"status": "failed", "error_message": f"YouTube publish failed: {data.get('error', {}).get('message', 'unknown')}"}

        except Exception as e:
            logger.error("YouTube publish failed: %s", e, exc_info=True)
            return {"status": "failed", "error_message": str(e)}

    async def validate_credentials(self) -> bool:
        """Validate YouTube credentials."""
        if not self.access_token:
            return False
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self.API_BASE}/channels?part=snippet&mine=true",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                )
                return resp.status_code == 200
        except Exception:
            return False


# ======================================================================
# Publisher Map
# ======================================================================

PUBLISHER_MAP = {
    "facebook": FacebookPublisher,
    "instagram": InstagramPublisher,
    "twitter": TwitterPublisher,
    "linkedin": LinkedInPublisher,
    "youtube": YouTubePublisher,
    "wechat": WeChatPublisher,
    "toutiao": ToutiaoPublisher,
    "zhihu": ZhihuPublisher,
    # 以下平台尚未接入 — 使用 UnimplementedPublisher，禁止借用 ZhihuPublisher 占位假发
    "pinterest": UnimplementedPublisher,
    "snapchat": UnimplementedPublisher,
    "reddit": UnimplementedPublisher,
    "tumblr": UnimplementedPublisher,
    "weibo": UnimplementedPublisher,
    "douyin": UnimplementedPublisher,
    "kuaishou": UnimplementedPublisher,
    "bilibili": UnimplementedPublisher,
    "tmall": UnimplementedPublisher,
    "taobao": UnimplementedPublisher,
    "jd": UnimplementedPublisher,
    "pinduoduo": UnimplementedPublisher,
    "amazon": UnimplementedPublisher,
    "ebay": UnimplementedPublisher,
    "shopify": UnimplementedPublisher,
    "woocommerce": UnimplementedPublisher,
    "magento": UnimplementedPublisher,
    "bigcommerce": UnimplementedPublisher,
    "wix": UnimplementedPublisher,
    "squarespace": UnimplementedPublisher,
    "wordpress": UnimplementedPublisher,
    "blogger": UnimplementedPublisher,
    "medium": UnimplementedPublisher,
    "substack": UnimplementedPublisher,
    "telegram": UnimplementedPublisher,
    "whatsapp_business": UnimplementedPublisher,
    "discord": UnimplementedPublisher,
    "slack": UnimplementedPublisher,
    "google_business": UnimplementedPublisher,
    "yelp": UnimplementedPublisher,
    "tripadvisor": UnimplementedPublisher,
    "wordpress_com": UnimplementedPublisher,
    "linkedin_company": UnimplementedPublisher,
    "tiktok": UnimplementedPublisher,
    # --- 09-13 全平台对齐补齐（PC-05）-------------------------------------------
    # 这些是 platforms 表目录里有、但既无真发 Publisher 也无平台适配器的渠道。
    # 过去它们要么解析不出键、要么被 platform_type 兜底借到 douyin/wechat，
    # 要么在 publish_block_reason 里查不到身份而被判「已放行」。现在各给一个显式键，
    # 全部挂 UnimplementedPublisher：命中即返回 PLATFORM_NOT_IMPLEMENTED，不发起任何请求。
    # 接入真发时，把对应行的类换成真 Publisher 并同步 STUB_PUBLISHER_KEYS 即可。
    "wechat_channels": UnimplementedPublisher,      # 微信视频号（≠ 微信公众号 wechat）
    "qieehao": UnimplementedPublisher,              # 企鹅号
    "wangyi_hao": UnimplementedPublisher,           # 网易号
    "sohu_hao": UnimplementedPublisher,             # 搜狐号
    "yidianzixun": UnimplementedPublisher,          # 一点资讯
    "dayuhao": UnimplementedPublisher,              # 大鱼号
    "jianshu": UnimplementedPublisher,              # 简书
    "maimai": UnimplementedPublisher,               # 脉脉
    "taobao_guangguang": UnimplementedPublisher,    # 淘宝逛逛
    "ali1688": UnimplementedPublisher,              # 1688
    "huizhong": UnimplementedPublisher,             # 慧聪网
    "line_official": UnimplementedPublisher,        # LINE Official
    "zalo": UnimplementedPublisher,                 # Zalo
    "vk": UnimplementedPublisher,                   # VK
    "quora": UnimplementedPublisher,                # Quora
    "amazon_seller": UnimplementedPublisher,        # Amazon Seller（≠ 电商 amazon 键）
    "tradekey": UnimplementedPublisher,             # TradeKey
    "kompass": UnimplementedPublisher,              # Kompass
    "thomasnet": UnimplementedPublisher,            # Thomasnet
    "aliexpress": UnimplementedPublisher,           # AliExpress
    "shopee": UnimplementedPublisher,               # Shopee
    "lazada": UnimplementedPublisher,               # Lazada
}


class PublishService:
    """Service to publish content to platforms."""
    def __init__(self, db: Any = None):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 可选 SQLAlchemy 会话；传入则复用调用方连接读平台目录，
                   不传则由 ``app.data.load_platforms`` 自开短会话（库不可用时退回 JSON）。
                   注：``api/v1/routes/platform.py`` 一直按 ``PublishService(db)`` 调用，
                   旧签名不接受参数，会让那批路由直接 TypeError。
        :return: 返回处理结果。
        """
        self.db = db
        self.platforms = load_platforms(db)

    def find_platform_config(self, platform_ref: str) -> Optional[Dict[str, Any]]:
        """按发布器键或平台显示名找配置（channels 里两种写法都可能出现）。

        多租户提醒：当前一条平台只带一个账号的凭证，跨租户共用同一发布器键时
        取库里的第一条；凭证真正铺开前，需按 tenant_id 过滤（见 platform_accounts.tenant_id）。
        """
        ref = (platform_ref or "").strip()
        if not ref:
            return None
        lowered = ref.lower()
        for item in self.platforms:
            pid = str(item.get("id") or "")
            name = str(item.get("name") or "")
            if pid == ref or name == ref or pid.lower() == lowered or name.lower() == lowered:
                return item
        return None

    async def publish(self, platform_id: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """Publish content to a platform.

        Args:
            platform_id: Platform ID (e.g., 'facebook').
            content: Content data.

        Returns:
            dict: Publish result.
        """
        from app.services.publish_capability_registry import (
            PLATFORM_NOT_CONFIGURED,
            PLATFORM_NOT_IMPLEMENTED,
            normalize_publish_result,
        )

        platform_config = self.find_platform_config(platform_id)
        if not platform_config:
            # 平台目录里没有这一项：属"环境/数据未配"，不是业务失败
            logger.error("Platform not in catalog: %s", platform_id)
            return normalize_publish_result(
                {
                    "status": "failed",
                    "error_code": PLATFORM_NOT_CONFIGURED,
                    "configured": False,
                    "error_message": (
                        f"{platform_id} 不在平台目录（platforms 表未登记、且无 platforms.json 兜底），"
                        "无法发布"
                    ),
                }
            )

        publisher_key = str(
            platform_config.get("publisher_key") or platform_config.get("id") or platform_id
        ).strip()
        publisher_class = PUBLISHER_MAP.get(publisher_key)
        if publisher_class is None:
            logger.error("Unsupported platform: %s", publisher_key)
            return normalize_publish_result(
                {
                    "status": "failed",
                    "error_code": PLATFORM_NOT_IMPLEMENTED,
                    "configured": False,
                    "error_message": (
                        f"{platform_config.get('name') or publisher_key} 尚未接入真实发布器"
                        f"（PUBLISHER_MAP 无 {publisher_key}）"
                    ),
                }
            )

        # 发布器内部按 config["id"] 取键（如日志、错误文案），统一成发布器键
        config = dict(platform_config)
        config["id"] = publisher_key
        publisher = publisher_class(config)

        # 主凭证缺失 → 不发起真实请求，直接以结构化错误码返回。
        # 状态仍是 failed（对现有调用方语义不变），但带上 configured/error_code，
        # 让编排层能区分「环境没配」与「配了但真发失败」，从而记 skipped 而不是把整条链判死。
        missing = publisher.missing_credentials()
        if missing:
            return normalize_publish_result(
                {
                    "status": "failed",
                    "error_code": PLATFORM_NOT_CONFIGURED,
                    "configured": False,
                    "missing_credentials": missing,
                    "error_message": (
                        f"{platform_config.get('name') or publisher_key} 渠道凭证未配置：{', '.join(missing)}"
                        "（补齐平台配置或环境变量后才能真发）"
                    ),
                }
            )

        logger.info("Publishing to %s (ref=%s)", publisher_key, platform_id)
        result = await publisher.publish(content)
        return normalize_publish_result(result)

    async def validate_platform_credentials(self, platform_id: str, credentials: Dict[str, Any]) -> bool:
        """Validate credentials for a platform."""
        if platform_id not in PUBLISHER_MAP:
            return False

        platform_config = {"credentials": credentials}
        publisher_class = PUBLISHER_MAP[platform_id]
        publisher = publisher_class(platform_config)
        return await publisher.validate_credentials()
