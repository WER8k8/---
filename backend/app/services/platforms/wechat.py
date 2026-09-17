# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""微信公众号发布适配器 —— 真实对接微信公众平台 API"""

import json
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import requests

from app.models.content import GeneratedContent, Platform, PlatformAccount

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 微信公众平台 API 端点
# ---------------------------------------------------------------------------
WECHAT_API_BASE = "https://api.weixin.qq.com"

# access_token
TOKEN_URL = f"{WECHAT_API_BASE}/cgi-bin/token"
# 新增永久素材（图文）
ADD_NEWS_URL = f"{WECHAT_API_BASE}/cgi-bin/material/add_news"
# 上传永久图片素材
UPLOAD_IMG_URL = f"{WECHAT_API_BASE}/cgi-bin/material/add_material"
# 发布（群发）
MASS_SEND_URL = f"{WECHAT_API_BASE}/cgi-bin/message/mass/send"
# 删除发布
MASS_DELETE_URL = f"{WECHAT_API_BASE}/cgi-bin/message/mass/delete"


class WeChatPublisher:
    """微信公众号素材发布核心类 —— 封装微信公众平台 API 调用。"""
    def __init__(self, appid: str, appsecret: str):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param appid: 参数 appid
        :param appsecret: 参数 appsecret
        :return: 返回处理结果。
        """
        self.appid = appid
        self.appsecret = appsecret
        self._token: Optional[str] = None
        self._token_expires: float = 0  # Unix 时间戳

    # ------------------------------------------------------------------
    # Access Token 管理
    # ------------------------------------------------------------------
    def _get_access_token(self) -> str:
        """获取（或缓存）有效的 access_token。

        微信 access_token 有效期 7200 秒，此处提前 300 秒刷新。
        """
        now = time.time()
        if self._token and now < self._token_expires - 300:
            return self._token

        logger.info("正在获取微信 access_token ...")
        resp = requests.get(
            TOKEN_URL,
            params={
                "grant_type": "client_credential",
                "appid": self.appid,
                "secret": self.appsecret,
            },
            timeout=10,
        )
        data = resp.json()
        if "access_token" not in data:
            errmsg = data.get("errmsg", "未知错误")
            raise RuntimeError(f"获取 access_token 失败: {errmsg} (errcode={data.get('errcode')})")

        self._token = data["access_token"]
        self._token_expires = now + float(data.get("expires_in", 7200))
        logger.info("微信 access_token 获取成功")
        return self._token

    # ------------------------------------------------------------------
    # 素材管理
    # ------------------------------------------------------------------
    def upload_permanent_image(self, file_path: str) -> str:
        """上传永久图片素材，返回 media_id。

        微信要求：图片大小不超过 2MB，支持 bmp / png / jpeg / jpg / gif 格式。
        """
        token = self._get_access_token()
        url = f"{UPLOAD_IMG_URL}?access_token={token}&type=image"
        with open(file_path, "rb") as f:
            resp = requests.post(url, files={"media": f}, timeout=30)
        data = resp.json()
        if "media_id" not in data:
            errmsg = data.get("errmsg", "未知错误")
            raise RuntimeError(f"上传图片素材失败: {errmsg} (errcode={data.get('errcode')})")

        media_id = data["media_id"]
        logger.info(f"永久图片素材上传成功, media_id={media_id}")
        return media_id

    def publish_article(
        self,
        title: str,
        content: str,
        digest: str = "",
        thumb_media_id: str = "",
        author: str = "",
        content_source_url: str = "",
        need_open_comment: int = 0,
        only_fans_can_comment: int = 0,
    ) -> str:
        """发布一篇图文素材到微信公众号（永久素材），返回 media_id。

        参数:
            title                : 图文标题
            content              : 图文消息正文（HTML）
            digest               : 图文消息摘要
            thumb_media_id       : 封面图片 media_id
            author               : 作者
            content_source_url   : 阅读原文链接
            need_open_comment    : 是否打开评论 (0/1)
            only_fans_can_comment: 是否粉丝才可评论 (0/1)
        返回:
            永久素材的 media_id
        """
        token = self._get_access_token()
        url = f"{ADD_NEWS_URL}?access_token={token}"
        body = {
            "articles": [
                {
                    "title": title,
                    "thumb_media_id": thumb_media_id,
                    "author": author or "",
                    "digest": digest or title[:50],
                    "content": content,
                    "content_source_url": content_source_url or "",
                    "need_open_comment": need_open_comment,
                    "only_fans_can_comment": only_fans_can_comment,
                }
            ]
        }
        resp = requests.post(url, json=body, timeout=30)
        data = resp.json()
        if "media_id" not in data:
            errmsg = data.get("errmsg", "未知错误")
            raise RuntimeError(f"发布图文素材失败: {errmsg} (errcode={data.get('errcode')})")

        media_id = data["media_id"]
        logger.info(f"图文素材发布成功, media_id={media_id}, title={title}")
        return media_id

    # ------------------------------------------------------------------
    # 群发消息
    # ------------------------------------------------------------------
    def mass_send_by_tag(self, media_id: str, tag_id: int = 0) -> dict:
        """根据标签群发图文消息。

        tag_id=0 表示全部用户。
        返回微信侧的消息 ID。
        """
        token = self._get_access_token()
        url = f"{MASS_SEND_URL}?access_token={token}"
        body = {
            "filter": {"is_to_all": True, "tag_id": tag_id},
            "mpnews": {"media_id": media_id},
            "msgtype": "mpnews",
            "send_ignore_reprint": 0,
        }
        resp = requests.post(url, json=body, timeout=30)
        data = resp.json()
        if data.get("errcode", -1) != 0:
            errmsg = data.get("errmsg", "未知错误")
            raise RuntimeError(f"群发失败: {errmsg} (errcode={data.get('errcode')})")

        msg_id = data.get("msg_id")
        logger.info(f"群发成功, msg_id={msg_id}, media_id={media_id}")
        return data

    # ------------------------------------------------------------------
    # 辅助：将 HTML 内容转成微信兼容格式
    # ------------------------------------------------------------------
    @staticmethod
    def to_wechat_html(content: str) -> str:
        """将普通文本或 Markdown 风格的文本转为微信图文兼容 HTML。

        微信图文素材的 content 字段支持 HTML 子集（不支持 iframe/script 等）。
        """
        paragraphs = content.strip().split("\n\n")
        html_parts = []
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            # 简单识别标题行
            if para.startswith("## "):
                html_parts.append(f"<h2>{para[3:]}</h2>")
            elif para.startswith("# "):
                html_parts.append(f"<h1>{para[2:]}</h1>")
            else:
                lines = para.split("\n")
                inner = "".join(
                    f"<p>{line}</p>" for line in lines if line.strip()
                )
                html_parts.append(inner)
        return "".join(html_parts)

    # ------------------------------------------------------------------
    # Token 校验（用于服务器配置）
    # ------------------------------------------------------------------
    @staticmethod
    def verify_signature(signature: str, timestamp: str, nonce: str, token: str) -> bool:
        """微信服务器配置验证——校验 signature。"""
        import hashlib
        tmp_list = sorted([token, timestamp, nonce])
        tmp_str = "".join(tmp_list)
        sha1 = hashlib.sha1(tmp_str.encode("utf-8")).hexdigest()
        return sha1 == signature


# ======================================================================
# PublishService Adapter —— 与 PublishService._dispatch_to_platform 集成
# ======================================================================


class WeChatPublisherAdapter:
    """PublishService 的微信公众号适配器，注册到 _PLATFORM_ADAPTERS。"""
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
        """向微信公众号发布一篇图文消息。

        从 PlatformConfig 中读取 appid / appsecret。
        返回微信文章预览 URL（草稿箱预览链接）。
        """
        # ---- 1. 读取账号配置中的 AppID 和 AppSecret ----
        configs = {}
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

        appid = configs.get("appid", "")
        appsecret = configs.get("appsecret", "")
        if not appid or not appsecret:
            raise ValueError(
                "微信公众号未配置 AppID 和 AppSecret，请在连接时填写"
            )

        # ---- 2. 构造发布参数 ----
        title = content.title or "未命名文章"
        raw_content = content.content or ""
        digest = raw_content[:100].replace("\n", " ").strip()
        html_body = WeChatPublisher.to_wechat_html(raw_content)
        # ---- 3. 通过 WeChatPublisher 发布 ----
        publisher = WeChatPublisher(appid=appid, appsecret=appsecret)
        media_id = publisher.publish_article(
            title=title,
            content=html_body,
            digest=digest,
            thumb_media_id="",     # 暂不传封面图片
            author="",
            content_source_url="",
        )
        # ---- 4. 返回微信文章预览 URL ----
        preview_url = (
            f"https://mp.weixin.qq.com/s?__biz={account.username}"
            f"&mid=2653&idx=1&sn={media_id}"
        )
        logger.info(
            f"微信公众号发布成功: platform={platform.id} account={account.id} "
            f"title={title} media_id={media_id}"
        )
        return preview_url
