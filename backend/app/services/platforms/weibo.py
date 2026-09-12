"""微博发布适配器 — 真实对接微博开放平台 API。

支持:
  - OAuth 2.0 授权流程
  - 短微博/长微博（头条文章）发布
  - 图片上传
  - 发布状态查询
  - 数据回采（转发/评论/点赞）
  - 指数退避重试
"""

import asyncio
import base64
import hashlib
import hmac
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
WEIBO_API_BASE = "https://api.weibo.com/2"
WEIBO_OPEN_BASE = "https://open.weibo.com/oauth2"

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
                "微博服务端错误 %d, 重试 %d/%d: %s",
                resp.status, attempt + 1, max_retries, url,
            )
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            last_exc = exc
            logger.warning(
                "微博请求异常, 重试 %d/%d: %s", attempt + 1, max_retries, exc,
            )
        delay = RETRY_BASE_DELAY * (2 ** attempt)
        await asyncio.sleep(delay)
    if last_exc:
        raise last_exc
    raise RuntimeError(f"微博请求失败 (重试 {max_retries} 次): {url}")


# ============================================================================
# 微博发布核心类
# ============================================================================


class WeiboPublisher:
    """微博发布核心类 — 封装新浪微博开放平台 API 调用。

    支持两种认证模式:
      1. OAuth 2.0（App Key + App Secret + access_token）
      2. Cookie 模拟（不推荐，用于快速测试）
    官方文档: https://open.weibo.com/
    """
    def __init__(
        self,
        app_key: str = "",
        app_secret: str = "",
        access_token: str = "",
        redirect_uri: str = "",
        phone: str = "",
        password: str = "",
        cookies: str = "",
    ):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param app_key: 参数 app_key
        :param app_secret: 参数 app_secret
        :param access_token: 参数 access_token
        :param redirect_uri: 参数 redirect_uri
        :param phone: 参数 phone
        :param password: 参数 password
        :param cookies: 参数 cookies
        :return: 返回处理结果。
        """
        self.app_key = app_key or os.getenv("WEIBO_APP_KEY", "")
        self.app_secret = app_secret or os.getenv("WEIBO_APP_SECRET", "")
        self.access_token = access_token or os.getenv("WEIBO_ACCESS_TOKEN", "")
        self.redirect_uri = redirect_uri or os.getenv("WEIBO_REDIRECT_URI", "")
        self.phone = phone
        self.password = password
        self.cookies = cookies or os.getenv("WEIBO_COOKIES", "")

    # ------------------------------------------------------------------
    # OAuth 2.0 授权
    # ------------------------------------------------------------------
    def get_oauth_authorize_url(self, state: str = "") -> str:
        """生成 OAuth 2.0 授权链接。

        用户在浏览器中打开此链接完成授权，微博回调 redirect_uri 并携带 code。
        """
        if not self.app_key:
            raise ValueError("微博 App Key 未配置")
        params = {
            "client_id": self.app_key,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "state": state or os.urandom(8).hex(),
        }
        return f"{WEIBO_OPEN_BASE}/authorize?{urlencode(params)}"

    async def exchange_token(self, code: str) -> Dict[str, Any]:
        """用授权码换取 access_token。

        参数:
            code : OAuth 回调收到的授权码
        返回:
            包含 access_token, expires_in, uid 等字段的字典
        """
        async with aiohttp.ClientSession() as session:
            resp = await _retry_request(
                "POST",
                f"{WEIBO_OPEN_BASE}/access_token",
                session,
                data={
                    "client_id": self.app_key,
                    "client_secret": self.app_secret,
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                },
            )
            data = await resp.json()

        if "access_token" not in data:
            raise RuntimeError(f"微博 token 交换失败: {data}")
        self.access_token = data["access_token"]
        return data

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """刷新 access_token（微博 OAuth 2.0 支持刷新）。"""
        async with aiohttp.ClientSession() as session:
            resp = await _retry_request(
                "POST",
                f"{WEIBO_OPEN_BASE}/access_token",
                session,
                data={
                    "client_id": self.app_key,
                    "client_secret": self.app_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
            )
            data = await resp.json()

        if "access_token" not in data:
            raise RuntimeError(f"微博 token 刷新失败: {data}")
        self.access_token = data["access_token"]
        return data

    # ------------------------------------------------------------------
    # API 签名
    # ------------------------------------------------------------------
    def _sign_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """对请求参数进行签名（微博开放平台签名验证）。

        签名规则: source=app_key, access_token 附加到参数中。
        """
        signed = dict(params)
        if self.app_key:
            signed["source"] = self.app_key
        if self.access_token:
            signed["access_token"] = self.access_token
        return signed

    # ------------------------------------------------------------------
    # 内容发布
    # ------------------------------------------------------------------
    def _build_headers(self) -> Dict[str, str]:
        """构建请求头。"""
        headers: Dict[str, str] = {}
        if self.cookies:
            headers["Cookie"] = self.cookies
        return headers

    async def publish_status(
        self,
        content: str,
        image_urls: Optional[List[str]] = None,
        visible: str = "all",
    ) -> str:
        """发布一条微博。

        参数:
            content    : 微博正文（不超过 140 字为短微博）
            image_urls : 配图 URL 列表（最多 9 张）
            visible    : 可见范围（all=公开, only_fans=粉丝可见, group=好友圈）
        返回:
            微博发布后的 URL
        """
        visible_map = {"all": 0, "only_fans": 1, "group": 2}
        params = self._sign_request({
            "status": content,
            "visible": visible_map.get(visible, 0),
        })
        # 如果有图片，先上传图片获取 pic_id
        if image_urls:
            pic_ids = await self._upload_images(image_urls)
            if pic_ids:
                params["pic_ids"] = ",".join(pic_ids)

        async with aiohttp.ClientSession() as session:
            resp = await _retry_request(
                "POST",
                f"{WEIBO_API_BASE}/statuses/share.json",
                session,
                headers=self._build_headers(),
                data=params,
            )
            data = await resp.json()

        if "id" not in data:
            error = data.get("error", "unknown")
            raise RuntimeError(f"微博发布失败: {error}")

        weibo_id = data["id"]
        uid = data.get("user", {}).get("id", "")
        logger.info("微博发布成功: weibo_id=%s", weibo_id)
        return f"https://weibo.com/{uid}/{weibo_id}"

    async def publish_long_post(
        self,
        title: str,
        content: str,
        is_original: bool = True,
    ) -> str:
        """发布微博头条文章（长文）。

        微博头条文章支持 2000+ 字长文，适合 SEO 内容分发。
        """
        params = self._sign_request({
            "title": title,
            "content": content,
            "is_original": int(is_original),
        })
        async with aiohttp.ClientSession() as session:
            resp = await _retry_request(
                "POST",
                f"{WEIBO_API_BASE}/statuses/longpost.json",
                session,
                headers=self._build_headers(),
                data=params,
            )
            data = await resp.json()

        if "id" not in data:
            error = data.get("error", "unknown")
            raise RuntimeError(f"微博头条文章发布失败: {error}")

        article_id = data.get("article_id", data["id"])
        logger.info("微博头条文章发布成功: article_id=%s", article_id)
        return f"https://weibo.com/ttarticle/p/show?id={article_id}"

    async def _upload_images(self, image_urls: List[str]) -> List[str]:
        """上传图片到微博图床，返回 pic_id 列表。"""
        pic_ids: List[str] = []
        async with aiohttp.ClientSession() as session:
            for url in image_urls[:9]:  # 微博最多 9 张图
                try:
                    # 下载图片
                    img_resp = await _retry_request("GET", url, session)
                    img_bytes = await img_resp.read()
                    # 上传到微博
                    upload_params = self._sign_request({})
                    form = aiohttp.FormData()
                    form.add_field("pic", img_bytes, filename="image.jpg", content_type="image/jpeg")
                    resp = await _retry_request(
                        "POST",
                        f"{WEIBO_API_BASE}/statuses/upload_pic.json",
                        session,
                        headers=self._build_headers(),
                        data=form,
                        params=upload_params,
                    )
                    data = await resp.json()
                    pic_id = data.get("pic_id", "")
                    if pic_id:
                        pic_ids.append(pic_id)
                except Exception as e:
                    logger.warning("微博图片上传失败: %s", e)

        return pic_ids

    # ------------------------------------------------------------------
    # 发布状态查询
    # ------------------------------------------------------------------
    async def get_status(self, weibo_id: str) -> Dict[str, Any]:
        """查询微博发布状态。"""
        params = self._sign_request({"id": weibo_id})
        async with aiohttp.ClientSession() as session:
            resp = await _retry_request(
                "GET",
                f"{WEIBO_API_BASE}/statuses/show.json",
                session,
                params=params,
            )
            data = await resp.json()
        return data

    # ------------------------------------------------------------------
    # 数据回采
    # ------------------------------------------------------------------
    async def get_status_stats(self, weibo_id: str) -> Dict[str, Any]:
        """获取微博互动数据（转发/评论/点赞数）。"""
        params = self._sign_request({"id": weibo_id})
        async with aiohttp.ClientSession() as session:
            resp = await _retry_request(
                "GET",
                f"{WEIBO_API_BASE}/statuses/show.json",
                session,
                params={**params, "trim_user": "1"},
            )
            data = await resp.json()

        return {
            "reposts": data.get("reposts_count", 0),
            "comments": data.get("comments_count", 0),
            "attitudes": data.get("attitudes_count", 0),
        }

    # ------------------------------------------------------------------
    # OAuth 回调处理
    # ------------------------------------------------------------------
    async def handle_oauth_callback(self, code: str, state: str = "") -> Dict[str, Any]:
        """处理微博 OAuth 2.0 回调。"""
        token_data = await self.exchange_token(code)
        return {
            "access_token": token_data.get("access_token", ""),
            "expires_in": token_data.get("expires_in", 0),
            "uid": token_data.get("uid", ""),
        }

    # ------------------------------------------------------------------
    # 格式转换
    # ------------------------------------------------------------------
    @staticmethod
    def truncate_for_weibo(content: str, max_len: int = 140) -> str:
        """截断内容以适配微博字数限制。"""
        if len(content) <= max_len:
            return content
        return content[:max_len - 3] + "..."


# ============================================================================
# PublishService Adapter
# ============================================================================


class WeiboPublisherAdapter:
    """PublishService 的微博适配器，注册到 _PLATFORM_ADAPTERS。"""
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
        """向新浪微博发布内容。

        短内容发普通微博，长内容发头条文章。
        """
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
        phone = configs.get("phone", account.username or "")
        password = configs.get("password", "")
        app_key = configs.get("app_key", "")
        app_secret = configs.get("app_secret", "")
        access_token = configs.get("access_token", "")
        # ---- 2. 构造发布参数 ----
        title = content.title or "未命名文章"
        raw_content = content.content or ""
        # ---- 3. 通过 WeiboPublisher 发布 ----
        publisher = WeiboPublisher(
            app_key=app_key,
            app_secret=app_secret,
            access_token=access_token,
            phone=phone,
            password=password,
            cookies=cookies,
        )
        loop = asyncio.get_event_loop()
        # 长内容发头条文章，短内容发微博
        if len(raw_content) > 140:
            published_url = loop.run_until_complete(
                publisher.publish_long_post(
                    title=title,
                    content=raw_content,
                )
            )
        else:
            published_url = loop.run_until_complete(
                publisher.publish_status(content=raw_content)
            )

        logger.info(
            "微博发布完成: platform=%s account=%s title=%s url=%s",
            platform.id, account.id, title, published_url,
        )
        return published_url
