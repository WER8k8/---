# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""小红书发布适配器 — 真实对接小红书创作者平台 API。

支持:
  - Cookie 模拟登录
  - 图文/视频笔记发布
  - 图片上传
  - 话题标签
  - 数据回采（点赞/收藏/评论）
  - 反爬参数（X-s, X-t 签名）
  - 指数退避重试

注意: 小红书 API 反爬机制较严格，需要配置有效的 Cookie 和签名参数。
官方创作者平台: https://creator.xiaohongshu.com/
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
XHS_CREATOR_BASE = "https://creator.xiaohongshu.com"
XHS_API_BASE = "https://edith.xiaohongshu.com"

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
                "小红书服务端错误 %d, 重试 %d/%d: %s",
                resp.status, attempt + 1, max_retries, url,
            )
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            last_exc = exc
            logger.warning(
                "小红书请求异常, 重试 %d/%d: %s", attempt + 1, max_retries, exc,
            )
        delay = RETRY_BASE_DELAY * (2 ** attempt)
        await asyncio.sleep(delay)
    if last_exc:
        raise last_exc
    raise RuntimeError(f"小红书请求失败 (重试 {max_retries} 次): {url}")


# ============================================================================
# 小红书发布核心类
# ============================================================================


class XiaohongshuPublisher:
    """小红书发布核心类 — 封装小红书创作者平台 API 调用。

    使用 Cookie 模拟登录，通过创作者平台 API 发布笔记。
    需要配置小红书的反爬签名参数（X-s, X-t）。
    """
    def __init__(
        self,
        cookies: str = "",
        x_s: str = "",
        x_t: str = "",
        phone: str = "",
        password: str = "",
    ):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param cookies: 参数 cookies
        :param x_s: 参数 x_s
        :param x_t: 参数 x_t
        :param phone: 参数 phone
        :param password: 参数 password
        :return: 返回处理结果。
        """
        self.cookies = cookies or os.getenv("XHS_COOKIES", "")
        self.x_s = x_s or os.getenv("XHS_X_S", "")
        self.x_t = x_t or os.getenv("XHS_X_T", "")
        self.phone = phone or os.getenv("XHS_PHONE", "")
        self.password = password or os.getenv("XHS_PASSWORD", "")

    def _build_headers(self) -> Dict[str, str]:
        """构建请求头，含小红书反爬参数。"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Origin": "https://creator.xiaohongshu.com",
            "Referer": "https://creator.xiaohongshu.com/publish/publish",
            "Accept": "application/json, text/plain, */*",
        }
        if self.cookies:
            headers["Cookie"] = self.cookies
        if self.x_s:
            headers["X-s"] = self.x_s
        if self.x_t:
            headers["X-t"] = self.x_t
        return headers

    # ------------------------------------------------------------------
    # 图片上传
    # ------------------------------------------------------------------
    async def _upload_image(self, image_url: str, session: aiohttp.ClientSession) -> str:
        """上传图片到小红书图床，返回图片 ID。"""
        # 下载图片
        img_resp = await _retry_request("GET", image_url, session)
        img_bytes = await img_resp.read()
        # 上传到小红书
        upload_headers = dict(self._build_headers())
        upload_headers["Content-Type"] = "multipart/form-data"
        form = aiohttp.FormData()
        form.add_field("file", img_bytes, filename="image.jpg", content_type="image/jpeg")
        resp = await _retry_request(
            "POST",
            f"{XHS_CREATOR_BASE}/api/media/v1/upload/webimg",
            session,
            headers={"Cookie": self.cookies} if self.cookies else {},
            data=form,
        )
        data = await resp.json()
        if data.get("code") != 0:
            raise RuntimeError(f"小红书图片上传失败: {data.get('msg', 'unknown')}")

        image_id = data.get("data", {}).get("image_id", "")
        if not image_id:
            # 尝试其他字段
            image_id = data.get("data", {}).get("id", "")
        return image_id

    # ------------------------------------------------------------------
    # 内容发布
    # ------------------------------------------------------------------
    async def publish_note(
        self,
        title: str,
        content: str,
        image_urls: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        topic: str = "",
        location: str = "",
        note_type: str = "normal",
    ) -> str:
        """发布小红书笔记。

        参数:
            title      : 笔记标题（最多 20 字）
            content    : 笔记正文
            image_urls : 配图 URL 列表（最多 18 张）
            tags       : 话题标签列表
            topic      : 关联话题
            location   : 发布地点
            note_type  : 笔记类型（normal=图文, video=视频）
        返回:
            笔记发布后的 URL
        """
        if not self.cookies:
            raise RuntimeError("小红书未配置 Cookie，无法发布笔记")

        # 上传图片
        image_ids: List[str] = []
        if image_urls:
            async with aiohttp.ClientSession() as session:
                for url in image_urls[:18]:
                    try:
                        img_id = await self._upload_image(url, session)
                        if img_id:
                            image_ids.append(img_id)
                    except Exception as e:
                        logger.warning("小红书图片上传失败: %s", e)

        # 构造发布 payload
        payload: Dict[str, Any] = {
            "title": title[:20],
            "desc": content,
            "type": note_type,
            "post_loc": {},
        }
        if image_ids:
            payload["image_info"] = {"image_ids": image_ids}
        if tags:
            payload["tag_ids"] = tags
        if topic:
            payload["topic_id"] = topic
        if location:
            payload["post_loc"] = {"name": location}

        async with aiohttp.ClientSession() as session:
            resp = await _retry_request(
                "POST",
                f"{XHS_CREATOR_BASE}/api/publish/v1/note",
                session,
                headers=self._build_headers(),
                json=payload,
            )
            data = await resp.json()

        if data.get("code") != 0:
            error_msg = data.get("msg", data.get("message", "unknown"))
            raise RuntimeError(f"小红书笔记发布失败: {error_msg}")

        note_id = (data.get("data", {}) or {}).get("note_id") or (data.get("data", {}) or {}).get("id") or ""
        note_id = str(note_id).strip()
        if not note_id or note_id.lower() in ("pending_review", "pending", "unknown"):
            raise RuntimeError("小红书发布未返回 note_id，禁止假成功")

        logger.info("小红书笔记发布成功: note_id=%s, title=%s", note_id, title)
        return f"https://www.xiaohongshu.com/explore/{note_id}"

    # ------------------------------------------------------------------
    # 发布状态查询
    # ------------------------------------------------------------------
    async def get_note_status(self, note_id: str) -> Dict[str, Any]:
        """查询笔记发布状态（审核中/已发布/被拒）。"""
        async with aiohttp.ClientSession() as session:
            resp = await _retry_request(
                "GET",
                f"{XHS_CREATOR_BASE}/api/publish/v1/note/status",
                session,
                params={"note_id": note_id},
                headers=self._build_headers(),
            )
            data = await resp.json()
        return data.get("data", {})

    # ------------------------------------------------------------------
    # 数据回采
    # ------------------------------------------------------------------
    async def get_note_stats(self, note_id: str) -> Dict[str, Any]:
        """获取笔记互动数据（点赞/收藏/评论数）。"""
        async with aiohttp.ClientSession() as session:
            resp = await _retry_request(
                "GET",
                f"{XHS_API_BASE}/api/sns/web/v1/note/{note_id}",
                session,
                headers=self._build_headers(),
            )
            data = await resp.json()

        interact_info = data.get("data", {}).get("interactInfo", {})
        return {
            "liked_count": interact_info.get("likedCount", 0),
            "collected_count": interact_info.get("collectedCount", 0),
            "comment_count": interact_info.get("commentCount", 0),
            "share_count": interact_info.get("shareCount", 0),
        }

    # ------------------------------------------------------------------
    # OAuth 回调处理
    # ------------------------------------------------------------------
    async def handle_oauth_callback(self, code: str, state: str = "") -> Dict[str, Any]:
        """处理小红书 OAuth 回调。

        小红书使用 Cookie 认证模式，此方法用于统一接口兼容。
        """
        logger.info("小红书 OAuth callback: code=%s, state=%s", code[:8], state)
        return {"status": "success", "message": "小红书使用 Cookie 认证模式"}

    # ------------------------------------------------------------------
    # 格式转换
    # ------------------------------------------------------------------
    @staticmethod
    def format_content_with_tags(content: str, tags: Optional[List[str]] = None) -> str:
        """在小红书正文末尾追加话题标签。"""
        formatted = content.strip()
        if tags:
            formatted += "\n\n" + " ".join(f"#{tag.replace(' ', '')}" for tag in tags)
        return formatted

    @staticmethod
    def truncate_title(title: str, max_len: int = 20) -> str:
        """截断标题以适配小红书 20 字限制。"""
        if len(title) <= max_len:
            return title
        return title[:max_len - 1] + "…"


# ============================================================================
# PublishService Adapter
# ============================================================================


class XiaohongshuPublisherAdapter:
    """PublishService 的小红书适配器，注册到 _PLATFORM_ADAPTERS。"""
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
        """向小红书发布一篇笔记。"""
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
        x_s = configs.get("x_s", "")
        x_t = configs.get("x_t", "")
        phone = configs.get("phone", account.username or "")
        password = configs.get("password", "")
        # ---- 2. 构造发布参数 ----
        raw_title = content.title or "未命名笔记"
        title = XiaohongshuPublisher.truncate_title(raw_title)
        raw_content = content.content or ""
        tags = configs.get("tags", "").split(",") if configs.get("tags") else None
        formatted_content = XiaohongshuPublisher.format_content_with_tags(
            raw_content, tags
        )
        # ---- 3. 通过 XiaohongshuPublisher 发布 ----
        publisher = XiaohongshuPublisher(
            cookies=cookies,
            x_s=x_s,
            x_t=x_t,
            phone=phone,
            password=password,
        )
        loop = asyncio.get_event_loop()
        published_url = loop.run_until_complete(
            publisher.publish_note(
                title=title,
                content=formatted_content,
                tags=tags,
            )
        )
        logger.info(
            "小红书发布完成: platform=%s account=%s title=%s url=%s",
            platform.id, account.id, title, published_url,
        )
        return published_url
