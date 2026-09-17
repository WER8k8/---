# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""百度百家号发布适配器 — 真实对接百家号开放平台 API。

支持:
  - OAuth 2.0 授权流程
  - 图文文章发布
  - 发布状态查询
  - 数据回采（阅读量/评论数/推荐量）
  - API 签名验证
  - 指数退避重试

官方文档: https://baijiahao.baidu.com/
"""

import asyncio
import hashlib
import hmac
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urlencode

import aiohttp

from app.models.content import GeneratedContent, Platform, PlatformAccount

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
BJH_API_BASE = "https://baijiahao.baidu.com/builderinner/api"
BJH_OPEN_BASE = "https://open.baidu.com/oauth/2.0"

MAX_RETRIES = 3
RETRY_BASE_DELAY = 2


async def _retry_request(
    method: str,
    url: str,
    session: aiohttp.ClientSession,
    max_retries: int = MAX_RETRIES,
    **kwargs: Any,
) -> aiohttp.ClientResponse:
    """带指数退避重试的 HTTP 请求。"""
    last_exc: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            resp = await session.request(method, url, **kwargs)
            if resp.status < 500:
                return resp
            logger.warning(
                "百家号服务端错误 %d, 重试 %d/%d: %s",
                resp.status, attempt + 1, max_retries, url,
            )
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            last_exc = exc
            logger.warning(
                "百家号请求异常, 重试 %d/%d: %s", attempt + 1, max_retries, exc,
            )
        delay = RETRY_BASE_DELAY * (2 ** attempt)
        await asyncio.sleep(delay)
    if last_exc:
        raise last_exc
    raise RuntimeError(f"百家号请求失败 (重试 {max_retries} 次): {url}")


# ============================================================================
# 百家号发布核心类
# ============================================================================


class BaijiahaoPublisher:
    """百度百家号发布核心类 — 封装百家号平台 API 调用。

    支持两种认证模式:
      1. 百度 OAuth 2.0（App Key + App Secret + access_token）
      2. Cookie 模拟（百家号后台 Cookie）
    官方文档: https://baijiahao.baidu.com/
    """
    def __init__(
        self,
        app_id: str = "",
        app_secret: str = "",
        access_token: str = "",
        refresh_token: str = "",
        cookies: str = "",
    ):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param app_id: 参数 app_id
        :param app_secret: 参数 app_secret
        :param access_token: 参数 access_token
        :param refresh_token: 参数 refresh_token
        :param cookies: 参数 cookies
        :return: 返回处理结果。
        """
        self.app_id = app_id or os.getenv("BJH_APP_ID", "")
        self.app_secret = app_secret or os.getenv("BJH_APP_SECRET", "")
        self.access_token = access_token or os.getenv("BJH_ACCESS_TOKEN", "")
        self.refresh_token = refresh_token or os.getenv("BJH_REFRESH_TOKEN", "")
        self.cookies = cookies or os.getenv("BJH_COOKIES", "")

    # ------------------------------------------------------------------
    # OAuth 2.0 授权
    # ------------------------------------------------------------------
    def get_oauth_authorize_url(self, redirect_uri: str, state: str = "") -> str:
        """生成百度 OAuth 2.0 授权链接。

        用户在浏览器中打开完成授权，百度回调 redirect_uri 并携带 code。
        """
        if not self.app_id:
            raise ValueError("百家号 App ID 未配置")
        params = {
            "client_id": self.app_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": "basic,netdisk",
            "state": state or os.urandom(8).hex(),
            "display": "popup",
        }
        return f"{BJH_OPEN_BASE}/authorize?{urlencode(params)}"

    async def exchange_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """用授权码换取 access_token。"""
        async with aiohttp.ClientSession() as session:
            resp = await _retry_request(
                "POST",
                f"{BJH_OPEN_BASE}/token",
                session,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": self.app_id,
                    "client_secret": self.app_secret,
                    "redirect_uri": redirect_uri,
                },
            )
            data = await resp.json()

        if "access_token" not in data:
            raise RuntimeError(f"百家号 token 交换失败: {data}")
        self.access_token = data["access_token"]
        self.refresh_token = data.get("refresh_token", "")
        return data

    async def refresh_access_token(self) -> Dict[str, Any]:
        """使用 refresh_token 刷新 access_token。"""
        if not self.refresh_token:
            raise RuntimeError("百家号 refresh_token 未配置")

        async with aiohttp.ClientSession() as session:
            resp = await _retry_request(
                "POST",
                f"{BJH_OPEN_BASE}/token",
                session,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token,
                    "client_id": self.app_id,
                    "client_secret": self.app_secret,
                },
            )
            data = await resp.json()

        if "access_token" not in data:
            raise RuntimeError(f"百家号 token 刷新失败: {data}")
        self.access_token = data["access_token"]
        return data

    # ------------------------------------------------------------------
    # API 签名
    # ------------------------------------------------------------------
    def _sign_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """对请求参数进行签名。

        百家号 API 签名规则:
          1. 将所有参数按 key 字典序排列
          2. 拼接为 key1=value1&key2=value2 格式
          3. 在末尾追加 app_secret
          4. 计算 MD5 哈希作为 sign 参数
        """
        # 附加 access_token
        signed = dict(params)
        if self.access_token:
            signed["access_token"] = self.access_token

        # 按字典序排列
        sorted_keys = sorted(signed.keys())
        query_string = "&".join(f"{k}={signed[k]}" for k in sorted_keys)
        # 追加 app_secret 并计算 MD5
        sign_str = query_string + self.app_secret
        sign = hashlib.md5(sign_str.encode()).hexdigest()
        signed["sign"] = sign
        return signed

    # ------------------------------------------------------------------
    # 内容发布
    # ------------------------------------------------------------------
    def _build_headers(self) -> Dict[str, str]:
        """构建请求头。"""
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if self.cookies:
            headers["Cookie"] = self.cookies
        return headers

    async def publish_article(
        self,
        title: str,
        content: str,
        cover_images: Optional[List[str]] = None,
        is_original: bool = True,
        category: str = "科技",
        tags: Optional[List[str]] = None,
    ) -> str:
        """发布百家号图文文章。

        参数:
            title        : 文章标题（8-30 字）
            content      : 文章正文（HTML）
            cover_images : 封面图片 URL 列表（支持单图 / 三图）
            is_original  : 是否声明原创
            category     : 文章分类
            tags         : 文章标签
        返回:
            文章发布后的 URL
        """
        if not self.cookies and not self.access_token:
            raise RuntimeError("百家号未配置 Cookie 或 access_token，无法发布文章")

        payload: Dict[str, Any] = {
            "title": title[:30],
            "content": content,
            "is_original": int(is_original),
            "category": category,
        }
        if cover_images:
            payload["cover_images"] = cover_images if len(cover_images) > 1 else cover_images[0]
        if tags:
            payload["tags"] = ",".join(tags) if isinstance(tags, list) else tags

        # 签名参数
        signed_params = self._sign_request({})
        async with aiohttp.ClientSession() as session:
            resp = await _retry_request(
                "POST",
                f"{BJH_API_BASE}/article/publish",
                session,
                params=signed_params,
                headers=self._build_headers(),
                json=payload,
            )
            data = await resp.json()

        errno = data.get("errno", data.get("code", -1))
        if errno != 0:
            error_msg = data.get("errmsg", data.get("message", "unknown"))
            raise RuntimeError(f"百家号文章发布失败: [{errno}] {error_msg}")

        article_id = data.get("data", {}).get("article_id", "")
        if not article_id:
            article_id = data.get("data", {}).get("id", "pending_review")

        logger.info("百家号文章发布成功: article_id=%s, title=%s", article_id, title)
        return f"https://baijiahao.baidu.com/s?id={article_id}"

    # ------------------------------------------------------------------
    # 发布状态查询
    # ------------------------------------------------------------------
    async def get_article_status(self, article_id: str) -> Dict[str, Any]:
        """查询文章发布状态（审核中/已发布/被拒）。"""
        params = self._sign_request({"article_id": article_id})
        async with aiohttp.ClientSession() as session:
            resp = await _retry_request(
                "GET",
                f"{BJH_API_BASE}/article/status",
                session,
                params=params,
                headers=self._build_headers(),
            )
            data = await resp.json()
        return data.get("data", {})

    # ------------------------------------------------------------------
    # 数据回采
    # ------------------------------------------------------------------
    async def get_article_stats(self, article_id: str) -> Dict[str, Any]:
        """获取文章数据（阅读量/评论数/推荐量等）。"""
        params = self._sign_request({"article_id": article_id})
        async with aiohttp.ClientSession() as session:
            resp = await _retry_request(
                "GET",
                f"{BJH_API_BASE}/article/stats",
                session,
                params=params,
                headers=self._build_headers(),
            )
            data = await resp.json()
        return data.get("data", {})

    # ------------------------------------------------------------------
    # OAuth 回调处理
    # ------------------------------------------------------------------
    async def handle_oauth_callback(self, code: str, redirect_uri: str, state: str = "") -> Dict[str, Any]:
        """处理百度 OAuth 2.0 回调。"""
        token_data = await self.exchange_token(code, redirect_uri)
        return {
            "access_token": token_data.get("access_token", ""),
            "expires_in": token_data.get("expires_in", 0),
            "refresh_token": token_data.get("refresh_token", ""),
        }

    # ------------------------------------------------------------------
    # 格式转换
    # ------------------------------------------------------------------
    @staticmethod
    def to_baijiahao_html(content: str) -> str:
        """将原始内容转为百家号兼容 HTML 格式。

        百家号对 HTML 标签有严格要求，不支持 script/style 等标签。
        """
        paragraphs = content.strip().split("\n")
        return "".join(f"<p>{p.strip()}</p>" for p in paragraphs if p.strip())


# ============================================================================
# PublishService Adapter
# ============================================================================


class BaijiahaoPublisherAdapter:
    """PublishService 的百家号适配器，注册到 _PLATFORM_ADAPTERS。"""
    def __init__(self, db=None):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.db = db

    def publish(
        self,
        platform: Platform,
        account: PlatformAccount,
        content: GeneratedContent,
    ) -> str:
        """向百度百家号发布一篇图文文章。"""
        # ---- 1. 读取账号配置 ----
        configs: Dict[str, str] = {}
        if self.db:
            from app.models.content import PlatformConfig
            rows = (
                self.db.query(PlatformConfig)
                .filter(
                    PlatformConfig.platform_id == platform.id,
                    PlatformConfig.account_id == account.id,
                )
                .all()
            )
            configs = {row.config_key: row.config_value for row in rows}

        cookies = account.cookie_data or configs.get("cookies", "")
        app_id = configs.get("app_id", "")
        app_secret = configs.get("app_secret", "")
        access_token = configs.get("access_token", "")
        # ---- 2. 构造发布参数 ----
        title = content.title or "未命名文章"
        raw_content = content.content or ""
        category = configs.get("category", "科技")
        is_original = configs.get("is_original", "true").lower() == "true"
        html_body = BaijiahaoPublisher.to_baijiahao_html(raw_content)
        # ---- 3. 通过 BaijiahaoPublisher 发布 ----
        publisher = BaijiahaoPublisher(
            app_id=app_id,
            app_secret=app_secret,
            access_token=access_token,
            cookies=cookies,
        )
        loop = asyncio.get_event_loop()
        published_url = loop.run_until_complete(
            publisher.publish_article(
                title=title,
                content=html_body,
                is_original=is_original,
                category=category,
            )
        )
        logger.info(
            "百家号发布完成: platform=%s account=%s title=%s url=%s",
            platform.id, account.id, title, published_url,
        )
        return published_url
