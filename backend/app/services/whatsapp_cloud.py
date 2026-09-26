"""
WhatsApp Cloud API 服务
替代 Baileys，使用 Meta 官方 API
"""
import os
import httpx
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WhatsAppConfig:
    """WhatsApp Cloud API 配置"""
    access_token: str
    phone_number_id: str
    verify_token: Optional[str] = None
    api_version: str = "v18.0"
    base_url: str = "https://graph.facebook.com"


class WhatsAppCloudAPI:
    """WhatsApp Cloud API 客户端"""

    def __init__(self, config: Optional[WhatsAppConfig] = None):
        if config:
            self.config = config
        else:
            self.config = WhatsAppConfig(
                access_token=os.getenv("WHATSAPP_CLOUD_TOKEN", ""),
                phone_number_id=os.getenv("WHATSAPP_PHONE_NUMBER_ID", ""),
                verify_token=os.getenv("WHATSAPP_VERIFY_TOKEN", ""),
            )
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                headers={
                    "Authorization": f"Bearer {self.config.access_token}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def send_text(self, to: str, text: str) -> Dict[str, Any]:
        """发送文本消息"""
        client = await self._get_client()
        url = f"/{self.config.api_version}/{self.config.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            logger.info(f"WhatsApp text sent to {to}: {result.get('messages', [{}])[0].get('id')}")
            return result
        except httpx.HTTPStatusError as e:
            logger.error(f"WhatsApp API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"WhatsApp send failed: {e}")
            raise

    async def send_template(
        self, to: str, template_name: str, language: str = "en", components: Optional[list] = None
    ) -> Dict[str, Any]:
        """发送模板消息"""
        client = await self._get_client()
        url = f"/{self.config.api_version}/{self.config.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language},
            },
        }
        if components:
            payload["template"]["components"] = components
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            logger.info(f"WhatsApp template sent to {to}: {result.get('messages', [{}])[0].get('id')}")
            return result
        except httpx.HTTPStatusError as e:
            logger.error(f"WhatsApp API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"WhatsApp template send failed: {e}")
            raise

    async def send_image(self, to: str, image_url: str, caption: Optional[str] = None) -> Dict[str, Any]:
        """发送图片消息"""
        client = await self._get_client()
        url = f"/{self.config.api_version}/{self.config.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "image",
            "image": {"link": image_url},
        }
        if caption:
            payload["image"]["caption"] = caption
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"WhatsApp API error: {e.response.status_code} - {e.response.text}")
            raise

    async def send_document(self, to: str, document_url: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """发送文档消息"""
        client = await self._get_client()
        url = f"/{self.config.api_version}/{self.config.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "document",
            "document": {"link": document_url},
        }
        if filename:
            payload["document"]["filename"] = filename
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"WhatsApp API error: {e.response.status_code} - {e.response.text}")
            raise

    async def mark_as_read(self, message_id: str) -> Dict[str, Any]:
        """标记消息已读"""
        client = await self._get_client()
        url = f"/{self.config.api_version}/{self.config.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"WhatsApp mark read error: {e.response.status_code} - {e.response.text}")
            raise

    async def send_action(self, to: str, action: str = "typing_on") -> Dict[str, Any]:
        """发送状态动作（typing_on / mark_seen）"""
        client = await self._get_client()
        url = f"/{self.config.api_version}/{self.config.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "reaction",
            "reaction": {"action": action},
        }
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"WhatsApp action error: {e.response.status_code} - {e.response.text}")
            raise

    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """验证 Webhook（GET 请求）"""
        if mode == "subscribe" and token == self.config.verify_token:
            logger.info("WhatsApp webhook verified")
            return challenge
        logger.warning("WhatsApp webhook verification failed")
        return None


# 全局实例
_whatsapp_client: Optional[WhatsAppCloudAPI] = None


def get_whatsapp_client() -> WhatsAppCloudAPI:
    """获取 WhatsApp Cloud API 全局实例"""
    global _whatsapp_client
    if _whatsapp_client is None:
        _whatsapp_client = WhatsAppCloudAPI()
    return _whatsapp_client
