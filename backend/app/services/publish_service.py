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
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import httpx
from sqlalchemy import func

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

    # ══════════════════════════════════════════════════════════════════
    # 模块5 · M1 五个发布面方法（契约 §3.1-3.5）
    #
    # 总原则（裁-6 / §3）：**禁止新造第三套发布机制**。
    #   · 本组方法**只建任务**（写 publish_tasks = publish_jobs），**不真发**；
    #   · 真发一律委托 §2.4 既有执行机（app.workers.publish_worker），严禁另起炉灶。
    #   · 不复用 content_master_publish_service._publish_single_platform：其形参耦合
    #     调用方的 drafts/gate_cache/tenant 对象，语义是「草稿→平台匹配」，与 M1
    #     「指定平台+账号建任务」不同；强行复用需重构既有发布路径（风险高于收益）。
    #     UTM/gate 属真发时机逻辑，由执行机侧既有链路处理，本组不复制。
    # R6：发布域 tenant_id 为 varchar(36)、内容域为 uuid → 跨域比较一律显式 str()/cast 归一。
    # R7：content_id 双解析（content_masters.id → generated_contents.id 回溯）；
    #     content_asset_id 一律落 content_masters.id。
    # R8：ORM 无 finished_at → 复用既有 published_at，不加新列。
    # ══════════════════════════════════════════════════════════════════

    @staticmethod
    def _serialize_publish_task(t: Any) -> Dict[str, Any]:
        """与 routes/unified_publish._serialize_task 字段对齐，并补 publish_jobs 新列。"""

        def _iso(v: Any) -> Optional[str]:
            return v.isoformat() if v else None

        return {
            "id": t.id,
            "content_master_id": t.content_master_id,
            "content_asset_id": getattr(t, "content_asset_id", None),
            "platform_id": t.platform_id,
            "account_id": t.account_id,
            "region": t.region,
            "status": t.status,
            "publish_type": t.publish_type,
            "primary_url": t.primary_url,
            "secondary_url": t.secondary_url,
            "published_url": t.published_url,
            "error_message": t.error_message,
            "error_code": getattr(t, "error_code", None),
            "external_id": getattr(t, "external_id", None),
            "idempotency_key": getattr(t, "idempotency_key", None),
            "retry_count": t.retry_count,
            "scheduled_time": _iso(t.scheduled_time),
            "created_at": _iso(t.created_at),
            "published_at": _iso(t.published_at),
        }

    def _resolve_content_asset_id(self, content_id: str) -> str:
        """R7 双解析：① content_masters.id；② generated_contents.id → 回溯其所属 master。

        :raises ValueError: 两条路径都解析不到（端点已 except ValueError → 400）。
        """
        from app.models.content import GeneratedContent
        from app.models.content_master import ContentMaster

        db = self.db
        cid = str(content_id or "").strip()
        if not cid:
            raise ValueError("内容不存在或不可发布")

        # ① 直接命中 content_masters.id
        if db.query(ContentMaster).filter(ContentMaster.id == cid).first() is not None:
            return cid

        # ② 按 generated_contents.id 回溯所属 master
        gen = db.query(GeneratedContent).filter(GeneratedContent.id == cid).first()
        if gen is not None:
            for attr in ("content_master_id", "master_id"):
                master_id = getattr(gen, attr, None)
                if master_id:
                    return str(master_id)

        raise ValueError("内容不存在或不可发布")

    def resolve_publish_credential(self, tenant_id: str, platform_id: str,
                                   account_id: Optional[str] = None) -> Dict[str, Any]:
        """发布凭据唯一出口（契约 §4 · M2/M5，fail-closed 收口）。

        优先级（§4.3 四级）：
          ① ``platform_accounts.credential_ref`` 非空 →
             ``CredentialVaultService.resolve_credential``（M5 接线）
          ② ``platform_accounts.token_data / cookie_data`` → ``tenant_account``
          ③ ``platform_configs`` 键值表 ``operator_account=true`` →
             ``platform_operator``（默认关；缺行即关）
          ④ 都空 → ``source="none"`` + ``error_code="credential_missing"``

        **fail-closed（裁-5 硬规则）**：租户作用域**严禁 env 兜底**——
        本方法返回空时，调用方必须把该平台判为 ``credential_missing`` 并跳过，
        不得回落 ``os.getenv``。
        """
        from app.models.content import PlatformAccount, PlatformConfig

        db = self.db
        tid = str(tenant_id or "").strip()

        q = db.query(PlatformAccount).filter(
            PlatformAccount.platform_id == str(platform_id),
            PlatformAccount.is_active.is_(True),
        )
        if tid:
            # 同域比较：platform_accounts.tenant_id 与 content_masters.tenant_id **同为 uuid**，
            # 交给 UUID_TYPE TypeDecorator 归一参数即可。
            # ⚠ 禁止 cast(... AS VARCHAR)：实测会暴露底层存储形态（sqlite 为 32hex），
            #   与 36 字符带横线串永不相等 → 查询恒 0（曾致 M1 正向用例全 fail）。
            q = q.filter(PlatformAccount.tenant_id == tid)
        if account_id:
            q = q.filter(PlatformAccount.id == str(account_id))
        account = q.first()

        if account is None:
            return {"source": "none", "values": {}, "account_id": None,
                    "credential_ref": None, "error_code": "credential_missing"}

        # ── 优先级 ①：credential_ref → Vault（M5 接线，契约 §4.3）────────
        # R9：credential_ref 列由迁移 133 并入建立；非空即走 Vault 解密。
        # AAD 四元绑定按 §4.3：owner_type="tenant" / owner_id=tenant_id /
        # connection_type="platform" / connection_id=platform_id。
        cred_ref = getattr(account, "credential_ref", None)
        if cred_ref:
            try:
                from app.services.vault.credential_service import CredentialVaultService

                vault = CredentialVaultService(db)
                plaintext = vault.resolve_credential(
                    str(cred_ref),
                    tenant_id=tid or None,
                    owner_type="tenant",
                    owner_id=tid,
                    connection_type="platform",
                    connection_id=str(platform_id),
                    # 2026-09-28 修正：原值 "platform_credential" 不在 vault ARTIFACT_TYPES
                    # 词表（resolve 恒抛 VaultError→fail-closed），M5 测试因全程 mock
                    # 未触雷。统一两侧为合法词 "api_token"（M6 connect 同源），AAD 才能匹配。
                    artifact_type="api_token",
                )
                return {"source": "vault", "values": {"_vault_resolved": plaintext},
                        "account_id": str(account.id),
                        "credential_ref": str(cred_ref),
                        "error_code": None}
            except Exception as exc:  # 含 CredentialNotFoundError / Revoked / AAD Mismatch
                # fail-closed：Vault 解析失败**不回退**明文列，直接 credential_missing
                logger.warning(
                    "Vault credential_ref 解析失败（fail-closed 不回退）"
                    " ref=%s platform=%s: %s", cred_ref, platform_id, exc,
                )
                return {"source": "none", "values": {}, "account_id": str(account.id),
                        "credential_ref": str(cred_ref),
                        "error_code": "credential_missing"}

        values: Dict[str, Any] = {}
        token_data = getattr(account, "token_data", None) or {}
        if isinstance(token_data, dict):
            values.update({k: v for k, v in token_data.items() if v})
        cookie_data = getattr(account, "cookie_data", None)
        if cookie_data:
            values["cookie_data"] = cookie_data

        if values:
            return {"source": "tenant_account", "values": values,
                    "account_id": str(account.id),
                    "credential_ref": getattr(account, "credential_ref", None),
                    "error_code": None}

        # 优先级 ③：platform_configs 键值表（R3 零迁移：缺行即关）
        cfg = (
            db.query(PlatformConfig)
            .filter(
                PlatformConfig.platform_id == str(platform_id),
                PlatformConfig.config_key == "operator_account",
            )
            .first()
        )
        raw = str((cfg.config_value if cfg else "") or "").strip().lower()
        if raw in ("true", "1", "yes", "on"):
            return {"source": "platform_operator", "values": {},
                    "account_id": str(account.id),
                    "credential_ref": getattr(account, "credential_ref", None),
                    "error_code": None}

        return {"source": "none", "values": {}, "account_id": str(account.id),
                "credential_ref": getattr(account, "credential_ref", None),
                "error_code": "credential_missing"}

    def publish_content(
        self,
        *,
        content_id: str,
        platform_ids: list,
        account_ids: list,
        publish_type: str = "immediate",
        scheduled_time: Any = None,
    ) -> Dict[str, Any]:
        """为一篇内容在多个平台各建一条发布任务（1 Content → N Platform Attempts）。

        只建任务不真发；幂等键同键重提复用既有行且 task_count 不增。
        :raises ValueError: 内容解析失败 / 平台未登记或未启用（端点 → 400）。
        """
        from app.models.content import Platform, PublishTask
        from app.models.content_master import ContentMaster

        db = self.db
        if db is None:
            raise ValueError("缺少数据库会话")

        asset_id = self._resolve_content_asset_id(content_id)
        master = db.query(ContentMaster).filter(ContentMaster.id == asset_id).first()
        if master is None:
            raise ValueError("内容不存在或不可发布")
        tenant_id = str(master.tenant_id) if getattr(master, "tenant_id", None) else ""

        task_ids: list = []
        skipped: list = []
        created_count = 0

        for idx, platform_id in enumerate(platform_ids or []):
            pid = str(platform_id)
            plat = (
                db.query(Platform)
                .filter(Platform.id == pid, Platform.is_active.is_(True))
                .first()
            )
            if plat is None:
                raise ValueError(f"平台不可用或未登记: {pid}")

            account_id = account_ids[idx] if idx < len(account_ids or []) else None
            if not account_id:
                skipped.append({"platform_id": pid, "reason": "account_missing"})
                continue

            cred = self.resolve_publish_credential(tenant_id, pid, str(account_id))
            if cred.get("error_code") == "credential_missing" or not cred.get("values"):
                # 裁-5 fail-closed：凭据缺失进 skipped，**不用 env 顶上**
                skipped.append({"platform_id": pid, "reason": "credential_missing"})
                continue

            key = f"pub:{tenant_id}:{asset_id}:{pid}:{account_id}:v1"
            existing = (
                db.query(PublishTask)
                .filter(PublishTask.idempotency_key == key)
                .first()
            )
            if existing is not None:
                task_ids.append(str(existing.id))  # 幂等：复用既有行，task_count 不增
                continue

            task = PublishTask(
                content_master_id=asset_id,
                content_asset_id=asset_id,
                platform_id=pid,
                account_id=str(account_id),
                tenant_id=tenant_id or None,   # R6：发布域 varchar(36)，存 uuid 字符串形式
                status="pending",
                publish_type=publish_type or "immediate",
                scheduled_time=scheduled_time,
                idempotency_key=key,
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            task_ids.append(str(task.id))
            created_count += 1

        return {"task_count": created_count, "task_ids": task_ids, "skipped": skipped}

    def batch_publish(self, tasks: list) -> list:
        """批量发布：内部循环调 publish_content（契约 §3.2）。"""
        results: list = []
        for item in tasks or []:
            if not isinstance(item, dict):
                continue
            results.append(
                self.publish_content(
                    content_id=item.get("content_id"),
                    platform_ids=item.get("platform_ids") or [],
                    account_ids=item.get("account_ids") or [],
                    publish_type=item.get("publish_type", "immediate"),
                    scheduled_time=item.get("scheduled_time"),
                )
            )
        return results

    async def schedule_publish(
        self,
        *,
        content_id: str,
        platform_ids: list,
        account_ids: list,
        scheduled_time: Any,
    ) -> Dict[str, Any]:
        """定时发布：建 pending + publish_type=scheduled 的任务，到期由执行机真发。"""
        return self.publish_content(
            content_id=content_id,
            platform_ids=platform_ids,
            account_ids=account_ids,
            publish_type="scheduled",
            scheduled_time=scheduled_time,
        )

    def get_publish_tasks(
        self,
        *,
        status: Optional[str] = None,
        platform_id: Optional[str] = None,
        account_id: Optional[str] = None,
        content_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[list, int]:
        """查询发布任务（按传入条件过滤 + 分页），返回 (items, total)。"""
        from app.models.content import PublishTask

        db = self.db
        if db is None:
            raise ValueError("缺少数据库会话")

        q = db.query(PublishTask)
        if status:
            q = q.filter(PublishTask.status == status)
        if platform_id:
            q = q.filter(PublishTask.platform_id == str(platform_id))
        if account_id:
            q = q.filter(PublishTask.account_id == str(account_id))
        if content_id:
            # R7：同一 content_id 可能是 master / generated / content_asset → 三个落点都认。
            # 同域 uuid 比较，直接交给 TypeDecorator 归一（禁止 cast，原因同 resolve_publish_credential）。
            q = q.filter(
                (PublishTask.content_master_id == str(content_id))
                | (PublishTask.content_id == str(content_id))
                | (PublishTask.content_asset_id == str(content_id))
            )

        total = q.count()
        page = max(int(page or 1), 1)
        page_size = max(int(page_size or 20), 1)
        items = (
            q.order_by(PublishTask.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return [self._serialize_publish_task(t) for t in items], total

    def _execute_publish_tasks(self, task_ids: list) -> None:
        """触发真实执行机（契约 §3.5）：仅"触发"，**禁止新造执行器**。

        端点已在调用前置 task.status='pending'、retry_count+=1 并 commit；
        此处委托既有同步入口 run_process_pending_tasks（ops_jobs.py:70 同一用法）。
        """
        db = self.db
        if db is None:
            raise ValueError("缺少数据库会话")
        try:
            from app.workers.publish_worker import run_process_pending_tasks

            run_process_pending_tasks(db, limit=max(len(task_ids or []), 1))
        except Exception:  # noqa: BLE001 —— 执行机内部已自行记账失败态；此处不阻断端点返回
            logger.exception("发布执行机触发失败（不阻断） task_ids=%s", task_ids)

    # ── 模块5 · M6 凭据面（docs/模块5-凭据面收口契约-2026-09-28.md）──────────
    # 红线：明文只在 vault（AAD 四元绑定）；platform_accounts.cookie_data/token_data
    # 恒 NULL；「凭据已存 ≠ 会话已验证」（login_status 恒 logged_out，无平台侧探测）。

    _CREDENTIAL_ARTIFACT_TYPE = "api_token"  # vault 词表合法值；真实种类由信封 kind 诚实标注

    def connect_platform(
        self,
        *,
        tenant_id: str,
        platform_id: str,
        account_name: str,
        username: Optional[str] = None,
        email: Optional[str] = None,
        cookie_data: Optional[str] = None,
        token_data: Optional[dict] = None,
        token_expire_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        db = self.db
        if db is None:
            raise ValueError("缺少数据库会话")
        from app.models.content import Platform, PlatformAccount
        from app.services.vault.credential_service import (
            CredentialVaultService,
            make_vault_ref,
        )

        platform = (
            db.query(Platform)
            .filter(Platform.id == str(platform_id), Platform.is_active.is_(True))
            .first()
        )
        if platform is None:
            raise LookupError("platform_not_found")
        if not cookie_data and not token_data:
            raise ValueError("credential_payload_required")

        kind = "cookie" if cookie_data else "token"
        envelope = json.dumps(
            {"kind": kind, "payload": cookie_data if cookie_data else token_data},
            ensure_ascii=False,
        )
        expires_at = None
        if token_expire_at:
            try:
                expires_at = datetime.fromisoformat(str(token_expire_at).replace("Z", "+00:00"))
            except (ValueError, TypeError):
                expires_at = None

        vault = CredentialVaultService(db)
        cred = vault.store_credential(
            secret=envelope,
            tenant_id=str(tenant_id),
            owner_type="tenant",
            owner_id=str(tenant_id),
            connection_type="platform",
            connection_id=str(platform_id),
            artifact_type=self._CREDENTIAL_ARTIFACT_TYPE,
            name=(account_name or f"platform-{platform_id}")[:100],
            expires_at=expires_at,
        )

        tid = str(tenant_id)
        acct = (
            db.query(PlatformAccount)
            .filter(
                PlatformAccount.tenant_id == tid,
                PlatformAccount.platform_id == str(platform_id),
                PlatformAccount.account_name == (account_name or "")[:100],
            )
            .first()
        )
        if acct is None:
            acct = PlatformAccount(
                tenant_id=tid,
                platform_id=str(platform_id),
                account_name=(account_name or "")[:100],
            )
        acct.username = username
        acct.email = email
        # 明文不落库：信封只进 vault；cookie_data/token_data 保持 NULL
        acct.cookie_data = None
        acct.token_data = None
        acct.token_expire_at = expires_at
        acct.credential_ref = make_vault_ref(str(cred.id))
        acct.login_status = "logged_out"  # 凭据已存 ≠ 会话已验证
        acct.is_active = True
        db.add(acct)
        db.commit()
        db.refresh(acct)
        return {
            "account_id": str(acct.id),
            "platform_id": str(platform_id),
            "account_name": acct.account_name,
            "credential_ref": acct.credential_ref,
            "login_status": acct.login_status,
            "session_verified": False,
            "credential_kind": kind,
        }

    def disconnect_platform(self, *, tenant_id: str, account_id: str) -> Dict[str, Any]:
        db = self.db
        if db is None:
            raise ValueError("缺少数据库会话")
        from app.models.content import PlatformAccount

        acct = (
            db.query(PlatformAccount)
            .filter(
                PlatformAccount.id == str(account_id),
                PlatformAccount.tenant_id == str(tenant_id),
            )
            .first()
        )
        if acct is None:
            raise LookupError("account_not_found")
        if acct.credential_ref:
            try:
                from app.services.vault.credential_service import CredentialVaultService

                CredentialVaultService(db).revoke_credential(str(acct.credential_ref))
            except Exception:  # noqa: BLE001 —— 吊销失败不阻断断开（ref 会被清除）
                logger.warning(
                    "vault revoke failed on disconnect ref=%s", acct.credential_ref
                )
        acct.credential_ref = None
        acct.login_status = "logged_out"
        db.add(acct)
        db.commit()
        return {"account_id": str(acct.id), "login_status": acct.login_status,
                "credential_ref": None}

    def list_accounts(
        self, *, tenant_ids: list, platform_id: Optional[str] = None
    ) -> list:
        """租户内账号列表（零明文：has_credential 布尔，不出 ref/cookie/token）。"""
        db = self.db
        if db is None or not tenant_ids:
            return []
        from app.models.content import PlatformAccount

        q = db.query(PlatformAccount).filter(
            PlatformAccount.tenant_id.in_([str(t) for t in tenant_ids])
        )
        if platform_id:
            q = q.filter(PlatformAccount.platform_id == str(platform_id))
        rows = q.order_by(PlatformAccount.created_at.desc()).limit(200).all()
        return [
            {
                "id": str(r.id),
                "platform_id": str(r.platform_id),
                "account_name": r.account_name,
                "username": r.username,
                "email": r.email,
                "login_status": r.login_status,
                "is_active": bool(r.is_active),
                "has_credential": bool(r.credential_ref),
                "token_expire_at": r.token_expire_at.isoformat() if r.token_expire_at else None,
            }
            for r in rows
        ]

    def check_session(self, *, tenant_id: str, account_id: str) -> Dict[str, Any]:
        """凭据可解密性探测（诚实语义：不是平台侧会话验证）。"""
        db = self.db
        if db is None:
            raise ValueError("缺少数据库会话")
        from app.models.content import PlatformAccount

        acct = (
            db.query(PlatformAccount)
            .filter(
                PlatformAccount.id == str(account_id),
                PlatformAccount.tenant_id == str(tenant_id),
            )
            .first()
        )
        if acct is None:
            raise LookupError("account_not_found")
        if not acct.credential_ref:
            return {"account_id": str(acct.id), "credential_resolvable": False,
                    "reason": "no_credential", "session_verified": False}
        try:
            from app.services.vault.credential_service import CredentialVaultService

            CredentialVaultService(db).resolve_credential(
                str(acct.credential_ref),
                tenant_id=str(tenant_id),
                owner_type="tenant",
                owner_id=str(tenant_id),
                connection_type="platform",
                connection_id=str(acct.platform_id),
                artifact_type=self._CREDENTIAL_ARTIFACT_TYPE,
            )
            return {"account_id": str(acct.id), "credential_resolvable": True,
                    "reason": None, "session_verified": False}
        except Exception as exc:  # noqa: BLE001 —— 探测失败给 reason，不泄漏明文
            return {"account_id": str(acct.id), "credential_resolvable": False,
                    "reason": type(exc).__name__, "session_verified": False}

    def get_publish_logs(
        self,
        *,
        tenant_ids: list,
        task_id: Optional[str] = None,
        level: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        db = self.db
        if db is None:
            raise ValueError("缺少数据库会话")
        from app.models.content import PublishLog, PublishTask

        q = (
            db.query(PublishLog)
            .join(PublishTask, PublishLog.task_id == PublishTask.id)
            .filter(PublishTask.tenant_id.in_([str(t) for t in tenant_ids or []]))
        )
        if task_id:
            q = q.filter(PublishLog.task_id == str(task_id))
        if level:
            q = q.filter(PublishLog.level == str(level))
        total = q.count()
        rows = (
            q.order_by(PublishLog.created_at.desc())
            .offset((max(1, page) - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {
            "total": total,
            "items": [
                {
                    "id": str(r.id),
                    "task_id": str(r.task_id),
                    "level": r.level,
                    "message": r.message,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ],
        }

    def get_publish_stats(self, *, tenant_ids: list) -> Dict[str, Any]:
        db = self.db
        if db is None:
            raise ValueError("缺少数据库会话")
        from app.models.content import PlatformAccount, PublishTask

        tids = [str(t) for t in tenant_ids or []]
        tasks_by_status: Dict[str, int] = {}
        if tids:
            rows = (
                db.query(PublishTask.status, func.count(PublishTask.id))
                .filter(PublishTask.tenant_id.in_(tids))
                .group_by(PublishTask.status)
                .all()
            )
            tasks_by_status = {str(k): int(v) for k, v in rows}
        accounts_total = 0
        accounts_with_credential = 0
        if tids:
            accounts_total = int(
                db.query(func.count(PlatformAccount.id))
                .filter(PlatformAccount.tenant_id.in_(tids))
                .scalar()
                or 0
            )
            accounts_with_credential = int(
                db.query(func.count(PlatformAccount.id))
                .filter(
                    PlatformAccount.tenant_id.in_(tids),
                    PlatformAccount.credential_ref.isnot(None),
                )
                .scalar()
                or 0
            )
        try:
            from app.services.publish_capability_registry import admitted_platform_count

            admitted = int(admitted_platform_count())
        except Exception:  # noqa: BLE001 —— 注册表异常时诚实给 0 并标注
            admitted = 0
        return {
            "tasks_by_status": tasks_by_status,
            "accounts_total": accounts_total,
            "accounts_with_credential": accounts_with_credential,
            "admitted_platform_count": admitted,
        }
