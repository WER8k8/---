"""通用支付服务（对接订单模型）

本模块只负责支付订单管理、渠道下单、回调处理与入账，迁移自原
app.services.payment_service 的 PaymentService 类。微信支付底层能力位于
同包的 wechat_pay 模块。
"""

import hashlib
import hmac
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.no_fake_delivery import is_mock_payload
from app.models.payment import PaymentChannel, PaymentOrder
from app.models.tenant import TenantPlan, TenantSubscription

from .wechat_pay import WeChatPayService

logger = logging.getLogger(__name__)


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
            if channel:
                cfg = json.loads(channel.config) if channel.config else {}
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
        from app.services.payment_pkg.verify_flags import is_payment_strict
        strict = is_payment_strict()
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
        # --- 风控检查（数据库写入之前） ---
        try:
            from app.core.payment_risk import assess_payment_risk, should_block_payment
            risk_result = assess_payment_risk(
                user_id="unknown",  # create_payment_order doesn't have user_id
                tenant_id=tenant_id,
                amount=float(amount),
                currency=currency,
                channel=channel,
            )
            if should_block_payment(risk_result.risk_score):
                logger.warning("[PaymentService] 风控拦截: tenant=%s amount=%s risk=%s",
                               tenant_id, amount, risk_result.risk_score)
                raise ValueError(f"支付被风控拦截: 风险评分 {risk_result.risk_score}")
            if risk_result.level == "high":
                logger.warning("[PaymentService] 高风险支付: tenant=%s amount=%s details=%s",
                               tenant_id, amount, risk_result.reasons)
        except ImportError:
            logger.debug("[PaymentService] 风控模块未加载，跳过风控检查")
        except ValueError:
            raise  # 风控拦截错误需要抛出
        except Exception as exc:
            # BUG-07 修复：fail-closed，风控异常时拒绝支付而非放行
            logger.error("[PaymentService] 风控检查异常，拒绝创建订单: %s", exc, exc_info=True)
            raise ValueError(f"风控检查异常，订单创建失败: {exc}")

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
            # BUG-09 修复：财务台账写入失败时回滚并重新抛出，不静默吞异常
            self.db.rollback()
            logger.exception("FinanceLedgerEntry 写入失败 order=%s", order.order_no)
            raise

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

        # 读取订单用于金额校验（F5）；不在此处改状态，避免 TOCTOU 重复发放
        order = self.db.query(PaymentOrder).filter(
            PaymentOrder.order_no == order_no
        ).first()
        if not order:
            return None

        # F5: 微信回调金额比对（v3 amount.total 单位为分）；字段缺失则不强制
        amount_info = parsed.get("amount") or data.get("amount") or {}
        paid_total = amount_info.get("total") if isinstance(amount_info, dict) else None
        if paid_total is not None:
            try:
                if int(paid_total) != int(order.amount):
                    logger.warning(
                        "wechat amount mismatch order=%s expected=%s got=%s",
                        order_no, order.amount, paid_total,
                    )
                    return None
            except (TypeError, ValueError):
                logger.warning("wechat amount unparseable order=%s got=%s", order_no, paid_total)
                return None

        # F3+BUG-02: 原子置 paid + 发放权益；发放失败回滚到 pending，渠道重试可自愈
        return self._mark_paid_and_provision(order_no, sync_data={**data, **parsed})

    def _mark_paid_and_provision(
        self, order_no: str, sync_data: Optional[dict] = None
    ) -> Optional[PaymentOrder]:
        """原子 pending→paid，随后发放权益。

        修复 BUG-02：原实现「先置 paid 后发权益」且发放异常时状态不可逆，
        渠道重试会因 status!=pending 直接 return None，权益永远不发放。
        现在发放失败时回滚订单到 pending（收入/权益均有 order_no 幂等去重，
        重放安全），并向上抛出异常让路由返回 5xx 触发渠道重试。
        """
        updated = (
            self.db.query(PaymentOrder)
            .filter(PaymentOrder.order_no == order_no, PaymentOrder.status == "pending")
            .update({PaymentOrder.status: "paid", PaymentOrder.paid_at: datetime.now(timezone.utc)})
        )
        self.db.commit()
        if updated == 0:
            return None
        order = self.db.query(PaymentOrder).filter(
            PaymentOrder.order_no == order_no
        ).first()
        try:
            self._record_revenue(order)
            self._provision_paid_order(order)
            if sync_data:
                self._sync_b2b_order_from_notify(sync_data)
        except Exception:
            self.db.rollback()
            logger.exception(
                "[BUG-02 fix] 发放权益失败，订单回滚 pending 等待渠道重试: order=%s",
                order_no,
            )
            reverted = (
                self.db.query(PaymentOrder)
                .filter(PaymentOrder.order_no == order_no, PaymentOrder.status == "paid")
                .update({PaymentOrder.status: "pending", PaymentOrder.paid_at: None})
            )
            self.db.commit()
            if reverted:
                logger.error("[BUG-02 fix] 已回滚订单 %s，渠道重试将重新走发放链路", order_no)
            raise
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

        # 读取订单用于金额校验（F2）；不在此处改状态，避免 TOCTOU 重复发放
        order = self.db.query(PaymentOrder).filter(
            PaymentOrder.order_no == order_no
        ).first()
        if not order:
            return None

        paid_yuan = data.get("total_amount") or data.get("receipt_amount")
        if paid_yuan is not None:
            try:
                paid_cents = int(round(float(paid_yuan) * 100))
            except (TypeError, ValueError):
                logger.warning("alipay amount unparseable order=%s got=%s", order_no, paid_yuan)
                return None
            if paid_cents != int(order.amount):
                logger.warning(
                    "alipay amount mismatch order=%s expected=%s got=%s",
                    order_no,
                    order.amount,
                    paid_cents,
                )
                return None

        # F3+BUG-02: 原子置 paid + 发放权益；发放失败回滚到 pending，渠道重试可自愈
        return self._mark_paid_and_provision(order_no, sync_data=data)

    # ------------------------------------------------------------------
    # mock-pay（仅 PAYMENT_ALLOW_MOCK=1；禁止当真实结算）
    # ------------------------------------------------------------------
    def mock_pay_order(self, order_id: str) -> Optional[PaymentOrder]:
        """Mark order paid only when mock explicitly allowed; never a real settlement path."""
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
        # W-20: sync B2B from subject-encoded business_order_id when present
        from app.services.b2b_deposit_payment_service import extract_business_order_id_from_subject
        b2b_id = extract_business_order_id_from_subject(order.subject)
        if b2b_id:
            self._sync_b2b_order_from_notify({
                "business_order_id": b2b_id,
                "out_trade_no": order.order_no,
                "mode": "mock",
            })
        return order

    def _sync_b2b_order_from_notify(self, data: dict) -> None:
        """_sync_b2b_order_from_notify。

        参数说明：
        :param self: 参数 self
        :param data: 参数 data
        :return: 返回处理结果。
        """
        from app.services.order_payment_sync_service import sync_b2b_from_payment_notify
        from app.services.b2b_deposit_payment_service import extract_business_order_id_from_subject
        payload = dict(data or {})
        if not payload.get("business_order_id"):
            order_no = str(payload.get("out_trade_no") or payload.get("order_no") or "")
            if order_no:
                po = self.db.query(PaymentOrder).filter(PaymentOrder.order_no == order_no).first()
                if po:
                    b2b = extract_business_order_id_from_subject(po.subject)
                    if b2b:
                        payload["business_order_id"] = b2b
        sync_b2b_from_payment_notify(self.db, payload)

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
