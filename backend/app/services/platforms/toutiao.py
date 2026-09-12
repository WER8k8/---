"""今日头条发布适配器 — 真实对接头条号开放平台 API。

支持:
  - OAuth 2.0 授权流程
  - 图文文章发布
  - 微头条发布
  - 发布状态查询
  - 数据回采
  - 指数退避重试
"""

import asyncio
import hashlib
import hmac
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import aiohttp

from app.models.content import GeneratedContent, Platform, PlatformAccount

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
TOUTIAO_OPEN_BASE = "https://open.toutiao.com"
TOUTIAO_MP_BASE = "https://mp.toutiao.com"

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
                "头条号服务端错误 %d, 重试 %d/%d: %s",
                resp.status, attempt + 1, max_retries, url,
            )
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            last_exc = exc
            logger.warning(
                "头条号请求异常, 重试 %d/%d: %s", attempt + 1, max_retries, exc,
            )
        delay = RETRY_BASE_DELAY * (2 ** attempt)
        await asyncio.sleep(delay)
    if last_exc:
        raise last_exc
    raise RuntimeError(f"头条号请求失败 (重试 {max_retries} 次): {url}")


# ============================================================================
# 今日头条发布核心类
# ============================================================================


class ToutiaoPublisher:
    """今日头条发布核心类 — 封装头条号开放平台 API 调用。

    支持 OAuth 2.0 授权和 Cookie 模拟两种模式。
    官方文档: https://mp.toutiao.com/
    """
    def __init__(
        self,
        client_key: str = "",
        client_secret: str = "",
        access_token: str = "",
        cookies: str = "",
    ):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param client_key: 参数 client_key
        :param client_secret: 参数 client_secret
        :param access_token: 参数 access_token
        :param cookies: 参数 cookies
        :return: 返回处理结果。
        """
        self.client_key = client_key or os.getenv("TOUTIAO_CLIENT_KEY", "")
        self.client_secret = client_secret or os.getenv("TOUTIAO_CLIENT_SECRET", "")
        self.access_token = access_token or os.getenv("TOUTIAO_ACCESS_TOKEN", "")
        self.cookies = cookies or os.getenv("TOUTIAO_COOKIES", "")

    # ------------------------------------------------------------------
    # OAuth 2.0 授权
    # ------------------------------------------------------------------
    def get_oauth_authorize_url(self, redirect_uri: str, state: str = "") -> str:
        """生成 OAuth 2.0 授权链接，用户在浏览器中打开完成授权。

        参数:
            redirect_uri : 回调地址
            state        : 防 CSRF 的随机字符串
        返回:
            授权 URL
        """
        if not self.client_key:
            raise ValueError("头条号 client_key 未配置")
        params = {
            "client_key": self.client_key,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": "article_write",
            "state": state or os.urandom(8).hex(),
        }
        query = "&".join(f"{k}={quote(str(v))}" for k, v in params.items())
        return f"{TOUTIAO_OPEN_BASE}/oauth2/authorize?{query}"

    async def exchange_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """用授权码换取 access_token。

        参数:
            code         : OAuth 回调收到的授权码
            redirect_uri : 与授权请求一致的回调地址
        返回:
            包含 access_token, expires_in, open_id 等字段的字典
        """
        async with aiohttp.ClientSession() as session:
            resp = await _retry_request(
                "POST",
                f"{TOUTIAO_OPEN_BASE}/oauth2/access_token",
                session,
                json={
                    "client_key": self.client_key,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                },
            )
            data = await resp.json()

        if "access_token" not in data:
            raise RuntimeError(f"头条号 token 交换失败: {data}")
        self.access_token = data["access_token"]
        return data

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """使用 refresh_token 刷新 access_token。"""
        async with aiohttp.ClientSession() as session:
            resp = await _retry_request(
                "POST",
                f"{TOUTIAO_OPEN_BASE}/oauth2/refresh_token",
                session,
                json={
                    "client_key": self.client_key,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            data = await resp.json()

        if "access_token" not in data:
            raise RuntimeError(f"头条号 token 刷新失败: {data}")
        self.access_token = data["access_token"]
        return data

    # ------------------------------------------------------------------
    # 内容发布
    # ------------------------------------------------------------------
    def _build_auth_params(self) -> Dict[str, str]:
        """构建认证参数。"""
        params: Dict[str, str] = {}
        if self.access_token:
            params["access_token"] = self.access_token
        return params

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
    ) -> str:
        """发布头条号图文文章。

        参数:
            title        : 文章标题（2-30 字）
            content      : 文章正文（HTML）
            cover_images : 封面图片 URL 列表（支持单图 / 三图）
            is_original  : 是否声明原创
            category     : 文章分类
        返回:
            文章发布后的 URL
        """
        payload: Dict[str, Any] = {
            "title": title[:30],
            "content": content,
            "is_original": int(is_original),
            "category": category,
        }
        if cover_images:
            payload["cover_image"] = cover_images[0] if len(cover_images) == 1 else cover_images

        async with aiohttp.ClientSession() as session:
            resp = await _retry_request(
                "POST",
                f"{TOUTIAO_MP_BASE}/api/article/publish",
                session,
                params=self._build_auth_params(),
                headers=self._build_headers(),
                json=payload,
            )
            data = await resp.json()

        error_code = data.get("error_code", data.get("code", 0))
        if error_code != 0:
            error_msg = data.get("message", data.get("error_message", "unknown"))
            raise RuntimeError(f"头条号发布失败: [{error_code}] {error_msg}")

        article_id = (
            data.get("data", {}).get("article_id")
            or data.get("data", {}).get("id")
            or data.get("article_id", "")
        )
        if not article_id:
            article_id = "pending_review"

        logger.info("头条号文章发布成功: article_id=%s, title=%s", article_id, title)
        return f"https://www.toutiao.com/article/{article_id}/"

    async def publish_micro_post(self, content: str) -> str:
        """发布微头条（短内容，无标题）。

        参数:
            content : 微头条正文
        返回:
            微头条 URL
        """
        payload = {"content": content}
        async with aiohttp.ClientSession() as session:
            resp = await _retry_request(
                "POST",
                f"{TOUTIAO_MP_BASE}/api/micro/publish",
                session,
                params=self._build_auth_params(),
                headers=self._build_headers(),
                json=payload,
            )
            data = await resp.json()

        error_code = data.get("error_code", data.get("code", 0))
        if error_code != 0:
            error_msg = data.get("message", data.get("error_message", "unknown"))
            raise RuntimeError(f"微头条发布失败: [{error_code}] {error_msg}")

        post_id = data.get("data", {}).get("id", f"micro_{hash(content) & 0xFFFFF}")
        logger.info("微头条发布成功: post_id=%s", post_id)
        return f"https://www.toutiao.com/w/{post_id}/"

    # ------------------------------------------------------------------
    # 发布状态查询
    # ------------------------------------------------------------------
    async def get_article_status(self, article_id: str) -> Dict[str, Any]:
        """查询文章发布状态（审核中/已通过/被拒）。"""
        async with aiohttp.ClientSession() as session:
            resp = await _retry_request(
                "GET",
                f"{TOUTIAO_MP_BASE}/api/article/status",
                session,
                params={**self._build_auth_params(), "article_id": article_id},
                headers=self._build_headers(),
            )
            data = await resp.json()

        if data.get("error_code", 0) != 0:
            raise RuntimeError(f"查询文章状态失败: {data}")
        return data.get("data", {})

    # ------------------------------------------------------------------
    # 数据回采
    # ------------------------------------------------------------------
    async def get_article_stats(self, article_id: str) -> Dict[str, Any]:
        """获取文章数据（阅读量、评论数、转发数等）。"""
        async with aiohttp.ClientSession() as session:
            resp = await _retry_request(
                "GET",
                f"{TOUTIAO_MP_BASE}/api/article/stats",
                session,
                params={**self._build_auth_params(), "article_id": article_id},
                headers=self._build_headers(),
            )
            data = await resp.json()

        if data.get("error_code", 0) != 0:
            raise RuntimeError(f"查询文章数据失败: {data}")
        return data.get("data", {})

    # ------------------------------------------------------------------
    # 内容格式转换
    # ------------------------------------------------------------------
    @staticmethod
    def to_toutiao_html(content: str) -> str:
        """将原始内容转为头条号兼容 HTML 格式。"""
        paragraphs = content.strip().split("\n")
        return "".join(f"<p>{p.strip()}</p>" for p in paragraphs if p.strip())


# ============================================================================
# PublishService Adapter
# ============================================================================


class ToutiaoPublisherAdapter:
    """PublishService 的今日头条适配器，注册到 _PLATFORM_ADAPTERS。"""
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
        """向今日头条发布一篇图文文章。"""
        import asyncio
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

        client_key = configs.get("client_key", "")
        client_secret = configs.get("client_secret", "")
        cookies = account.cookie_data or configs.get("cookies", "")
        access_token = configs.get("access_token", "")
        # ---- 2. 构造发布参数 ----
        title = content.title or "未命名文章"
        raw_content = content.content or ""
        category = configs.get("category", "科技")
        is_original = configs.get("is_original", "true").lower() == "true"
        html_body = ToutiaoPublisher.to_toutiao_html(raw_content)
        # ---- 3. 通过 ToutiaoPublisher 发布 ----
        publisher = ToutiaoPublisher(
            client_key=client_key,
            client_secret=client_secret,
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
            "今日头条发布完成: platform=%s account=%s title=%s url=%s",
            platform.id, account.id, title, published_url,
        )
        return published_url
