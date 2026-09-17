# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""WhatsApp Business Cloud API 正式接入 — FIX-54

Meta WhatsApp Cloud API v17.0+ 集成：
1. 发送文本消息（模板/自由格式）
2. 发送媒体消息（图片/文档/视频/音频）
3. 模板管理（创建/查询/删除）
4. Webhook 事件处理（消息接收、状态回调）
5. 会话管理（24h 客服窗口 + 模板消息）
6. 速率限制 + 重试

API 文档: https://developers.facebook.com/docs/whatsapp/cloud-api

环境变量:
  WHATSAPP_PHONE_NUMBER_ID — WhatsApp 商业账号电话号码 ID
  WHATSAPP_ACCESS_TOKEN — 系统用户访问令牌（永久令牌）
  WHATSAPP_BUSINESS_ACCOUNT_ID — 商业账号 ID
  WHATSAPP_VERIFY_TOKEN — Webhook 验证令牌
  WHATSAPP_API_VERSION — API 版本（默认 v17.0）
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


# ── 枚举 ──────────────────────────────────────────────────

class WhatsAppMessageType(str, Enum):
    """WhatsApp 消息类型"""
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"
    STICKER = "sticker"
    LOCATION = "location"
    CONTACTS = "contacts"
    INTERACTIVE = "interactive"
    TEMPLATE = "template"
    REACTION = "reaction"


class WhatsAppMessageStatus(str, Enum):
    """WhatsApp 消息状态（Webhook 回调）"""
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    DELETED = "deleted"


class WhatsAppTemplateCategory(str, Enum):
    """模板类别"""
    MARKETING = "MARKETING"
    UTILITY = "UTILITY"
    AUTHENTICATION = "AUTHENTICATION"


class WhatsAppTemplateStatus(str, Enum):
    """模板审核状态"""
    APPROVED = "APPROVED"
    PENDING = "PENDING"
    REJECTED = "REJECTED"
    PAUSED = "PAUSED"
    DISABLED = "DISABLED"


class WhatsAppLanguage(str, Enum):
    """WhatsApp 支持的语言"""
    EN = "en"
    EN_US = "en_US"
    ZH_CN = "zh_CN"
    ZH_HK = "zh_HK"
    AR = "ar"
    PT_BR = "pt_BR"
    ES = "es"
    ES_AR = "es_AR"
    ES_ES = "es_ES"
    ES_MX = "es_MX"
    FR = "fr"
    DE = "de"
    IT = "it"
    JA = "ja"
    KO = "ko"
    RU = "ru"
    HI = "hi"
    ID = "id"
    TR = "tr"
    NL = "nl"
    TH = "th"
    VI = "vi"


# ── 数据模型 ──────────────────────────────────────────────

@dataclass
class WhatsAppTemplate:
    """WhatsApp 消息模板"""
    name: str
    language: WhatsAppLanguage = WhatsAppLanguage.EN
    category: WhatsAppTemplateCategory = WhatsAppTemplateCategory.UTILITY
    status: WhatsAppTemplateStatus = WhatsAppTemplateStatus.PENDING
    id: str = ""
    components: list[dict] = field(default_factory=list)
    rejected_reason: str = ""
    def to_dict(self) -> dict:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "id": self.id,
            "name": self.name,
            "language": self.language.value,
            "category": self.category.value,
            "status": self.status.value,
            "components": self.components,
            "rejected_reason": self.rejected_reason,
        }


@dataclass
class WhatsAppMessage:
    """WhatsApp 消息记录"""
    wa_id: str = ""                    # 消息 ID
    recipient_phone: str = ""          # 接收者手机号
    message_type: WhatsAppMessageType = WhatsAppMessageType.TEXT
    content: str = ""                  # 文本内容
    media_id: str = ""                 # 媒体 ID
    media_url: str = ""                # 媒体 URL
    status: WhatsAppMessageStatus = WhatsAppMessageStatus.SENT
    template_name: str = ""            # 模板名称
    template_language: str = ""        # 模板语言
    created_at: str = ""
    delivered_at: str = ""
    read_at: str = ""
    error_message: str = ""
    def to_dict(self) -> dict:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "wa_id": self.wa_id,
            "recipient_phone": self.recipient_phone,
            "message_type": self.message_type.value,
            "content": self.content,
            "media_id": self.media_id,
            "status": self.status.value,
            "template_name": self.template_name,
            "created_at": self.created_at,
            "delivered_at": self.delivered_at,
            "read_at": self.read_at,
            "error_message": self.error_message,
        }


@dataclass
class WhatsAppIncomingMessage:
    """WhatsApp 收到的消息"""
    from_phone: str = ""
    from_name: str = ""
    message_type: WhatsAppMessageType = WhatsAppMessageType.TEXT
    text_body: str = ""
    media_id: str = ""
    media_mime_type: str = ""
    timestamp: str = ""
    message_id: str = ""
    def to_dict(self) -> dict:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "from_phone": self.from_phone,
            "from_name": self.from_name,
            "message_type": self.message_type.value,
            "text_body": self.text_body,
            "media_id": self.media_id,
            "timestamp": self.timestamp,
            "message_id": self.message_id,
        }


# ── WhatsApp Cloud API 客户端 ─────────────────────────────

class WhatsAppBusinessClient:
    """WhatsApp Business Cloud API 客户端"""
    BASE_URL = "https://graph.facebook.com"
    def __init__(
        self,
        phone_number_id: str = "",
        access_token: str = "",
        waba_id: str = "",
        api_version: str = "",
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param phone_number_id: 参数 phone_number_id
        :param access_token: 参数 access_token
        :param waba_id: 参数 waba_id
        :param api_version: 参数 api_version
        :param timeout: 参数 timeout
        :param max_retries: 参数 max_retries
        :return: 返回处理结果。
        """
        self._phone_number_id = phone_number_id or os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
        self._access_token = access_token or os.getenv("WHATSAPP_ACCESS_TOKEN", "")
        self._waba_id = waba_id or os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", "")
        self._api_version = api_version or os.getenv("WHATSAPP_API_VERSION", "v17.0")
        self._timeout = timeout
        self._max_retries = max_retries

    @property
    def is_configured(self) -> bool:
        """is_configured。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return bool(self._phone_number_id and self._access_token)

    @property
    def messages_url(self) -> str:
        """messages_url。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return f"{self.BASE_URL}/{self._api_version}/{self._phone_number_id}/messages"

    @property
    def media_url(self) -> str:
        """media_url。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return f"{self.BASE_URL}/{self._api_version}/{self._phone_number_id}/media"

    async def _request(
        self,
        method: str,
        url: str,
        json_data: dict | None = None,
        files: dict | None = None,
    ) -> dict[str, Any]:
        """_request。

        参数说明：
        :param self: 参数 self
        :param method: 参数 method
        :param url: 参数 url
        :param json_data: 参数 json_data
        :param files: 参数 files
        :return: 返回处理结果。
        """
        headers = {
            "Authorization": f"Bearer {self._access_token}",
        }
        if json_data and not files:
            headers["Content-Type"] = "application/json"

        last_error = None
        for attempt in range(self._max_retries):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    if method == "POST":
                        if files:
                            resp = await client.post(url, data=json_data, files=files, headers={"Authorization": headers["Authorization"]})
                        else:
                            resp = await client.post(url, json=json_data, headers=headers)
                    elif method == "GET":
                        resp = await client.get(url, headers=headers)
                    elif method == "DELETE":
                        resp = await client.delete(url, headers=headers)
                    else:
                        raise ValueError(f"Unsupported method: {method}")

                    if resp.status_code == 429:
                        retry_after = int(resp.headers.get("Retry-After", 5))
                        logger.warning("WhatsApp 429: retry after %ds", retry_after)
                        await asyncio.sleep(retry_after)
                        continue

                    if resp.status_code >= 500:
                        await asyncio.sleep(2 ** attempt)
                        continue

                    resp.raise_for_status()
                    return resp.json()

            except httpx.HTTPStatusError as e:
                last_error = e
                error_body = {}
                try:
                    error_body = e.response.json()
                except Exception:
                    pass

                error_info = error_body.get("error", {})
                error_code = error_info.get("code", "unknown")
                error_msg = error_info.get("message", str(e))
                if error_code == 190 or "access token" in error_msg.lower():
                    raise ValueError(f"WhatsApp 令牌无效: {error_msg}") from e
                if error_code == 100 or "phone number" in error_msg.lower():
                    raise ValueError(f"WhatsApp 号码 ID 无效: {error_msg}") from e

                logger.warning("WhatsApp HTTP error [%s]: %s", error_code, error_msg)

            except httpx.TimeoutException:
                last_error = TimeoutError("WhatsApp 请求超时")
                logger.warning("WhatsApp timeout: %s", url)
            except Exception as e:
                last_error = e
                logger.warning("WhatsApp request error: %s", e)

        raise last_error or RuntimeError("WhatsApp 请求失败")

    # ── 消息发送 ──────────────────────────────────────────
    async def send_text(
        self,
        to: str,
        body: str,
        preview_url: bool = True,
    ) -> WhatsAppMessage:
        """发送文本消息。

        Args:
            to: 接收者手机号（国际格式，如 +8613800138000）
            body: 消息正文
            preview_url: 是否预览链接
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "preview_url": preview_url,
                "body": body,
            },
        }
        data = await self._request("POST", self.messages_url, json_data=payload)
        msg = data.get("messages", [{}])[0]
        return WhatsAppMessage(
            wa_id=msg.get("id", ""),
            recipient_phone=to,
            message_type=WhatsAppMessageType.TEXT,
            content=body,
            status=WhatsAppMessageStatus.SENT,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    async def send_template(
        self,
        to: str,
        template_name: str,
        language: WhatsAppLanguage = WhatsAppLanguage.EN,
        components: list[dict] | None = None,
    ) -> WhatsAppMessage:
        """发送模板消息。

        Args:
            to: 接收者手机号
            template_name: 模板名称（需先通过审核）
            language: 模板语言
            components: 模板组件（header/body/button 参数替换）
                示例:
                [{"type": "body", "parameters": [{"type": "text", "text": "张三"}]}]
        """
        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language.value},
            },
        }
        if components:
            payload["template"]["components"] = components

        data = await self._request("POST", self.messages_url, json_data=payload)
        msg = data.get("messages", [{}])[0]
        return WhatsAppMessage(
            wa_id=msg.get("id", ""),
            recipient_phone=to,
            message_type=WhatsAppMessageType.TEMPLATE,
            template_name=template_name,
            template_language=language.value,
            status=WhatsAppMessageStatus.SENT,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    async def send_image(
        self,
        to: str,
        image_url: str = "",
        image_id: str = "",
        caption: str = "",
    ) -> WhatsAppMessage:
        """发送图片消息。

        Args:
            to: 接收者手机号
            image_url: 图片 URL（公开可访问）
            image_id: 已上传的媒体 ID（与 URL 二选一）
            caption: 图片说明
        """
        media: dict[str, str] = {}
        if image_id:
            media["id"] = image_id
        elif image_url:
            media["link"] = image_url
        if caption:
            media["caption"] = caption

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "image",
            "image": media,
        }
        data = await self._request("POST", self.messages_url, json_data=payload)
        msg = data.get("messages", [{}])[0]
        return WhatsAppMessage(
            wa_id=msg.get("id", ""),
            recipient_phone=to,
            message_type=WhatsAppMessageType.IMAGE,
            media_url=image_url,
            media_id=image_id,
            status=WhatsAppMessageStatus.SENT,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    async def send_document(
        self,
        to: str,
        document_url: str = "",
        document_id: str = "",
        filename: str = "",
        caption: str = "",
    ) -> WhatsAppMessage:
        """发送文档消息。

        Args:
            to: 接收者手机号
            document_url: 文档 URL
            document_id: 已上传的媒体 ID
            filename: 文件名
            caption: 说明
        """
        media: dict[str, str] = {}
        if document_id:
            media["id"] = document_id
        elif document_url:
            media["link"] = document_url
        if filename:
            media["filename"] = filename
        if caption:
            media["caption"] = caption

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "document",
            "document": media,
        }
        data = await self._request("POST", self.messages_url, json_data=payload)
        msg = data.get("messages", [{}])[0]
        return WhatsAppMessage(
            wa_id=msg.get("id", ""),
            recipient_phone=to,
            message_type=WhatsAppMessageType.DOCUMENT,
            media_url=document_url,
            media_id=document_id,
            status=WhatsAppMessageStatus.SENT,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    async def send_interactive(
        self,
        to: str,
        body_text: str,
        buttons: list[dict],
        header_text: str = "",
        footer_text: str = "",
        header_type: str = "text",
    ) -> WhatsAppMessage:
        """发送交互式消息（按钮/列表）。

        Args:
            to: 接收者手机号
            body_text: 消息正文
            buttons: 按钮列表
                [{"type": "reply", "reply": {"id": "btn1", "title": "确认"}}]
                或 URL 按钮: [{"type": "url", "url": "https://..."}]
            header_text: 标题
            footer_text: 页脚
            header_type: 标题类型（text/image/video/document）
        """
        interactive: dict[str, Any] = {
            "type": "button",
            "body": {"text": body_text},
            "action": {"buttons": buttons},
        }
        if header_text:
            interactive["header"] = {"type": header_type, "text": header_text}
        if footer_text:
            interactive["footer"] = {"text": footer_text}

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": interactive,
        }
        data = await self._request("POST", self.messages_url, json_data=payload)
        msg = data.get("messages", [{}])[0]
        return WhatsAppMessage(
            wa_id=msg.get("id", ""),
            recipient_phone=to,
            message_type=WhatsAppMessageType.INTERACTIVE,
            content=body_text,
            status=WhatsAppMessageStatus.SENT,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    # ── 模板管理 ──────────────────────────────────────────
    async def create_template(
        self,
        name: str,
        category: WhatsAppTemplateCategory,
        language: WhatsAppLanguage = WhatsAppLanguage.EN,
        components: list[dict] | None = None,
    ) -> WhatsAppTemplate:
        """创建消息模板。

        Args:
            name: 模板名称（小写字母+下划线，如 lead_welcome_1）
            category: 模板类别
            language: 语言
            components: 模板组件
                示例:
                [{"type": "BODY", "text": "你好 {{1}}，欢迎了解我们的产品"},
                 {"type": "HEADER", "format": "TEXT", "text": "欢迎"},
                 {"type": "FOOTER", "text": "回复 STOP 退订"},
                 {"type": "BUTTONS", "buttons": [
                     {"type": "QUICK_REPLY", "text": "了解更多"},
                     {"type": "URL", "text": "查看官网", "url": "https://example.com"}
                 ]}]
        """
        if not components:
            components = [{"type": "BODY", "text": "{{1}}"}]

        url = f"{self.BASE_URL}/{self._api_version}/{self._waba_id}/message_templates"
        payload = {
            "name": name,
            "category": category.value,
            "language": language.value,
            "components": components,
        }
        try:
            data = await self._request("POST", url, json_data=payload)
            tpl = data
            return WhatsAppTemplate(
                id=tpl.get("id", ""),
                name=tpl.get("name", name),
                language=language,
                category=category,
                status=WhatsAppTemplateStatus(tpl.get("status", "PENDING")),
                components=components,
            )
        except Exception as e:
            logger.error("Create WhatsApp template failed: %s", e)
            raise

    async def list_templates(
        self,
        limit: int = 50,
        status: str = "",
        language: str = "",
    ) -> list[WhatsAppTemplate]:
        """查询模板列表。

        Args:
            limit: 每页数量
            status: 筛选状态（APPROVED/PENDING/REJECTED）
            language: 筛选语言
        """
        url = f"{self.BASE_URL}/{self._api_version}/{self._waba_id}/message_templates"
        params = {"limit": min(limit, 100)}
        if status:
            params["status"] = status
        if language:
            params["language"] = language

        # GET with query params
        headers = {"Authorization": f"Bearer {self._access_token}"}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        templates = []
        for t in data.get("data", []):
            templates.append(WhatsAppTemplate(
                id=t.get("id", ""),
                name=t.get("name", ""),
                language=WhatsAppLanguage(t.get("language", "en")),
                category=WhatsAppTemplateCategory(t.get("category", "UTILITY")),
                status=WhatsAppTemplateStatus(t.get("status", "PENDING")),
                components=t.get("components", []),
                rejected_reason=t.get("rejected_reason", ""),
            ))

        return templates

    async def delete_template(self, template_name: str) -> bool:
        """删除模板。

        Args:
            template_name: 模板名称
        """
        # 先查询模板 ID
        templates = await self.list_templates()
        template_id = ""
        for t in templates:
            if t.name == template_name:
                template_id = t.id
                break

        if not template_id:
            raise ValueError(f"模板不存在: {template_name}")

        url = f"{self.BASE_URL}/{self._api_version}/{template_id}"
        headers = {"Authorization": f"Bearer {self._access_token}"}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.delete(url, headers=headers)
            return resp.status_code == 200

    # ── 媒体上传 ──────────────────────────────────────────
    async def upload_media(
        self,
        file_path: str,
        media_type: str = "image/png",
    ) -> str:
        """上传媒体文件，返回媒体 ID。

        Args:
            file_path: 本地文件路径
            media_type: MIME 类型
        """
        url = self.media_url
        headers = {"Authorization": f"Bearer {self._access_token}"}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f, media_type)}
                data = {"messaging_product": "whatsapp"}
                resp = await client.post(url, data=data, files=files, headers=headers)
                resp.raise_for_status()
                result = resp.json()

        return result.get("id", "")

    async def get_media_url(self, media_id: str) -> str:
        """获取媒体下载 URL。

        Args:
            media_id: 媒体 ID
        """
        url = f"{self.BASE_URL}/{self._api_version}/{media_id}"
        headers = {"Authorization": f"Bearer {self._access_token}"}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        return data.get("url", "")

    async def download_media(self, media_id: str, save_path: str) -> str:
        """下载媒体文件到本地。

        Args:
            media_id: 媒体 ID
            save_path: 保存路径
        """
        media_url = await self.get_media_url(media_id)
        if not media_url:
            raise ValueError("无法获取媒体 URL")

        headers = {"Authorization": f"Bearer {self._access_token}"}
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(media_url, headers=headers)
            resp.raise_for_status()
            with open(save_path, "wb") as f:
                f.write(resp.content)

        return save_path

    # ── Webhook 处理 ──────────────────────────────────────
    @staticmethod
    def verify_webhook(
        mode: str,
        token: str,
        challenge: str,
        verify_token: str = "",
    ) -> tuple[bool, str]:
        """验证 Webhook 订阅。

        Args:
            mode: hub.mode（应为 "subscribe"）
            token: hub.verify_token
            challenge: hub.challenge
            verify_token: 本地配置的验证令牌

        Returns:
            (验证通过, challenge 或错误信息)
        """
        config_token = verify_token or os.getenv("WHATSAPP_VERIFY_TOKEN", "")
        if mode == "subscribe" and token == config_token:
            return True, challenge
        return False, ""

    @staticmethod
    def parse_incoming_message(
        payload: dict[str, Any],
        signature: str = "",
        app_secret: str = "",
    ) -> tuple[bool, list[WhatsAppIncomingMessage]]:
        """解析 Webhook 回调中的消息。

        Args:
            payload: Webhook JSON payload
            signature: X-Hub-Signature-256 头
            app_secret: Meta App Secret（用于签名验证）

        Returns:
            (签名验证通过, 消息列表)
        """
        # 签名验证（可选）
        if app_secret and signature:
            body = json.dumps(payload, sort_keys=True)
            expected = "sha256=" + hmac.new(
                app_secret.encode(),
                body.encode(),
                hashlib.sha256,
            ).hexdigest()
            if not hmac.compare_digest(expected, signature):
                return False, []

        messages: list[WhatsAppIncomingMessage] = []
        entries = payload.get("entry", [])
        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                msgs = value.get("messages", [])
                for msg in msgs:
                    msg_type = WhatsAppMessageType(msg.get("type", "text"))
                    incoming = WhatsAppIncomingMessage(
                        from_phone=msg.get("from", ""),
                        from_name=value.get("contacts", [{}])[0].get("profile", {}).get("name", ""),
                        message_type=msg_type,
                        text_body=msg.get("text", {}).get("body", ""),
                        media_id="",
                        media_mime_type="",
                        timestamp=msg.get("timestamp", ""),
                        message_id=msg.get("id", ""),
                    )
                    if msg_type == WhatsAppMessageType.IMAGE:
                        incoming.media_id = msg.get("image", {}).get("id", "")
                        incoming.media_mime_type = msg.get("image", {}).get("mime_type", "")
                    elif msg_type == WhatsAppMessageType.DOCUMENT:
                        incoming.media_id = msg.get("document", {}).get("id", "")
                        incoming.media_mime_type = msg.get("document", {}).get("mime_type", "")
                    elif msg_type == WhatsAppMessageType.AUDIO:
                        incoming.media_id = msg.get("audio", {}).get("id", "")
                        incoming.media_mime_type = msg.get("audio", {}).get("mime_type", "")
                    elif msg_type == WhatsAppMessageType.VIDEO:
                        incoming.media_id = msg.get("video", {}).get("id", "")
                        incoming.media_mime_type = msg.get("video", {}).get("mime_type", "")

                    messages.append(incoming)

        return True, messages

    @staticmethod
    def parse_status_update(payload: dict[str, Any]) -> list[dict[str, Any]]:
        """解析消息状态更新。

        Args:
            payload: Webhook JSON payload

        Returns:
            状态更新列表
        """
        statuses: list[dict[str, Any]] = []
        entries = payload.get("entry", [])
        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                status_list = value.get("statuses", [])
                for s in status_list:
                    statuses.append({
                        "wa_id": s.get("id", ""),
                        "status": s.get("status", ""),
                        "timestamp": s.get("timestamp", ""),
                        "recipient_id": s.get("recipient_id", ""),
                        "errors": s.get("errors", []),
                    })

        return statuses

    # ── 业务账号信息 ──────────────────────────────────────
    async def get_phone_number_info(self) -> dict[str, Any]:
        """获取电话号码信息。"""
        url = f"{self.BASE_URL}/{self._api_version}/{self._phone_number_id}"
        headers = {"Authorization": f"Bearer {self._access_token}"}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        return data

    async def get_business_profile(self) -> dict[str, Any]:
        """获取商业资料。"""
        url = f"{self.BASE_URL}/{self._api_version}/{self._phone_number_id}/whatsapp_business_profile"
        params = {"fields": "about,address,description,email,profile_picture_url,websites,vertical"}
        headers = {"Authorization": f"Bearer {self._access_token}"}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        return data.get("data", [{}])[0]

    async def update_business_profile(
        self,
        about: str = "",
        address: str = "",
        description: str = "",
        email: str = "",
        websites: list[str] | None = None,
        vertical: str = "",
    ) -> bool:
        """更新商业资料。"""
        url = f"{self.BASE_URL}/{self._api_version}/{self._phone_number_id}/whatsapp_business_profile"
        payload: dict[str, Any] = {}
        if about:
            payload["about"] = about
        if address:
            payload["address"] = address
        if description:
            payload["description"] = description
        if email:
            payload["email"] = email
        if websites:
            payload["websites"] = websites
        if vertical:
            payload["vertical"] = vertical

        if not payload:
            return True

        headers = {"Authorization": f"Bearer {self._access_token}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            return resp.status_code == 200


# ── 获客集成：WhatsApp 外联服务 ───────────────────────────

PROSPECT_TEMPLATES: dict[str, dict] = {
    "lead_intro": {
        "name": "lead_intro_1",
        "category": WhatsAppTemplateCategory.MARKETING,
        "components": [
            {"type": "HEADER", "format": "TEXT", "text": "{{1}}"},
            {"type": "BODY", "text": "Hi {{2}}! I'm {{3}} from {{4}}. We help {{5}} companies like yours with {{6}}. Would you be interested in a quick chat?"},
            {"type": "FOOTER", "text": "Reply STOP to opt out"},
            {"type": "BUTTONS", "buttons": [
                {"type": "QUICK_REPLY", "text": "Yes, let's chat"},
                {"type": "QUICK_REPLY", "text": "Not now, thanks"},
            ]},
        ],
    },
    "lead_follow_up": {
        "name": "lead_follow_up_1",
        "category": WhatsAppTemplateCategory.MARKETING,
        "components": [
            {"type": "HEADER", "format": "TEXT", "text": "Following up"},
            {"type": "BODY", "text": "Hi {{1}}! Just wanted to follow up on my previous message about {{2}}. We've helped companies like {{3}} achieve {{4}}. Let me know if you'd like to learn more!"},
            {"type": "BUTTONS", "buttons": [
                {"type": "QUICK_REPLY", "text": "Tell me more"},
                {"type": "QUICK_REPLY", "text": "Not interested"},
            ]},
        ],
    },
    "lead_value_prop": {
        "name": "lead_value_prop_1",
        "category": WhatsAppTemplateCategory.MARKETING,
        "components": [
            {"type": "HEADER", "format": "IMAGE", "example": {"header_handle": ["https://example.com/banner.jpg"]}},
            {"type": "BODY", "text": "Hi {{1}}! Did you know {{2}}% of {{3}} companies are now using {{4}} to {{5}}? Here's a quick case study of how {{6}} achieved {{7}}."},
            {"type": "BUTTONS", "buttons": [
                {"type": "URL", "text": "View Case Study", "url": "{{8}}"},
                {"type": "QUICK_REPLY", "text": "Book a demo"},
            ]},
        ],
    },
}


class WhatsAppOutreachService:
    """WhatsApp 获客外联服务"""
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._client = WhatsAppBusinessClient()

    @property
    def is_configured(self) -> bool:
        """is_configured。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return self._client.is_configured

    async def send_prospect_intro(
        self,
        to_phone: str,
        prospect_name: str,
        sender_name: str,
        company_name: str,
        industry: str,
        value_prop: str,
    ) -> WhatsAppMessage:
        """发送获客开场白。

        Args:
            to_phone: 目标客户手机号
            prospect_name: 客户名
            sender_name: 发送者名
            company_name: 我方公司名
            industry: 行业
            value_prop: 价值主张
        """
        template_name = "lead_intro_1"
        components = [
            {
                "type": "header",
                "parameters": [{"type": "text", "text": f"Hello {prospect_name}"}],
            },
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": prospect_name},
                    {"type": "text", "text": sender_name},
                    {"type": "text", "text": company_name},
                    {"type": "text", "text": industry},
                    {"type": "text", "text": value_prop},
                ],
            },
        ]
        return await self._client.send_template(
            to=to_phone,
            template_name=template_name,
            language=WhatsAppLanguage.EN,
            components=components,
        )

    async def send_prospect_follow_up(
        self,
        to_phone: str,
        prospect_name: str,
        topic: str,
        reference_company: str,
        result: str,
    ) -> WhatsAppMessage:
        """发送跟进消息。

        Args:
            to_phone: 目标客户手机号
            prospect_name: 客户名
            topic: 话题
            reference_company: 参考案例公司
            result: 达成结果
        """
        template_name = "lead_follow_up_1"
        components = [
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": prospect_name},
                    {"type": "text", "text": topic},
                    {"type": "text", "text": reference_company},
                    {"type": "text", "text": result},
                ],
            },
        ]
        return await self._client.send_template(
            to=to_phone,
            template_name=template_name,
            language=WhatsAppLanguage.EN,
            components=components,
        )

    async def send_case_study(
        self,
        to_phone: str,
        prospect_name: str,
        stat_percent: str,
        industry: str,
        solution: str,
        benefit: str,
        case_company: str,
        case_result: str,
        case_url: str,
    ) -> WhatsAppMessage:
        """发送案例研究。

        Args:
            to_phone: 目标客户手机号
            prospect_name: 客户名
            stat_percent: 统计百分比
            industry: 行业
            solution: 解决方案
            benefit: 收益
            case_company: 案例公司
            case_result: 案例结果
            case_url: 案例链接
        """
        template_name = "lead_value_prop_1"
        components = [
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": prospect_name},
                    {"type": "text", "text": stat_percent},
                    {"type": "text", "text": industry},
                    {"type": "text", "text": solution},
                    {"type": "text", "text": benefit},
                    {"type": "text", "text": case_company},
                    {"type": "text", "text": case_result},
                    {"type": "text", "text": case_url},
                ],
            },
        ]
        return await self._client.send_template(
            to=to_phone,
            template_name=template_name,
            language=WhatsAppLanguage.EN,
            components=components,
        )


# 单例
whatsapp_business_client = WhatsAppBusinessClient()
whatsapp_outreach_service = WhatsAppOutreachService()