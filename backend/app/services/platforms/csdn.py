"""CSDN 发布适配器 — 真实对接 CSDN 博客 API。

支持:
  - Cookie 模拟登录
  - Markdown 文章发布
  - 分类/标签设置
  - 发布状态查询
  - 数据回采（阅读量、评论数）
  - 指数退避重试
"""

import asyncio
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

import aiohttp

from app.models.content import GeneratedContent, Platform, PlatformAccount

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
CSDN_API_BASE = "https://bizapi.csdn.net"
CSDN_BLOG_API = "https://blog.csdn.net"

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
                "CSDN 服务端错误 %d, 重试 %d/%d: %s",
                resp.status, attempt + 1, max_retries, url,
            )
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            last_exc = exc
            logger.warning(
                "CSDN 请求异常, 重试 %d/%d: %s", attempt + 1, max_retries, exc,
            )
        delay = RETRY_BASE_DELAY * (2 ** attempt)
        await asyncio.sleep(delay)
    if last_exc:
        raise last_exc
    raise RuntimeError(f"CSDN 请求失败 (重试 {max_retries} 次): {url}")


# ============================================================================
# CSDN 发布核心类
# ============================================================================


class CSDNPublisher:
    """CSDN 发布核心类 — 封装 CSDN 博客 API 调用。

    使用 Cookie 模拟登录 CSDN，通过 Markdown 编辑器 API 发布文章。
    CSDN API 需要 Cookie 中的 UserName 和 UserToken 进行认证。
    """
    def __init__(self, cookies: str = "", csrf_token: str = ""):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param cookies: 参数 cookies
        :param csrf_token: 参数 csrf_token
        :return: 返回处理结果。
        """
        self.cookies = cookies or os.getenv("CSDN_COOKIES", "")
        self.csrf_token = csrf_token or os.getenv("CSDN_CSRF_TOKEN", "")

    def _build_headers(self) -> Dict[str, str]:
        """构建请求头，含 Cookie 和必要的 CSDN 头信息。"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Origin": "https://mp.csdn.net",
            "Referer": "https://mp.csdn.net/",
            "Accept": "application/json, text/plain, */*",
        }
        if self.cookies:
            headers["Cookie"] = self.cookies
        if self.csrf_token:
            headers["X-CSRFToken"] = self.csrf_token
        return headers

    def _parse_cookies(self) -> Dict[str, str]:
        """从 Cookie 字符串解析为字典。"""
        cookie_dict: Dict[str, str] = {}
        if self.cookies:
            for item in self.cookies.split(";"):
                item = item.strip()
                if "=" in item:
                    k, v = item.split("=", 1)
                    cookie_dict[k.strip()] = v.strip()
        return cookie_dict

    # ------------------------------------------------------------------
    # 内容发布
    # ------------------------------------------------------------------
    async def publish_article(
        self,
        title: str,
        content: str,
        category: str = "",
        tags: Optional[List[str]] = None,
        article_type: str = "original",
        is_publish: bool = True,
    ) -> str:
        """发布 CSDN 博客文章。

        参数:
            title        : 文章标题
            content      : 文章正文（Markdown 格式）
            category     : 文章分类
            tags         : 文章标签列表
            article_type : 文章类型（original=原创, repost=转载, translated=翻译）
            is_publish   : 是否直接发布（False=存草稿箱）
        返回:
            文章发布后的 URL
        """
        if not self.cookies:
            raise RuntimeError("CSDN 未配置 Cookie，无法发布文章")

        # CSDN 文章发布 payload
        payload: Dict[str, Any] = {
            "title": title,
            "markdowncontent": content,
            "content": content,
            "article_type": article_type,
            "status": 0 if is_publish else 2,  # 0=发布, 2=草稿
        }
        if category:
            payload["categories"] = category
        if tags:
            payload["tags"] = ",".join(tags) if isinstance(tags, list) else tags

        async with aiohttp.ClientSession() as session:
            resp = await _retry_request(
                "POST",
                f"{CSDN_API_BASE}/blog-console/v1/article/save",
                session,
                headers=self._build_headers(),
                json=payload,
            )
            data = await resp.json()

        if data.get("code") != 200 and data.get("code") != 0:
            error_msg = data.get("message", "unknown error")
            raise RuntimeError(f"CSDN 文章发布失败: {error_msg}")

        article_id = data.get("data", {}).get("articleId") or data.get("data", {}).get("id", "")
        if not article_id:
            # 尝试从返回的 URL 中提取
            article_url = data.get("data", {}).get("url", "")
            if article_url:
                return article_url
            raise RuntimeError("CSDN 发布成功但未获取到文章 ID")

        logger.info("CSDN 文章发布成功: article_id=%s, title=%s", article_id, title)
        cookie_dict = self._parse_cookies()
        username = cookie_dict.get("UserName", cookie_dict.get("username", ""))
        if username:
            return f"https://blog.csdn.net/{username}/article/details/{article_id}"
        return f"https://blog.csdn.net/article/details/{article_id}"

    # ------------------------------------------------------------------
    # 发布状态查询
    # ------------------------------------------------------------------
    async def get_article_status(self, article_id: str) -> Dict[str, Any]:
        """查询文章发布状态。"""
        async with aiohttp.ClientSession() as session:
            resp = await _retry_request(
                "GET",
                f"{CSDN_API_BASE}/blog-console/v1/article/detail",
                session,
                params={"articleId": article_id},
                headers=self._build_headers(),
            )
            data = await resp.json()
        return data.get("data", {})

    # ------------------------------------------------------------------
    # 数据回采
    # ------------------------------------------------------------------
    async def get_article_stats(self, article_id: str) -> Dict[str, Any]:
        """获取文章数据（阅读量、评论数、点赞数等）。"""
        async with aiohttp.ClientSession() as session:
            resp = await _retry_request(
                "GET",
                f"{CSDN_API_BASE}/blog/phoenix/console/v1/article/stat",
                session,
                params={"articleId": article_id},
                headers=self._build_headers(),
            )
            data = await resp.json()
        return data.get("data", {})

    # ------------------------------------------------------------------
    # OAuth 回调处理
    # ------------------------------------------------------------------
    async def handle_oauth_callback(self, code: str, state: str = "") -> Dict[str, Any]:
        """处理 CSDN OAuth 回调（如使用第三方登录集成）。

        CSDN 主要使用 Cookie 认证，OAuth 回调用于获取登录 Cookie。
        """
        logger.info("CSDN OAuth callback: code=%s, state=%s", code[:8], state)
        return {"status": "success", "message": "CSDN 使用 Cookie 认证模式"}

    # ------------------------------------------------------------------
    # 格式转换
    # ------------------------------------------------------------------
    @staticmethod
    def to_csdn_markdown(content: str) -> str:
        """将原始内容转为 CSDN 兼容 Markdown 格式。"""
        return content.strip()


# ============================================================================
# PublishService Adapter
# ============================================================================


class CSDNPublisherAdapter:
    """PublishService 的 CSDN 适配器，注册到 _PLATFORM_ADAPTERS。"""
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
        """向 CSDN 发布一篇博客文章。"""
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
        csrf_token = configs.get("csrf_token", "")
        # ---- 2. 构造发布参数 ----
        title = content.title or "未命名文章"
        raw_content = content.content or ""
        category = configs.get("category", "")
        tags = configs.get("tags", "").split(",") if configs.get("tags") else None
        md_body = CSDNPublisher.to_csdn_markdown(raw_content)
        # ---- 3. 通过 CSDNPublisher 发布 ----
        publisher = CSDNPublisher(cookies=cookies, csrf_token=csrf_token)
        loop = asyncio.get_event_loop()
        published_url = loop.run_until_complete(
            publisher.publish_article(
                title=title,
                content=md_body,
                category=category,
                tags=tags,
            )
        )
        logger.info(
            "CSDN 发布完成: platform=%s account=%s title=%s url=%s",
            platform.id, account.id, title, published_url,
        )
        return published_url
