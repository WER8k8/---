"""微信支付服务（Native 扫码支付 + 回调验签 + 退款）

本模块只负责微信支付相关能力，迁移自原 app.services.payment_service 的
WeChatPayService 类。请勿在此混入订单管理等其他职责。
"""

import hashlib
import hmac
import logging
import os
import uuid
from datetime import datetime
from typing import Optional

from app.core.config import settings
from app.core.no_fake_delivery import stamp_mock

logger = logging.getLogger(__name__)


class WeChatPayService:
    """微信支付 Native 模式（扫码支付）

    使用前需在 .env 或数据库中配置微信商户号参数。
    """
    def __init__(
        self,
        appid: str = "",
        mchid: str = "",
        api_key: str = "",
        api_v3_key: str = "",
        serial_no: str = "",
        private_key_pem: str = "",
        notify_url: str = "",
    ):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param appid: 参数 appid
        :param mchid: 参数 mchid
        :param api_key: 参数 api_key
        :param api_v3_key: 参数 api_v3_key
        :param serial_no: 参数 serial_no
        :param private_key_pem: 参数 private_key_pem
        :param notify_url: 参数 notify_url
        :return: 返回处理结果。
        """
        self.appid = appid
        self.mchid = mchid
        self.api_key = api_key          # APIv2 密钥（用于签名）
        self.api_v3_key = api_v3_key    # APIv3 密钥（用于回调解密）
        self.serial_no = serial_no      # 平台证书序列号（v3）
        self.private_key_pem = private_key_pem
        self.notify_url = notify_url or f"{settings.SITE_URL}/api/v1/payment/notify/wechat"

    @property
    def is_configured(self) -> bool:
        """is_configured。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        from app.services.wechat_pay_v3 import load_wechat_pay_v3_config
        cfg = load_wechat_pay_v3_config(
            appid=self.appid,
            mchid=self.mchid,
            api_v3_key=self.api_v3_key,
            serial_no=self.serial_no,
            notify_url=self.notify_url,
        )
        if cfg.is_live:
            return True
        return bool(self.mchid and self.appid and self.api_key)

    # ------------------------------------------------------------------
    # 统一下单（Native）
    # ------------------------------------------------------------------
    def create_native_order(
        self,
        out_trade_no: str,
        total_fee: int,
        description: str,
        notify_url: Optional[str] = None,
    ) -> dict:
        """调用微信支付统一下单 API，返回 code_url（二维码内容）。"""
        from app.services.wechat_pay_v3 import (
            WeChatPayV3Client,
            load_wechat_pay_v3_config,
            payment_mock_allowed,
        )
        cfg = load_wechat_pay_v3_config(
            appid=self.appid,
            mchid=self.mchid,
            api_v3_key=self.api_v3_key,
            serial_no=self.serial_no,
            notify_url=notify_url or self.notify_url,
        )
        if not cfg.private_key_pem and self.private_key_pem:
            cfg.private_key_pem = self.private_key_pem

        client = WeChatPayV3Client(cfg)
        if client.is_live:
            return client.create_native(out_trade_no, total_fee, description)

        if not payment_mock_allowed():
            raise RuntimeError(
                "微信支付未配置（需 WECHAT_PAY_MCH_ID / API_V3_KEY / 商户私钥），"
                "且生产环境已禁用 mock"
            )

        return stamp_mock(
            {
                "code_url": f"weixin://wxpay/bizpayurl?pr=MOCK_{out_trade_no}",
                "prepay_id": f"mock_prepay_{out_trade_no}",
            },
            reason="wechat_pay_not_configured",
        )

    # ------------------------------------------------------------------
    # 回调验签
    # ------------------------------------------------------------------
    def verify_notify(self, data: dict, signature: str, *, channel: str = "wechat") -> bool:
        """验证支付回调签名。

        - 未配置 PAYMENT_WEBHOOK_SECRET 且非严格模式：演示环境放行
        - 已配置：HMAC-SHA256(order_no:amount, secret)
        - 微信 APIv2：若回调带 sign 字段且已配置 api_key，则校验 MD5 签名
        """
        import hashlib
        import hmac
        import os
        from app.services.payment_pkg.verify_flags import is_payment_strict
        strict = is_payment_strict()
        secret = (os.getenv("PAYMENT_WEBHOOK_SECRET") or "").strip()
        if data.get("sign") and self.api_key and channel == "wechat":
            expected = self._md5_sign({k: v for k, v in data.items() if k != "sign" and v})
            if hmac.compare_digest(expected, str(data.get("sign", "")).upper()):
                return True

        if not secret:
            return not strict
        if not signature:
            return False
        order_no = str(data.get("out_trade_no") or data.get("order_no") or "")
        amount = str(data.get("total_fee") or data.get("amount") or data.get("total_amount") or "")
        payload = f"{order_no}:{amount}"
        expected = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature.strip())

    def decrypt_notify_body(self, body: dict) -> Optional[dict]:
        """解密微信支付回调通知的 resource 密文

        返回解密后的明文字典，或 None（验签失败）。
        """
        # 占位：直接返回 body 中的 resource （仅用于模拟回调）
        resource = body.get("resource", {})
        if "ciphertext" in resource:
            # 真实接入：AEAD-AES-256-GCM 解密
            # ciphertext = base64.b64decode(resource["ciphertext"])
            # associated_data = resource["associated_data"]
            # nonce = resource["nonce"]
            # plaintext = ... 解密 ...
            # return json.loads(plaintext)
            pass
        return body  # 占位

    def verify_v3_notify(self, body: str, headers: dict[str, str]) -> bool:
        """微信支付 v3 回调 HTTP 头验签。"""
        from app.services.wechat_pay_v3 import WeChatPayV3Client, load_wechat_pay_v3_config
        cfg = load_wechat_pay_v3_config(
            appid=self.appid,
            mchid=self.mchid,
            api_v3_key=self.api_v3_key,
            serial_no=self.serial_no,
            notify_url=self.notify_url,
        )
        if cfg.private_key_pem and self.private_key_pem:
            cfg.private_key_pem = self.private_key_pem
        return WeChatPayV3Client(cfg).verify_v3_notify(body, headers)

    # ------------------------------------------------------------------
    # 退款申请
    # ------------------------------------------------------------------
    def refund(
        self,
        out_trade_no: str,
        refund_amount: int,
        total_amount: int,
        out_refund_no: Optional[str] = None,
    ) -> dict:
        """申请退款（未配置真实微信退款 API 时仅 dev mock）。"""
        from app.services.wechat_pay_v3 import payment_mock_allowed
        out_refund_no = out_refund_no or f"REF{datetime.now().strftime('%Y%m%d%H%M%S%f')}{uuid.uuid4().hex[:4].upper()}"
        if not payment_mock_allowed():
            raise RuntimeError("微信退款未配置，生产环境禁止 mock 退款")
        return stamp_mock(
            {
                "refund_id": f"mock_refund_{out_refund_no}",
                "out_refund_no": out_refund_no,
                "status": "SUCCESS",
                "amount": {
                    "refund": refund_amount,
                    "total": total_amount,
                },
            },
            reason="wechat_refund_not_configured",
        )

    # ------------------------------------------------------------------
    # 辅助：APIv3 签名（真实接入时使用）
    # ------------------------------------------------------------------
    def _v3_headers(self, method: str, url: str, body: str = "") -> dict:
        """生成 APIv3 认证头（占位，返回空）"""
        # 真实接入参考：
        #   token = f"{method}\n{url_path}\n{timestamp}\n{nonce}\n{body}\n"
        #   signature = rsa_sign(token, private_key)
        #   auth = f'WECHATPAY2-SHA256-RSA2048 mchid="{self.mchid}",...'
        return {}

    # ------------------------------------------------------------------
    # 辅助：MD5 签名（APIv2，兼容旧接口）
    # ------------------------------------------------------------------
    def _md5_sign(self, params: dict) -> str:
        """APIv2 MD5 签名"""
        keys = sorted(k for k in params if params[k])
        pairs = [f"{k}={params[k]}" for k in keys]
        pairs.append(f"key={self.api_key}")
        raw = "&".join(pairs)
        return hashlib.md5(raw.encode("utf-8")).hexdigest().upper()
