import asyncio
import json
import logging
import time
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class FeishuClient:
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._app_id = settings.FEISHU_APP_ID
        self._app_secret = settings.FEISHU_APP_SECRET
        self._base_url = settings.FEISHU_API_BASE_URL
        self._tenant_access_token: Optional[str] = None
        self._token_expire_time: float = 0
        self._http_client: Optional[httpx.AsyncClient] = None
        self._sync_http_client: Optional[httpx.Client] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """_get_client。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=httpx.Timeout(15.0),
            )
        return self._http_client

    async def _refresh_token(self):
        """_refresh_token。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if not self._app_id or not self._app_secret:
            logger.warning("飞书AppID或AppSecret未配置")
            return
        client = await self._get_client()
        resp = await client.post(
            "/auth/v3/tenant_access_token/internal",
            json={"app_id": self._app_id, "app_secret": self._app_secret},
        )
        data = resp.json()
        if data.get("code") != 0:
            logger.error(f"获取飞书token失败: {data}")
            return
        self._tenant_access_token = data["tenant_access_token"]
        self._token_expire_time = time.time() + data.get("expire", 7200) - 60

    async def _ensure_token(self):
        """_ensure_token。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if not self._tenant_access_token or time.time() >= self._token_expire_time:
            await self._refresh_token()

    async def send_text_message(self, open_id: str, text: str) -> dict:
        """send_text_message。

        参数说明：
        :param self: 参数 self
        :param open_id: 参数 open_id
        :param text: 参数 text
        :return: 返回处理结果。
        """
        await self._ensure_token()
        client = await self._get_client()
        resp = await client.post(
            "/im/v1/messages",
            params={"receive_id_type": "open_id"},
            headers={
                "Authorization": f"Bearer {self._tenant_access_token}",
                "Content-Type": "application/json",
            },
            json={
                "receive_id": open_id,
                "msg_type": "text",
                "content": json.dumps({"text": text}),
            },
        )
        return resp.json()

    async def send_card_message(self, open_id: str, card: dict) -> dict:
        """send_card_message。

        参数说明：
        :param self: 参数 self
        :param open_id: 参数 open_id
        :param card: 参数 card
        :return: 返回处理结果。
        """
        await self._ensure_token()
        client = await self._get_client()
        raw_content = json.dumps(card, ensure_ascii=False)
        if isinstance(card, dict) and "config" not in card:
            card["config"] = {"wide_screen_mode": True}

        resp = await client.post(
            "/im/v1/messages",
            params={"receive_id_type": "open_id"},
            headers={
                "Authorization": f"Bearer {self._tenant_access_token}",
                "Content-Type": "application/json",
            },
            json={
                "receive_id": open_id,
                "msg_type": "interactive",
                "content": json.dumps(card, ensure_ascii=False),
            },
        )
        return resp.json()

    async def send_text_to_user_by_email(self, email: str, text: str) -> dict:
        """send_text_to_user_by_email。

        参数说明：
        :param self: 参数 self
        :param email: 参数 email
        :param text: 参数 text
        :return: 返回处理结果。
        """
        await self._ensure_token()
        client = await self._get_client()
        email_resp = await client.post(
            "/im/v1/users/batch_get_id",
            headers={
                "Authorization": f"Bearer {self._tenant_access_token}",
                "Content-Type": "application/json",
            },
            json={"emails": [email]},
        )
        user_data = email_resp.json()
        if user_data.get("code") != 0 or not user_data.get(
                "data", {}).get("user_list"):
            logger.warning(f"未找到飞书用户: {email}")
            return user_data
        open_id = user_data["data"]["user_list"][0]["user_id"]["open_id"]
        return await self.send_text_message(open_id, text)

    async def get_user_info(self, open_id: str) -> Optional[dict]:
        """get_user_info。

        参数说明：
        :param self: 参数 self
        :param open_id: 参数 open_id
        :return: 返回处理结果。
        """
        await self._ensure_token()
        client = await self._get_client()
        resp = await client.get(
            f"/im/v1/users/{open_id}",
            headers={"Authorization": f"Bearer {self._tenant_access_token}"},
        )
        data = resp.json()
        if data.get("code") == 0:
            return data.get("data", {}).get("user")
        return None

    async def reply_message(
            self,
            message_id: str,
            content: str,
            msg_type: str = "text") -> dict:
        """reply_message。

        参数说明：
        :param self: 参数 self
        :param message_id: 参数 message_id
        :param content: 参数 content
        :param msg_type: 参数 msg_type
        :return: 返回处理结果。
        """
        await self._ensure_token()
        client = await self._get_client()
        resp = await client.post(
            f"/im/v1/messages/{message_id}/reply",
            headers={
                "Authorization": f"Bearer {self._tenant_access_token}",
                "Content-Type": "application/json",
            },
            json={
                "msg_type": msg_type,
                "content": content,
            },
        )
        return resp.json()

    async def upload_image(self, image_path: str) -> Optional[str]:
        """upload_image。

        参数说明：
        :param self: 参数 self
        :param image_path: 参数 image_path
        :return: 返回处理结果。
        """
        await self._ensure_token()
        client = await self._get_client()
        with open(image_path, "rb") as f:
            files = {"image": f}
            resp = await client.post(
                "/im/v1/images",
                headers={"Authorization": f"Bearer {self._tenant_access_token}"},
                files=files,
                data={"image_type": "message"},
            )
        data = resp.json()
        if data.get("code") == 0:
            return data["data"]["image_key"]
        logger.error(f"上传图片失败: {data}")
        return None

    async def close(self):
        """close。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
        if self._sync_http_client:
            self._sync_http_client.close()
            self._sync_http_client = None

    # ==================== 同步方法（用于告警等同步场景） ====================
    def _get_sync_client(self) -> httpx.Client:
        """_get_sync_client。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if self._sync_http_client is None:
            self._sync_http_client = httpx.Client(
                base_url=self._base_url,
                timeout=httpx.Timeout(15.0),
            )
        return self._sync_http_client

    def _refresh_token_sync(self):
        """_refresh_token_sync。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if not self._app_id or not self._app_secret:
            logger.warning("飞书AppID或AppSecret未配置")
            return
        client = self._get_sync_client()
        resp = client.post(
            "/auth/v3/tenant_access_token/internal",
            json={"app_id": self._app_id, "app_secret": self._app_secret},
        )
        data = resp.json()
        if data.get("code") != 0:
            logger.error(f"获取飞书token失败: {data}")
            return
        self._tenant_access_token = data["tenant_access_token"]
        self._token_expire_time = time.time() + data.get("expire", 7200) - 60

    def _ensure_token_sync(self):
        """_ensure_token_sync。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if not self._tenant_access_token or time.time() >= self._token_expire_time:
            self._refresh_token_sync()

    def send_text_message_sync(self, open_id: str, text: str) -> dict:
        """send_text_message_sync。

        参数说明：
        :param self: 参数 self
        :param open_id: 参数 open_id
        :param text: 参数 text
        :return: 返回处理结果。
        """
        self._ensure_token_sync()
        client = self._get_sync_client()
        resp = client.post(
            "/im/v1/messages",
            params={"receive_id_type": "open_id"},
            headers={
                "Authorization": f"Bearer {self._tenant_access_token}",
                "Content-Type": "application/json",
            },
            json={
                "receive_id": open_id,
                "msg_type": "text",
                "content": json.dumps({"text": text}),
            },
        )
        return resp.json()

    def send_card_message_sync(self, open_id: str, card: dict) -> dict:
        """send_card_message_sync。

        参数说明：
        :param self: 参数 self
        :param open_id: 参数 open_id
        :param card: 参数 card
        :return: 返回处理结果。
        """
        self._ensure_token_sync()
        client = self._get_sync_client()
        if isinstance(card, dict) and "config" not in card:
            card["config"] = {"wide_screen_mode": True}

        resp = client.post(
            "/im/v1/messages",
            params={"receive_id_type": "open_id"},
            headers={
                "Authorization": f"Bearer {self._tenant_access_token}",
                "Content-Type": "application/json",
            },
            json={
                "receive_id": open_id,
                "msg_type": "interactive",
                "content": json.dumps(card, ensure_ascii=False),
            },
        )
        return resp.json()

    def send_broadcast_message(self, text: str, card: dict = None) -> bool:
        """
        发送广播消息到飞书机器人（同步版本，用于告警等场景）
        默认发送到配置的管理员或群组
        """
        # 如果配置了Webhook，优先使用Webhook发送
        if settings.FEISHU_WEBHOOK_URL:
            return self.send_webhook_message(text, card)

        try:
            self._ensure_token_sync()
            # 优先发送卡片消息
            if card:
                # 发送给默认管理员（需要配置或使用群消息）
                # 这里使用文本消息作为演示，实际应根据配置发送到指定用户/群组
                client = self._get_sync_client()
                resp = client.post(
                    "/im/v1/messages",
                    params={
                        "receive_id_type": "open_id"},
                    headers={
                        "Authorization": f"Bearer {self._tenant_access_token}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "receive_id": settings.FEISHU_DEFAULT_RECEIVER or "ou_xxx",
                        "msg_type": "interactive",
                        "content": json.dumps(
                            card,
                            ensure_ascii=False),
                    },
                )
                result = resp.json()
                if result.get("code") == 0:
                    logger.info(f"飞书广播消息发送成功")
                    return True
                else:
                    logger.error(f"飞书消息发送失败: {result}")
                    return False
            else:
                # 发送文本消息
                # 实际应发送到配置的接收者
                logger.info(f"飞书广播消息（文本）: {text[:50]}...")
                return True

        except Exception as e:
            logger.error(f"发送飞书广播消息异常: {e}")
            return False

    def send_webhook_message(self, text: str, card: dict = None) -> bool:
        """
        通过飞书群机器人Webhook发送消息
        """
        if not settings.FEISHU_WEBHOOK_URL:
            logger.error("飞书Webhook URL未配置")
            return False

        try:
            client = self._get_sync_client()
            if card:
                # 发送卡片消息
                if isinstance(card, dict) and "config" not in card:
                    card["config"] = {"wide_screen_mode": True}
                payload = {
                    "msg_type": "interactive",
                    "card": card,
                }
            else:
                # 发送文本消息
                payload = {
                    "msg_type": "text",
                    "content": {"text": text},
                }

            resp = client.post(
                settings.FEISHU_WEBHOOK_URL,
                headers={"Content-Type": "application/json"},
                json=payload,
            )
            if resp.status_code == 200:
                result = resp.json()
                if result.get("code") == 0:
                    logger.info(f"飞书Webhook消息发送成功")
                    return True
                else:
                    logger.error(f"飞书Webhook消息发送失败: {result}")
                    return False
            else:
                logger.error(f"飞书Webhook请求失败，状态码: {resp.status_code}")
                return False

        except Exception as e:
            logger.error(f"发送飞书Webhook消息异常: {e}")
            return False

    async def send_webhook_message_async(
            self, text: str, card: dict = None) -> bool:
        """
        通过飞书群机器人Webhook异步发送消息
        """
        if not settings.FEISHU_WEBHOOK_URL:
            logger.error("飞书Webhook URL未配置")
            return False

        try:
            client = await self._get_client()
            if card:
                # 发送卡片消息
                if isinstance(card, dict) and "config" not in card:
                    card["config"] = {"wide_screen_mode": True}
                payload = {
                    "msg_type": "interactive",
                    "card": card,
                }
            else:
                # 发送文本消息
                payload = {
                    "msg_type": "text",
                    "content": {"text": text},
                }

            resp = await client.post(
                settings.FEISHU_WEBHOOK_URL,
                headers={"Content-Type": "application/json"},
                json=payload,
            )
            if resp.status_code == 200:
                result = resp.json()
                if result.get("code") == 0:
                    logger.info(f"飞书Webhook消息发送成功")
                    return True
                else:
                    logger.error(f"飞书Webhook消息发送失败: {result}")
                    return False
            else:
                logger.error(f"飞书Webhook请求失败，状态码: {resp.status_code}")
                return False

        except Exception as e:
            logger.error(f"发送飞书Webhook消息异常: {e}")
            return False
