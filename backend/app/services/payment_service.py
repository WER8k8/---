# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""支付服务 - 支付订单管理 + 微信支付 Native 模式（扫码支付）"""

import hashlib
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

import requests
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.core.config import settings
from app.core.no_fake_delivery import is_mock_payload, stamp_mock
from app.models.payment import PaymentChannel, PaymentOrder
from app.models.tenant import TenantPlan, TenantSubscription


# =============================================================================
# 微信支付服务（占位实现，需配置真实微信商户号才能调用）
# =============================================================================

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
        strict = os.getenv("PAYMENT_STRICT_VERIFY", "").lower() in ("1", "true", "yes")
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


# =============================================================================
# 通用支付服务（对接订单模型）
# =============================================================================

class PaymentService:
    """支付服务"""
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.db = db
        # 从数据库读取支付渠道配置（如无则回退环境变量）
        self._wechat_service: Optional[WeChatPayService] = None
        self._alipay_client = None

    # ------------------------------------------------------------------
    # 获取微信支付服务实例（懒加载）
    # ------------------------------------------------------------------
    @property
    def wechat(self) -> WeChatPayService:
        """wechat。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if self._wechat_service is None:
            channel = self.db.query(PaymentChannel).filter(
                PaymentChannel.channel == "wechat",
                PaymentChannel.is_active.is_(True),
            ).first()
            if channel and isinstance(getattr(channel, "config", None), str):
                try:
                    cfg = json.loads(channel.config) if channel.config else {}
                except Exception:
                    cfg = {}
            else:
                cfg = {}
            self._wechat_service = WeChatPayService(
                appid=cfg.get("appid", settings.WECHAT_OPEN_APP_ID or ""),
                mchid=cfg.get("mchid", ""),
                api_key=cfg.get("api_key", ""),
                api_v3_key=cfg.get("api_v3_key", ""),
                serial_no=cfg.get("serial_no", ""),
                notify_url=cfg.get(
                    "notify_url",
                    f"{settings.SITE_URL}/api/v1/payment/notify/wechat",
                ),
            )
        return self._wechat_service

    @property
    def alipay(self):
        """alipay。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if self._alipay_client is None:
            from app.services.alipay_client import AlipayClient, load_alipay_config
            notify = f"{settings.SITE_URL}/api/v1/payment/notify/alipay"
            self._alipay_client = AlipayClient(load_alipay_config(notify_url=notify))
        return self._alipay_client

    def _create_channel_native(
        self,
        channel: str,
        out_trade_no: str,
        total_fee: int,
        subject: str,
    ) -> dict:
        """按渠道调用 Native 预下单，返回含 code_url / mock 的字典。"""
        ch = (channel or "wechat").lower()
        if ch == "alipay":
            return self.alipay.create_precreate(out_trade_no, total_fee, subject)
        return self.wechat.create_native_order(out_trade_no, total_fee, subject)

    def _verify_notify_amount_guard(self, data: dict) -> bool:
        """严验签下 egress 加购金额校验（非 egress 订单直接通过）。"""
        import os
        strict = os.getenv("PAYMENT_STRICT_VERIFY", "").lower() in ("1", "true", "yes")
        if not strict:
            return True
        order_no = str(data.get("out_trade_no") or data.get("order_no") or "")
        if not order_no:
            return False
        order = self.get_order_by_no(order_no)
        if not order:
            return False
        from app.services.egress_addon_service import (
            EGRESS_SLOT_PRICE_CENTS,
            parse_addon_slots,
        )
        slots = parse_addon_slots(order.subject or "")
        if not slots:
            return True
        paid_raw = (
            data.get("total_fee")
            or data.get("amount")
            or data.get("total_amount")
            or order.amount
            or 0
        )
        if isinstance(paid_raw, dict):
            paid_raw = paid_raw.get("total") or order.amount
        try:
            paid = int(round(float(paid_raw) * 100)) if isinstance(paid_raw, str) and "." in str(paid_raw) else int(paid_raw)
        except (TypeError, ValueError):
            paid = int(order.amount or 0)
        return paid == EGRESS_SLOT_PRICE_CENTS * slots

    def verify_notify(self, data: dict, signature: str, *, channel: str = "wechat") -> bool:
        """支付回调验签；支持 HMAC / 渠道验签 + egress 严验。"""
        import hashlib
        import hmac
        import os
        secret = (os.getenv("PAYMENT_WEBHOOK_SECRET") or "").strip()
        sig = (signature or "").strip()
        if secret and sig:
            order_no = str(data.get("out_trade_no") or data.get("order_no") or "")
            amount_raw = data.get("total_fee") or data.get("amount") or data.get("total_amount") or ""
            if isinstance(amount_raw, dict):
                amount = str(amount_raw.get("total") or "")
            else:
                amount = str(amount_raw)
            payload = f"{order_no}:{amount}"
            expected = hmac.new(
                secret.encode("utf-8"),
                payload.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            if hmac.compare_digest(expected, sig):
                return self._verify_notify_amount_guard(data)

        ch = (channel or "wechat").lower()
        if ch == "alipay":
            if not self.alipay.verify_notify(data, signature or data.get("sign")):
                return False
        elif not self.wechat.verify_notify(data, signature, channel=channel):
            return False
        return self._verify_notify_amount_guard(data)

    # ------------------------------------------------------------------
    # 创建支付订单（基础）
    # ------------------------------------------------------------------
    def create_payment_order(
        self,
        tenant_id: str,
        subscription_id: str,
        amount: int,
        channel: str,
        subject: str,
        currency: str = "CNY",
    ) -> PaymentOrder:
        """创建支付订单"""
        order_no = self._generate_order_no()
        order = PaymentOrder(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            subscription_id=subscription_id,
            order_no=order_no,
            amount=amount,
            currency=currency,
            channel=channel,
            subject=subject,
            status="pending",
        )
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order

    # ------------------------------------------------------------------
    # 创建 Native 支付订单（含调用微信统一下单）
    # ------------------------------------------------------------------
    def create_native_payment(
        self,
        tenant_id: str,
        plan_id: str,
        billing_cycle: str,
        current_user_id: str,
        channel: str = "wechat",
    ) -> dict:
        """创建扫码支付订单并返回二维码 URL

        Args:
            tenant_id:  租户 ID
            plan_id:    套餐 ID
            billing_cycle: monthly / yearly
            current_user_id: 当前用户 ID

        Returns:
            {
                "order": PaymentOrder,
                "code_url": "weixin://...",
                "mode": "mock|live",
            }
        """
        # 1. 查套餐
        plan = self.db.query(TenantPlan).filter(
            TenantPlan.id == plan_id,
            TenantPlan.is_active.is_(True),
        ).first()
        if not plan:
            raise ValueError("套餐不存在或已停用")

        # 2. 算价格
        amount = plan.price_yearly if billing_cycle == "yearly" else plan.price_monthly
        if amount <= 0:
            raise ValueError("该套餐免费，无需支付")

        # 3. 创建或更新订阅记录
        subscription = self.db.query(TenantSubscription).filter(
            TenantSubscription.tenant_id == tenant_id,
            TenantSubscription.plan_id == plan_id,
            TenantSubscription.status == "active",
        ).first()
        if not subscription:
            subscription = TenantSubscription(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                plan_id=plan_id,
                billing_cycle=billing_cycle,
                amount=amount,
                status="active",
                started_at=datetime.now(timezone.utc),
            )
            self.db.add(subscription)
            self.db.flush()
        else:
            # 已存在订阅 → 刷新周期和金额
            subscription.billing_cycle = billing_cycle
            subscription.amount = amount
            self.db.flush()

        # 4. 创建支付订单
        subject = f"{plan.name} - {'年付' if billing_cycle == 'yearly' else '月付'}"
        pay_channel = (channel or "wechat").lower()
        if pay_channel not in ("wechat", "alipay"):
            raise ValueError("channel 须为 wechat 或 alipay")

        order = self.create_payment_order(
            tenant_id=tenant_id,
            subscription_id=subscription.id,
            amount=amount,
            channel=pay_channel,
            subject=subject,
        )
        # 5. 调用渠道 Native 预下单
        try:
            pay_result = self._create_channel_native(
                pay_channel,
                order.order_no,
                amount,
                subject,
            )
            code_url = pay_result.get("code_url", "")
            mock = is_mock_payload(pay_result)
        except Exception as exc:
            if settings.ENVIRONMENT == "production":
                self.db.rollback()
                raise RuntimeError(
                    f"{pay_channel} 支付下单失败（生产环境不降级 mock）：{exc}"
                ) from exc
            logger.warning("%s 支付 API 调用失败，降级为 mock 模式: %s", pay_channel, exc)
            code_url = ""
            mock = True

        self.db.commit()
        return {
            "order": order,
            "code_url": code_url,
            "mock": mock,
        }

    # ------------------------------------------------------------------
    # 财务入账：支付成功 → FinanceLedgerEntry
    # ------------------------------------------------------------------
    def _record_revenue(self, order: PaymentOrder) -> None:
        """支付成功后自动写入财务台账（幂等，按 order_no 去重）。"""
        try:
            from app.models.finance_ledger import FinanceLedgerEntry
            exists = (
                self.db.query(FinanceLedgerEntry.id)
                .filter(
                    FinanceLedgerEntry.reference_id == order.order_no,
                    FinanceLedgerEntry.entry_type == "revenue",
                )
                .first()
            )
            if exists:
                return

            if order.channel in ("mock", "mock_pay"):
                category = "mock_pay"
            else:
                category = "egress_ip" if "egress" in (order.subject or "").lower() else (
                    "token" if "token" in (order.subject or "").lower() else "subscription"
                )
            entry = FinanceLedgerEntry(
                entry_type="revenue",
                category=category,
                amount_cents=order.amount,
                tenant_id=order.tenant_id,
                reference_id=order.order_no,
                note=f"支付渠道:{order.channel} | 订单:{order.order_no} | {order.subject or ''}",
            )
            self.db.add(entry)
            self.db.commit()
            logger.info(
                "FinanceLedgerEntry created: order=%s tenant=%s amount=%s category=%s",
                order.order_no, order.tenant_id, order.amount, category,
            )
        except Exception:
            logger.exception("FinanceLedgerEntry 写入失败 order=%s", order.order_no)

    # ------------------------------------------------------------------
    # 处理微信支付回调
    # ------------------------------------------------------------------
    def process_wechat_notify(self, data: dict) -> Optional[PaymentOrder]:
        """处理微信支付回调通知（兼容 v3 加密体与 v2 明文）。"""
        from app.services.wechat_pay_v3 import WeChatPayV3Client, load_wechat_pay_v3_config
        cfg = load_wechat_pay_v3_config(
            appid=self.wechat.appid,
            mchid=self.wechat.mchid,
            api_v3_key=self.wechat.api_v3_key,
            serial_no=self.wechat.serial_no,
            notify_url=self.wechat.notify_url,
        )
        parsed = WeChatPayV3Client(cfg).parse_notify_payload(data)
        trade_state = (parsed.get("trade_state") or "").upper()
        if trade_state and trade_state not in ("SUCCESS", "SUCCESSFUL"):
            return None

        order_no = parsed.get("out_trade_no") or data.get("out_trade_no")
        if not order_no:
            return None

        order = self.db.query(PaymentOrder).filter(
            PaymentOrder.order_no == order_no
        ).first()
        if not order or order.status != "pending":
            return None

        order.status = "paid"
        order.paid_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(order)
        self._record_revenue(order)
        # BUG-02 修复：权益发放失败时记录补偿任务，不阻断回调响应
        # 渠道可立即收到成功响应并重试；补偿任务由定时巡检处理
        try:
            self._provision_paid_order(order)
            self._sync_b2b_order_from_notify({**data, **parsed})
            logger.info("WeChat notify success | order_no=%s", order_no)
        except Exception as exc:
            logger.error(
                "WeChat provision failed, scheduled compensation | order_no=%s err=%s",
                order_no,
                exc,
                exc_info=True,
            )
            self._schedule_compensation(order, source="wechat_notify")
        return order

    # ------------------------------------------------------------------
    # 处理支付宝回调
    # ------------------------------------------------------------------
    def process_alipay_notify(self, data: dict) -> Optional[PaymentOrder]:
        """处理支付宝回调（trade_status + 金额校验）。"""
        order_no = data.get("out_trade_no")
        trade_status = (data.get("trade_status") or "").upper()
        if not order_no:
            return None
        if trade_status not in ("TRADE_SUCCESS", "TRADE_FINISHED"):
            return None

        order = self.db.query(PaymentOrder).filter(
            PaymentOrder.order_no == order_no
        ).first()
        if not order or order.status != "pending":
            return None

        paid_yuan = data.get("total_amount") or data.get("receipt_amount")
        if paid_yuan is not None:
            try:
                paid_cents = int(round(float(paid_yuan) * 100))
                if paid_cents != int(order.amount):
                    logger.warning(
                        "alipay amount mismatch order=%s expected=%s got=%s",
                        order_no,
                        order.amount,
                        paid_cents,
                    )
                    return None
            except (TypeError, ValueError):
                pass

        order.status = "paid"
        order.paid_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(order)
        self._record_revenue(order)
        # BUG-02 修复：权益发放失败时记录补偿任务
        try:
            self._provision_paid_order(order)
            self._sync_b2b_order_from_notify(data)
            logger.info("Alipay notify success | order_no=%s", order_no)
        except Exception as exc:
            logger.error(
                "Alipay provision failed, scheduled compensation | order_no=%s err=%s",
                order_no,
                exc,
                exc_info=True,
            )
            self._schedule_compensation(order, source="alipay_notify")
        return order

    # ------------------------------------------------------------------
    # 模拟支付成功（管理员后台手动确认）
    # ------------------------------------------------------------------
    def mock_pay_order(self, order_id: str) -> Optional[PaymentOrder]:
        """将指定订单标记为已支付（仅用于占位/演示环境）"""
        order = self.db.query(PaymentOrder).filter(
            PaymentOrder.id == order_id
        ).first()
        if not order or order.status != "pending":
            return None
        order.channel = "mock"
        order.status = "paid"
        order.paid_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(order)
        self._record_revenue(order)
        self._provision_paid_order(order)
        return order

    def _sync_b2b_order_from_notify(self, data: dict) -> None:
        """_sync_b2b_order_from_notify。

        参数说明：
        :param self: 参数 self
        :param data: 参数 data
        :return: 返回处理结果。
        """
        from app.services.order_payment_sync_service import sync_b2b_from_payment_notify
        sync_b2b_from_payment_notify(self.db, data or {})

    # ------------------------------------------------------------------
    # BUG-02 修复：补偿任务调度
    # ------------------------------------------------------------------
    def _schedule_compensation(self, order: PaymentOrder, source: str) -> None:
        """权益发放失败时，记录补偿任务供定时巡检处理。

        补偿任务以 order_no 为幂等键，定时巡检会重试直到发放成功。
        这确保支付回调失败时不会静默丢失权益。
        """
        from datetime import datetime, timezone
        from app.models.payment import PaymentCompensationTask
        try:
            # 幂等检查：同一 order_no 不再重复记录
            existing = (
                self.db.query(PaymentCompensationTask)
                .filter(
                    PaymentCompensationTask.order_no == order.order_no,
                    PaymentCompensationTask.status == "pending",
                )
                .first()
            )
            if existing:
                logger.warning(
                    "Compensation already pending | order_no=%s",
                    order.order_no,
                )
                return

            task = PaymentCompensationTask(
                order_no=order.order_no,
                source=source,
                status="pending",
                attempts=0,
                last_error=None,
                scheduled_at=datetime.now(timezone.utc),
            )
            self.db.add(task)
            self.db.commit()
            logger.info(
                "Compensation task created | order_no=%s source=%s",
                order.order_no,
                source,
            )
        except Exception as exc:
            logger.error(
                "Failed to create compensation task | order_no=%s err=%s",
                order.order_no,
                exc,
                exc_info=True,
            )
        sync_b2b_from_payment_notify(self.db, data or {})

    def create_egress_addon_order(
        self,
        tenant_id: str,
        slots: int,
        channel: str = "wechat",
    ) -> PaymentOrder:
        """create_egress_addon_order。

        参数说明：
        :param self: 参数 self
        :param tenant_id: 参数 tenant_id
        :param slots: 参数 slots
        :param channel: 参数 channel
        :return: 返回处理结果。
        """
        from app.services.egress_addon_service import (
            EGRESS_SLOT_PRICE_CENTS,
            addon_subject,
        )
        if slots < 1 or slots > 20:
            raise ValueError("slots 须在 1～20 之间")
        amount = EGRESS_SLOT_PRICE_CENTS * slots
        return self.create_payment_order(
            tenant_id=tenant_id,
            subscription_id=None,
            amount=amount,
            channel=channel,
            subject=addon_subject(slots),
        )

    def create_egress_addon_native(
        self,
        tenant_id: str,
        slots: int,
        channel: str = "wechat",
    ) -> dict:
        """创建 Egress IP 槽位 Native 支付订单并返回二维码。"""
        pay_channel = (channel or "wechat").lower()
        if pay_channel not in ("wechat", "alipay"):
            raise ValueError("channel 须为 wechat 或 alipay")

        order = self.create_egress_addon_order(tenant_id, slots, pay_channel)
        subject = order.subject
        try:
            pay_result = self._create_channel_native(
                pay_channel,
                order.order_no,
                order.amount,
                subject,
            )
            code_url = pay_result.get("code_url", "")
            mock = is_mock_payload(pay_result)
        except Exception as exc:
            if settings.ENVIRONMENT == "production":
                self.db.rollback()
                raise RuntimeError(f"{pay_channel} 支付下单失败：{exc}") from exc
            logger.warning("Egress 加购 %s 支付降级 mock: %s", pay_channel, exc)
            code_url = ""
            mock = True
        self.db.commit()
        return {
            "order": order,
            "code_url": code_url,
            "mock": mock,
            "slots": slots,
        }

    def create_token_pack_order(
        self,
        tenant_id: str,
        pack_id: str,
        channel: str = "wechat",
        provider_id: str | None = None,
    ) -> PaymentOrder:
        """create_token_pack_order。

        参数说明：
        :param self: 参数 self
        :param tenant_id: 参数 tenant_id
        :param pack_id: 参数 pack_id
        :param channel: 参数 channel
        :param provider_id: 参数 provider_id
        :return: 返回处理结果。
        """
        from app.services.order_addon_service import resolve_pack, token_addon_subject
        pack = resolve_pack(pack_id)
        return self.create_payment_order(
            tenant_id=tenant_id,
            subscription_id=None,
            amount=int(pack["price_cents"]),
            channel=channel,
            subject=token_addon_subject(int(pack["tokens"]), provider_id),
        )

    def create_custom_token_recharge_order(
        self,
        tenant_id: str,
        amount_yuan: float,
        channel: str = "wechat",
        provider_id: str | None = None,
    ) -> PaymentOrder:
        """create_custom_token_recharge_order。

        参数说明：
        :param self: 参数 self
        :param tenant_id: 参数 tenant_id
        :param amount_yuan: 参数 amount_yuan
        :param channel: 参数 channel
        :param provider_id: 参数 provider_id
        :return: 返回处理结果。
        """
        from app.services.order_addon_service import (
            resolve_custom_token_recharge,
            token_addon_subject,
        )
        spec = resolve_custom_token_recharge(amount_yuan)
        return self.create_payment_order(
            tenant_id=tenant_id,
            subscription_id=None,
            amount=int(spec["price_cents"]),
            channel=channel,
            subject=token_addon_subject(int(spec["tokens"]), provider_id),
        )

    def create_token_pack_native(
        self,
        tenant_id: str,
        channel: str = "wechat",
        provider_id: str | None = None,
        *,
        pack_id: str | None = None,
        amount_yuan: float | None = None,
    ) -> dict:
        """创建 Token 包或自定义金额 Native 支付订单并返回二维码。"""
        from app.services.order_addon_service import resolve_pack
        pay_channel = (channel or "wechat").lower()
        if pay_channel not in ("wechat", "alipay"):
            raise ValueError("channel 须为 wechat 或 alipay")
        if pack_id and amount_yuan is not None:
            raise ValueError("pack_id 与 amount_yuan 只能二选一")
        if not pack_id and amount_yuan is None:
            raise ValueError("请指定 pack_id 或 amount_yuan")

        if pack_id:
            order = self.create_token_pack_order(
                tenant_id, pack_id, pay_channel, provider_id=provider_id
            )
            tokens = int(resolve_pack(pack_id)["tokens"])
        else:
            order = self.create_custom_token_recharge_order(
                tenant_id, float(amount_yuan), pay_channel, provider_id=provider_id
            )
            from app.services.order_addon_service import parse_token_addon
            tokens, _ = parse_token_addon(order.subject)
            tokens = int(tokens or 0)

        subject = order.subject
        try:
            pay_result = self._create_channel_native(
                pay_channel,
                order.order_no,
                order.amount,
                subject,
            )
            code_url = pay_result.get("code_url", "")
            mock = is_mock_payload(pay_result)
        except Exception as exc:
            if settings.ENVIRONMENT == "production":
                self.db.rollback()
                raise RuntimeError(f"{pay_channel} 支付下单失败：{exc}") from exc
            logger.warning("Token 包 %s 支付降级 mock: %s", pay_channel, exc)
            code_url = ""
            mock = True
        self.db.commit()
        return {
            "order": order,
            "code_url": code_url,
            "mock": mock,
            "pack_id": pack_id,
            "amount_yuan": amount_yuan,
            "tokens": tokens,
        }

    def _provision_paid_order(self, order: PaymentOrder) -> None:
        """_provision_paid_order。

        参数说明：
        :param self: 参数 self
        :param order: 参数 order
        :return: 返回处理结果。
        """
        from app.services.provisioning_service import ProvisioningService
        ProvisioningService(self.db).provision_after_payment(order)

    # ------------------------------------------------------------------
    # 订单查询
    # ------------------------------------------------------------------
    def get_order(self, order_id: str) -> Optional[PaymentOrder]:
        """查询订单"""
        return self.db.query(PaymentOrder).filter(
            PaymentOrder.id == order_id
        ).first()

    def get_order_by_no(self, order_no: str) -> Optional[PaymentOrder]:
        """按商户订单号查询"""
        return self.db.query(PaymentOrder).filter(
            PaymentOrder.order_no == order_no
        ).first()

    def list_orders(
        self,
        tenant_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ):
        """订单列表"""
        query = self.db.query(PaymentOrder)
        if tenant_id:
            query = query.filter(PaymentOrder.tenant_id == tenant_id)
        if status:
            query = query.filter(PaymentOrder.status == status)
        total = query.count()
        items = query.order_by(
            PaymentOrder.created_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    # ------------------------------------------------------------------
    # 工具
    # ------------------------------------------------------------------
    @staticmethod
    def _generate_order_no() -> str:
        """生成唯一商户订单号"""
        ts = datetime.now().strftime("%Y%m%d%H%M%S%f")
        rand = str(uuid.uuid4().hex[:8]).upper()
        return f"ORD{ts}{rand}"
