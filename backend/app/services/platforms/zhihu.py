"""知乎发布适配器 — 真实对接知乎专栏 API。

支持:
  - Cookie 模拟登录
  - 专栏文章发布（Markdown / HTML）
  - 发布状态查询
  - 数据回采（点赞/评论/收藏）
  - 反爬参数 x-zse 签名
  - 指数退避重试
"""

import asyncio
import hashlib
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
ZHIHU_API_BASE = "https://www.zhihu.com/api/v4"
ZHIHU_ZHUANLAN_API = "https://zhuanlan.zhihu.com/api"

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
                "知乎服务端错误 %d, 重试 %d/%d: %s",
                resp.status, attempt + 1, max_retries, url,
            )
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            last_exc = exc
            logger.warning(
                "知乎请求异常, 重试 %d/%d: %s", attempt + 1, max_retries, exc,
            )
        delay = RETRY_BASE_DELAY * (2 ** attempt)
        await asyncio.sleep(delay)
    if last_exc:
        raise last_exc
    raise RuntimeError(f"知乎请求失败 (重试 {max_retries} 次): {url}")


# ============================================================================
# 知乎发布核心类
# ============================================================================


class ZhihuPublisher:
    """知乎发布核心类 — 封装知乎专栏 API 调用。

    使用 Cookie 模拟登录知乎，通过专栏 API 创建/发布文章。
    需要处理知乎反爬参数（x-zse-93, x-zse-96 等）。
    """
    def __init__(
        self,
        cookies: str = "",
        x_zse_93: str = "",
        x_zse_96: str = "",
        x_zse_99: str = "",
    ):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param cookies: 参数 cookies
        :param x_zse_93: 参数 x_zse_93
        :param x_zse_96: 参数 x_zse_96
        :param x_zse_99: 参数 x_zse_99
        :return: 返回处理结果。
        """
        self.cookies = cookies or os.getenv("ZHIHU_COOKIES", "")
        self.x_zse_93 = x_zse_93 or os.getenv("ZHIHU_X_ZSE_93", "101_3_3.0")
        self.x_zse_96 = x_zse_96 or os.getenv("ZHIHU_X_ZSE_96", "")
        self.x_zse_99 = x_zse_99 or os.getenv("ZHIHU_X_ZSE_99", "")

    def _build_headers(self) -> Dict[str, str]:
        """构建请求头，含知乎反爬参数。"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Origin": "https://zhuanlan.zhihu.com",
            "Referer": "https://zhuanlan.zhihu.com/",
            "Accept": "application/json, text/plain, */*",
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

    def _compute_x_zse_96(self, url: str, dc0: str = "") -> str:
        """计算知乎 x-zse-96 签名（简化版）。

        完整签名算法较复杂且知乎经常更新，此处实现基础框架。
        生产环境需根据知乎最新算法调整。
        """
        if self.x_zse_96:
            return self.x_zse_96
        # 基础签名框架：实际需要逆向 x-zse-96 的加密逻辑
        # 此处返回空表示需要外部提供
        return ""

    # ------------------------------------------------------------------
    # 内容发布
    # ------------------------------------------------------------------
    async def publish_article(
        self,
        title: str,
        content: str,
        column_id: str = "",
        tags: Optional[List[str]] = None,
        cover_image_url: str = "",
    ) -> str:
        """发布知乎文章。

        参数:
            title           : 文章标题
            content         : 文章正文（Markdown 或 HTML）
            column_id       : 目标专栏 ID（空字符串表示发布到个人文章）
            tags            : 文章标签列表
            cover_image_url : 封面图片 URL
        返回:
            文章发布后的 URL
        """
        if not self.cookies:
            raise RuntimeError("知乎未配置 Cookie，无法发布文章")

        payload: Dict[str, Any] = {
            "title": title,
            "content": content,
            "comment_permission": "all",
            "can_reward": False,
        }
        if cover_image_url:
            payload["title_image"] = cover_image_url
        if tags:
            payload["topics"] = [{"id": t} if t.isdigit() else {"name": t} for t in tags]

        # 选择发布端点
        if column_id:
            url = f"{ZHIHU_ZHUANLAN_API}/columns/{column_id}/articles"
        else:
            url = f"{ZHIHU_API_BASE}/articles"

        async with aiohttp.ClientSession() as session:
            resp = await _retry_request(
                "POST",
                url,
                session,
                headers=self._build_headers(),
                json=payload,
            )
            data = await resp.json()

        if resp.status not in (200, 201):
            error_msg = data.get("error", {}).get("message", "") or data.get("message", "unknown")
            raise RuntimeError(f"知乎文章发布失败: {error_msg}")

        article_id = data.get("id", "")
        article_url = data.get("url", "")
        if article_url:
            # 知乎返回的 URL 可能不包含域名
            if not article_url.startswith("http"):
                article_url = f"https://zhuanlan.zhihu.com{article_url}"
        elif article_id:
            article_url = f"https://zhuanlan.zhihu.com/p/{article_id}"
        else:
            raise RuntimeError("知乎发布成功但未获取到文章 ID")

        logger.info("知乎文章发布成功: article_id=%s, title=%s", article_id, title)
        return article_url

    # ------------------------------------------------------------------
    # 发布状态查询
    # ------------------------------------------------------------------
    async def get_article_status(self, article_id: str) -> Dict[str, Any]:
        """查询文章状态（审核/已发布）。"""
        async with aiohttp.ClientSession() as session:
            resp = await _retry_request(
                "GET",
                f"{ZHIHU_API_BASE}/articles/{article_id}",
                session,
                headers=self._build_headers(),
            )
            data = await resp.json()
        return data

    # ------------------------------------------------------------------
    # 数据回采
    # ------------------------------------------------------------------
    async def get_article_stats(self, article_id: str) -> Dict[str, Any]:
        """获取文章互动数据（点赞/评论/收藏数）。"""
        async with aiohttp.ClientSession() as session:
            resp = await _retry_request(
                "GET",
                f"{ZHIHU_API_BASE}/articles/{article_id}",
                session,
                headers=self._build_headers(),
            )
            data = await resp.json()

        return {
            "voteup_count": data.get("voteup_count", 0),
            "comment_count": data.get("comment_count", 0),
            "favorited_count": data.get("favorited_count", 0),
            "view_count": data.get("view_count", 0),
        }

    # ------------------------------------------------------------------
    # OAuth 回调处理
    # ------------------------------------------------------------------
    async def handle_oauth_callback(self, code: str, state: str = "") -> Dict[str, Any]:
        """处理知乎 OAuth 回调（如使用第三方登录集成）。

        知乎主要使用 Cookie 认证，OAuth 用于开放平台应用集成。
        """
        logger.info("知乎 OAuth callback: code=%s, state=%s", code[:8], state)
        return {"status": "success", "message": "知乎使用 Cookie 认证模式"}

    # ------------------------------------------------------------------
    # 格式转换
    # ------------------------------------------------------------------
    @staticmethod
    def to_zhihu_markdown(content: str) -> str:
        """将原始内容转为知乎兼容 Markdown 格式。"""
        return content.strip()


# ============================================================================
# PublishService Adapter
# ============================================================================


class ZhihuPublisherAdapter:
    """PublishService 的知乎适配器，注册到 _PLATFORM_ADAPTERS。"""
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
        """向知乎发布一篇文章。"""
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
        x_zse_93 = configs.get("x_zse_93", "")
        x_zse_96 = configs.get("x_zse_96", "")
        x_zse_99 = configs.get("x_zse_99", "")
        # ---- 2. 构造发布参数 ----
        title = content.title or "未命名文章"
        raw_content = content.content or ""
        column_id = configs.get("column_id", "")
        tags = configs.get("tags", "").split(",") if configs.get("tags") else None
        # ---- 3. 通过 ZhihuPublisher 发布 ----
        publisher = ZhihuPublisher(
            cookies=cookies,
            x_zse_93=x_zse_93,
            x_zse_96=x_zse_96,
            x_zse_99=x_zse_99,
        )
        loop = asyncio.get_event_loop()
        published_url = loop.run_until_complete(
            publisher.publish_article(
                title=title,
                content=raw_content,
                column_id=column_id,
                tags=tags,
            )
        )
        logger.info(
            "知乎发布完成: platform=%s account=%s title=%s url=%s",
            platform.id, account.id, title, published_url,
        )
        return published_url
