"""微信支付 API v3 — Native 下单与回调解密（配置齐全时走真实接口）。"""

from __future__ import annotations

import base64
import json
import logging
import os
import secrets
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger(__name__)

WECHAT_NATIVE_URL = "https://api.mch.weixin.qq.com/v3/pay/transactions/native"


@dataclass
class WeChatPayV3Config:
    appid: str
    mchid: str
    api_v3_key: str
    serial_no: str
    private_key_pem: str
    notify_url: str
    @property
    def is_live(self) -> bool:
        """is_live。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return bool(
            self.appid
            and self.mchid
            and self.api_v3_key
            and self.serial_no
            and self.private_key_pem
            and self.notify_url
        )


def payment_mock_allowed() -> bool:
    """payment_mock_allowed。
    :return: 返回处理结果。
    """
    default = "0" if os.getenv("ENVIRONMENT", "").lower() == "production" else "1"
    return os.getenv("PAYMENT_ALLOW_MOCK", default).lower() in ("1", "true", "yes")


def load_private_key_pem() -> str:
    """load_private_key_pem。
    :return: 返回处理结果。
    """
    inline = (os.getenv("WECHAT_PAY_PRIVATE_KEY") or "").strip()
    if inline:
        return inline.replace("\\n", "\n")
    path = (os.getenv("WECHAT_PAY_PRIVATE_KEY_PATH") or "").strip()
    if path and Path(path).is_file():
        return Path(path).read_text(encoding="utf-8")
    return ""


def load_wechat_pay_v3_config(
    *,
    appid: str = "",
    mchid: str = "",
    api_v3_key: str = "",
    serial_no: str = "",
    notify_url: str = "",
) -> WeChatPayV3Config:
    """load_wechat_pay_v3_config。

    参数说明：
    :param appid: 参数 appid
    :param mchid: 参数 mchid
    :param api_v3_key: 参数 api_v3_key
    :param serial_no: 参数 serial_no
    :param notify_url: 参数 notify_url
    :return: 返回处理结果。
    """
    return WeChatPayV3Config(
        appid=appid or os.getenv("WECHAT_PAY_APP_ID") or os.getenv("WECHAT_OPEN_APP_ID") or "",
        mchid=mchid or os.getenv("WECHAT_PAY_MCH_ID") or "",
        api_v3_key=api_v3_key or os.getenv("WECHAT_PAY_API_V3_KEY") or "",
        serial_no=serial_no or os.getenv("WECHAT_PAY_SERIAL_NO") or "",
        private_key_pem=load_private_key_pem(),
        notify_url=notify_url or os.getenv("WECHAT_PAY_NOTIFY_URL") or "",
    )


class WeChatPayV3Client:
    def __init__(self, config: WeChatPayV3Config):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param config: 参数 config
        :return: 返回处理结果。
        """
        self.config = config

    @property
    def is_live(self) -> bool:
        """is_live。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return self.config.is_live

    def _sign(self, message: str) -> str:
        """_sign。

        参数说明：
        :param self: 参数 self
        :param message: 参数 message
        :return: 返回处理结果。
        """
        key = serialization.load_pem_private_key(
            self.config.private_key_pem.encode("utf-8"),
            password=None,
        )
        signature = key.sign(
            message.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return base64.b64encode(signature).decode("ascii")

    def _authorization(self, method: str, url_path: str, body: str) -> str:
        """_authorization。

        参数说明：
        :param self: 参数 self
        :param method: 参数 method
        :param url_path: 参数 url_path
        :param body: 参数 body
        :return: 返回处理结果。
        """
        timestamp = str(int(time.time()))
        nonce = secrets.token_hex(16)
        sign_message = f"{method}\n{url_path}\n{timestamp}\n{nonce}\n{body}\n"
        signature = self._sign(sign_message)
        return (
            'WECHATPAY2-SHA256-RSA2048 '
            f'mchid="{self.config.mchid}",'
            f'nonce_str="{nonce}",'
            f'timestamp="{timestamp}",'
            f'serial_no="{self.config.serial_no}",'
            f'signature="{signature}"'
        )

    def create_native(
        self,
        out_trade_no: str,
        total_fee: int,
        description: str,
    ) -> dict[str, Any]:
        """create_native。

        参数说明：
        :param self: 参数 self
        :param out_trade_no: 参数 out_trade_no
        :param total_fee: 参数 total_fee
        :param description: 参数 description
        :return: 返回处理结果。
        """
        if not self.is_live:
            raise RuntimeError("微信支付 v3 未配置完整")
        body_obj = {
            "appid": self.config.appid,
            "mchid": self.config.mchid,
            "description": description[:127],
            "out_trade_no": out_trade_no,
            "notify_url": self.config.notify_url,
            "amount": {"total": int(total_fee), "currency": "CNY"},
        }
        body = json.dumps(body_obj, ensure_ascii=False)
        url_path = "/v3/pay/transactions/native"
        headers = {
            "Authorization": self._authorization("POST", url_path, body),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        with httpx.Client(timeout=20.0) as client:
            resp = client.post(WECHAT_NATIVE_URL, content=body.encode("utf-8"), headers=headers)
        if resp.status_code >= 400:
            logger.error("WeChat native order failed: %s %s", resp.status_code, resp.text[:500])
            raise RuntimeError(f"微信下单失败 HTTP {resp.status_code}")
        data = resp.json()
        return {
            "code_url": data.get("code_url", ""),
            "prepay_id": data.get("prepay_id"),
            "mock": False,
        }

    @staticmethod
    def decrypt_resource(api_v3_key: str, resource: dict[str, Any]) -> dict[str, Any]:
        """解密微信支付 v3 回调 resource 字段。"""
        ciphertext = resource.get("ciphertext")
        nonce = resource.get("nonce")
        associated_data = resource.get("associated_data") or ""
        if not ciphertext or not nonce:
            return resource if isinstance(resource, dict) else {}
        key = api_v3_key.encode("utf-8")
        aesgcm = AESGCM(key)
        plain = aesgcm.decrypt(
            nonce.encode("utf-8"),
            base64.b64decode(ciphertext),
            associated_data.encode("utf-8"),
        )
        return json.loads(plain.decode("utf-8"))

    def parse_notify_payload(self, body: dict[str, Any]) -> dict[str, Any]:
        """将 v3 加密回调或 v2 明文回调统一为 {out_trade_no, total_fee, trade_state}。"""
        resource = body.get("resource")
        if isinstance(resource, dict) and resource.get("ciphertext"):
            decrypted = self.decrypt_resource(self.config.api_v3_key, resource)
            return {
                "out_trade_no": decrypted.get("out_trade_no"),
                "total_fee": (decrypted.get("amount") or {}).get("total"),
                "transaction_id": decrypted.get("transaction_id"),
                "trade_state": decrypted.get("trade_state"),
            }
        return {
            "out_trade_no": body.get("out_trade_no"),
            "total_fee": body.get("total_fee") or body.get("amount"),
            "transaction_id": body.get("transaction_id"),
            "trade_state": body.get("trade_state") or body.get("result_code"),
        }

    def verify_v3_notify(
        self,
        body: str,
        headers: dict[str, str],
        *,
        cert_store: Optional[Any] = None,
    ) -> bool:
        """校验微信支付 v3 回调签名；优先平台证书 serial，失败时刷新缓存重试一次。"""
        timestamp = headers.get("wechatpay-timestamp") or headers.get("Wechatpay-Timestamp") or ""
        nonce = headers.get("wechatpay-nonce") or headers.get("Wechatpay-Nonce") or ""
        signature_b64 = headers.get("wechatpay-signature") or headers.get("Wechatpay-Signature") or ""
        serial = headers.get("wechatpay-serial") or headers.get("Wechatpay-Serial") or ""
        if not (timestamp and nonce and signature_b64):
            return False

        from app.services.wechat_platform_cert_service import WeChatPlatformCertStore
        store = cert_store or WeChatPlatformCertStore(self)
        for force_refresh in (False, True):
            pem = store.resolve_public_key(serial, force_refresh=force_refresh)
            if pem and self._verify_notify_with_pem(body, timestamp, nonce, signature_b64, pem):
                return True
        return False

    @staticmethod
    def _verify_notify_with_pem(
        body: str,
        timestamp: str,
        nonce: str,
        signature_b64: str,
        platform_pem: str,
    ) -> bool:
        """_verify_notify_with_pem。

        参数说明：
        :param body: 参数 body
        :param timestamp: 参数 timestamp
        :param nonce: 参数 nonce
        :param signature_b64: 参数 signature_b64
        :param platform_pem: 参数 platform_pem
        :return: 返回处理结果。
        """
        message = f"{timestamp}\n{nonce}\n{body}\n"
        pem = platform_pem if "BEGIN" in platform_pem else (
            "-----BEGIN PUBLIC KEY-----\n"
            + platform_pem.replace("\n", "")
            + "\n-----END PUBLIC KEY-----"
        )
        try:
            key = serialization.load_pem_public_key(pem.encode("utf-8"))
            key.verify(
                base64.b64decode(signature_b64),
                message.encode("utf-8"),
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
            return True
        except Exception:
            return False
