"""支付宝 Native 支付（alipay.trade.precreate）与回调验签。"""

from __future__ import annotations

import base64
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from app.core.no_fake_delivery import stamp_mock

logger = logging.getLogger(__name__)

ALIPAY_GATEWAY = os.getenv(
    "ALIPAY_GATEWAY", "https://openapi.alipay.com/gateway.do"
)


@dataclass
class AlipayConfig:
    app_id: str
    private_key_pem: str
    alipay_public_key_pem: str
    notify_url: str
    gateway: str = ALIPAY_GATEWAY
    @property
    def is_live(self) -> bool:
        """is_live。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return bool(
            self.app_id
            and self.private_key_pem
            and self.alipay_public_key_pem
            and self.notify_url
        )


def load_alipay_config(notify_url: str = "") -> AlipayConfig:
    """load_alipay_config。

    参数说明：
    :param notify_url: 参数 notify_url
    :return: 返回处理结果。
    """
    inline_key = (os.getenv("ALIPAY_PRIVATE_KEY") or "").replace("\\n", "\n")
    inline_pub = (os.getenv("ALIPAY_PUBLIC_KEY") or "").replace("\\n", "\n")
    return AlipayConfig(
        app_id=os.getenv("ALIPAY_APP_ID") or "",
        private_key_pem=inline_key,
        alipay_public_key_pem=inline_pub,
        notify_url=notify_url or os.getenv("ALIPAY_NOTIFY_URL") or "",
        gateway=os.getenv("ALIPAY_GATEWAY") or ALIPAY_GATEWAY,
    )


def _normalize_pem(pem: str, label: str) -> str:
    """_normalize_pem。

    参数说明：
    :param pem: 参数 pem
    :param label: 参数 label
    :return: 返回处理结果。
    """
    text = (pem or "").strip()
    if not text:
        return ""
    if "BEGIN" in text:
        return text
    body = text.replace("\n", "").replace("\r", "")
    wrapped = "\n".join(body[i : i + 64] for i in range(0, len(body), 64))
    return f"-----BEGIN {label}-----\n{wrapped}\n-----END {label}-----"


def _sign_content(params: dict[str, Any]) -> str:
    """_sign_content。

    参数说明：
    :param params: 参数 params
    :return: 返回处理结果。
    """
    items = sorted(
        (k, v)
        for k, v in params.items()
        if k != "sign" and v is not None and str(v) != ""
    )
    return "&".join(f"{k}={v}" for k, v in items)


def _rsa2_sign(private_key_pem: str, content: str) -> str:
    """_rsa2_sign。

    参数说明：
    :param private_key_pem: 参数 private_key_pem
    :param content: 参数 content
    :return: 返回处理结果。
    """
    pem = _normalize_pem(private_key_pem, "PRIVATE KEY")
    key = serialization.load_pem_private_key(pem.encode("utf-8"), password=None)
    signature = key.sign(
        content.encode("utf-8"),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode("ascii")


def _rsa2_verify(public_key_pem: str, content: str, signature_b64: str) -> bool:
    """_rsa2_verify。

    参数说明：
    :param public_key_pem: 参数 public_key_pem
    :param content: 参数 content
    :param signature_b64: 参数 signature_b64
    :return: 返回处理结果。
    """
    if not public_key_pem or not signature_b64:
        return False
    pem = _normalize_pem(public_key_pem, "PUBLIC KEY")
    try:
        key = serialization.load_pem_public_key(pem.encode("utf-8"))
        key.verify(
            base64.b64decode(signature_b64),
            content.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return True
    except Exception:
        return False


class AlipayClient:
    """支付宝 openapi 网关客户端。"""
    def __init__(self, config: AlipayConfig):
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

    def _build_signed_params(self, method: str, biz_content: dict[str, Any]) -> dict[str, str]:
        """_build_signed_params。

        参数说明：
        :param self: 参数 self
        :param method: 参数 method
        :param biz_content: 参数 biz_content
        :return: 返回处理结果。
        """
        params: dict[str, str] = {
            "app_id": self.config.app_id,
            "method": method,
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "notify_url": self.config.notify_url,
            "biz_content": json.dumps(biz_content, ensure_ascii=False, separators=(",", ":")),
        }
        params["sign"] = _rsa2_sign(self.config.private_key_pem, _sign_content(params))
        return params

    def create_precreate(
        self,
        out_trade_no: str,
        total_fee: int,
        subject: str,
    ) -> dict[str, Any]:
        """调用 alipay.trade.precreate，返回 code_url（与微信字段对齐）。"""
        from app.services.wechat_pay_v3 import payment_mock_allowed
        if not self.is_live:
            if not payment_mock_allowed():
                raise RuntimeError(
                    "支付宝未配置（需 ALIPAY_APP_ID / 私钥 / 公钥 / NOTIFY_URL），"
                    "且生产环境已禁用 mock"
                )
            return stamp_mock(
                {
                    "code_url": f"alipay://mock/precreate?order={out_trade_no}",
                    "qr_code": f"https://mock.alipay.qrcode/{out_trade_no}",
                },
                reason="alipay_not_configured",
            )

        total_amount = f"{total_fee / 100:.2f}"
        params = self._build_signed_params(
            "alipay.trade.precreate",
            {
                "out_trade_no": out_trade_no,
                "total_amount": total_amount,
                "subject": subject[:256],
            },
        )
        try:
            with httpx.Client(timeout=20.0) as client:
                resp = client.post(self.config.gateway, data=params)
                resp.raise_for_status()
                payload = resp.json()
        except Exception as exc:
            logger.warning("支付宝 precreate 请求失败: %s", exc)
            raise RuntimeError(f"支付宝下单失败：{exc}") from exc

        response_key = "alipay_trade_precreate_response"
        body = payload.get(response_key) or {}
        sign = payload.get("sign", "")
        if sign and not _rsa2_verify(
            self.config.alipay_public_key_pem,
            json.dumps(body, ensure_ascii=False, separators=(",", ":")),
            sign,
        ):
            raise RuntimeError("支付宝响应验签失败")

        if body.get("code") != "10000":
            raise RuntimeError(
                body.get("sub_msg") or body.get("msg") or "支付宝 precreate 失败"
            )

        qr_code = body.get("qr_code") or ""
        return {"code_url": qr_code, "qr_code": qr_code, "mock": False}

    def sign_notify_payload(self, data: dict[str, Any]) -> dict[str, Any]:
        """为异步通知表单生成 RSA2 签名（沙箱/生产联调用）。"""
        payload = dict(data)
        payload["sign_type"] = "RSA2"
        content = _sign_content(
            {k: v for k, v in payload.items() if k not in ("sign", "sign_type") and v is not None}
        )
        payload["sign"] = _rsa2_sign(self.config.private_key_pem, content)
        return payload

    def verify_notify(self, data: dict[str, Any], signature: Optional[str] = None) -> bool:
        """验证支付宝异步通知 RSA2 签名。"""
        import os
        strict = os.getenv("PAYMENT_STRICT_VERIFY", "").lower() in ("1", "true", "yes")
        sign = (signature or data.get("sign") or "").strip()
        if not self.is_live:
            return not strict
        if not sign:
            return False
        verify_params = {k: v for k, v in data.items() if k != "sign" and k != "sign_type"}
        return _rsa2_verify(
            self.config.alipay_public_key_pem,
            _sign_content(verify_params),
            sign,
        )
