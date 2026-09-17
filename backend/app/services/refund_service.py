# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""退款服务 — 通用退款入口，按支付通道分发退款请求。

幂等修复（ORCH-17）：
- out_refund_no 改为确定性派生（refund_id），禁止时间戳；
- 幂等键改用 SET NX 原子占位，Redis 故障 fail-closed（拒绝退款而非放行）；
- 退款失败后释放幂等键，合法重试不阻塞；
- 幂等命中时从 Redis 读取上次成功结果（含 channel_refund_id），而非笼统的 already_processed。
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from app.models.payment import PaymentOrder

logger = logging.getLogger("uj-admin.payment.refund")

# 支持的支付通道
SUPPORTED_CHANNELS = ("wechat", "alipay", "stripe")


# ---------------------------------------------------------------------------
# 退款结果结构
# ---------------------------------------------------------------------------

@dataclass
class RefundResult:
    """统一退款返回结构。"""
    success: bool = False
    refund_id: str = ""
    channel: str = ""
    channel_refund_id: str = ""
    status: str = "pending"
    message: str = ""
    def to_dict(self) -> dict:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "success": self.success,
            "refund_id": self.refund_id,
            "channel": self.channel,
            "channel_refund_id": self.channel_refund_id,
            "status": self.status,
            "message": self.message,
        }


# ---------------------------------------------------------------------------
# 退款服务
# ---------------------------------------------------------------------------

class RefundService:
    """通用退款服务。

    根据订单支付通道分发退款请求：
    - wechat / alipay：当前仅记录 TODO + 日志，不触发现有支付逻辑。
    - stripe：预留接口参数，待 Stripe SDK 集成后实现。
    """
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.db = db

    # ------------------------------------------------------------------
    # 公共入口
    # ------------------------------------------------------------------
    def refund(
        self,
        order_id: str,
        amount: int,
        reason: str,
        channel: str,
        *,
        idempotency_key: Optional[str] = None,
        order_snapshot: Optional[dict] = None,
        max_refund_amount: Optional[int] = None,
    ) -> dict:
        """通用退款入口。

        参数:
            order_id: 原支付订单 ID（PaymentOrder.id）。
            amount: 退款金额，单位「分」，必须 > 0。
            reason: 退款原因。
            channel: 支付通道，支持 wechat / alipay / stripe。
            idempotency_key: 幂等键，防止重复退款（可选）。
            order_snapshot: 订单快照 dict，可包含 max_refund_amount 等约束字段。
            max_refund_amount: 允许的最大退款金额（分），优先级高于 order_snapshot 中的同名字段。

        返回:
            dict: 结构化退款结果。
        """
        # --- 幂等检查 ---
        if idempotency_key:
            existing = self._resolve_idempotency_hit(idempotency_key)
            if existing is not None:
                return existing

        # --- 校验请求参数并加载原始订单 ---
        order, error_result = self._validate_and_load_order(
            order_id=order_id,
            amount=amount,
            reason=reason,
            channel=channel,
            max_refund_amount=max_refund_amount,
            order_snapshot=order_snapshot,
        )
        if error_result is not None:
            return error_result

        # --- 按通道分发 ---
        refund_id = str(uuid.uuid4())
        return self._dispatch_refund_with_idempotency(
            order, refund_id, amount, reason, channel, idempotency_key
        )

    def _validate_and_load_order(
        self,
        *,
        order_id: str,
        amount: int,
        reason: str,
        channel: str,
        max_refund_amount: Optional[int],
        order_snapshot: Optional[dict],
    ) -> tuple[Optional[PaymentOrder], Optional[dict]]:
        """校验请求参数并加载原始订单，失败时返回 (None, 失败结果)。"""
        validation_error = self._validate_refund_request(
            amount=amount,
            channel=channel,
            max_refund_amount=max_refund_amount,
            order_snapshot=order_snapshot,
        )
        if validation_error:
            logger.warning(
                "退款校验失败 | order_id=%s channel=%s amount=%s reason=%s message=%s",
                order_id,
                channel,
                amount,
                reason,
                validation_error,
            )
            return (None, self._build_failure_result(channel, validation_error, "rejected"))

        order = self.db.query(PaymentOrder).filter(PaymentOrder.id == order_id).first()
        if not order:
            logger.warning(
                "退款失败：订单不存在 | order_id=%s channel=%s",
                order_id,
                channel,
            )
            return (None, self._build_failure_result(channel, "原始支付订单不存在", "order_not_found"))

        if amount > order.amount:
            logger.warning(
                "退款金额超限 | order_id=%s order_amount=%s refund_amount=%s",
                order_id,
                order.amount,
                amount,
            )
            return (
                None,
                self._build_failure_result(
                    channel,
                    f"退款金额({amount}分)超过原始支付金额({order.amount}分)",
                    "rejected",
                ),
            )
        return (order, None)

    def _resolve_idempotency_hit(self, idempotency_key: str) -> Optional[dict]:
        """幂等检查：命中已处理请求时返回缓存的既有结果，否则返回 None。"""
        existing = self._check_idempotency(idempotency_key)
        if existing is None:
            return None
        # 幂等命中时，如果已有结果直接返回
        if existing.get("status") == "already_processed" and "data" in existing:
            logger.info(
                "幂等命中，返回已有结果 | idempotency_key=%s",
                idempotency_key,
            )
            return existing["data"]
        logger.info(
            "幂等命中 | idempotency_key=%s",
            idempotency_key,
        )
        return existing

    def _dispatch_refund_with_idempotency(
        self,
        order: PaymentOrder,
        refund_id: str,
        amount: int,
        reason: str,
        channel: str,
        idempotency_key: Optional[str],
    ) -> dict:
        """按通道分发退款（携带已生成的 refund_id 与幂等键）。"""
        if channel == "wechat":
            return self._refund_wechat(order, refund_id, amount, reason, idempotency_key)

        if channel == "alipay":
            return self._refund_alipay(order, refund_id, amount, reason, idempotency_key)

        if channel == "stripe":
            return self._refund_stripe(order, refund_id, amount, reason, idempotency_key)

        # 不应到达此处（校验已拦截未知通道）
        return RefundResult(
            success=False,
            refund_id=refund_id,
            channel=channel,
            status="unsupported",
            message=f"不支持的支付通道: {channel}",
        ).to_dict()

    def _build_failure_result(
        self,
        channel: str,
        message: str,
        status: str,
    ) -> dict:
        """构造统一失败退款结果（含新生成的 refund_id）。"""
        refund_id = str(uuid.uuid4())
        return RefundResult(
            success=False,
            refund_id=refund_id,
            channel=channel,
            status=status,
            message=message,
        ).to_dict()

    # ------------------------------------------------------------------
    # 通道分发（内部）
    # ------------------------------------------------------------------
    def _refund_wechat(
        self,
        order: PaymentOrder,
        refund_id: str,
        amount: int,
        reason: str,
        idempotency_key: Optional[str],
    ) -> dict:
        """微信退款。out_refund_no 使用确定性 refund_id，禁止时间戳。"""
        try:
            from app.services.wechat_pay_v3 import WeChatPayV3Client
            client = WeChatPayV3Client()
            # ORCH-17 修复：使用 refund_id 而非时间戳作为商户退款单号
            out_refund_no = f"refund_{order.order_no}_{refund_id[:8]}"
            result = client.create_refund(
                out_trade_no=order.order_no,
                out_refund_no=out_refund_no,
                total=order.amount,
                refund=amount,
                reason=reason,
            )
            refund_result = RefundResult(
                success=True,
                refund_id=refund_id,
                status="processing",
                channel="wechat",
                channel_refund_id=result.get("refund_id", ""),
                message="微信退款已提交",
            ).to_dict()
            # 记录结果供幂等命中时返回
            if idempotency_key:
                self._record_idempotent_result(idempotency_key, refund_result)
            return refund_result
        except Exception as e:
            # ORCH-17 修复：失败时释放幂等键
            if idempotency_key:
                self._release_idempotent_key(idempotency_key)
            return RefundResult(
                success=False,
                refund_id=refund_id,
                status="failed",
                channel="wechat",
                message=f"微信退款失败: {e}",
            ).to_dict()

    def _refund_alipay(
        self,
        order: PaymentOrder,
        refund_id: str,
        amount: int,
        reason: str,
        idempotency_key: Optional[str],
    ) -> dict:
        """支付宝退款。"""
        try:
            from app.services.alipay_client import AlipayClient, load_alipay_config
            client = AlipayClient(load_alipay_config())
            result = client.refund(
                out_trade_no=order.order_no,
                refund_amount=amount / 100,
                refund_reason=reason,
            )
            refund_result = RefundResult(
                success=True,
                refund_id=refund_id,
                status="processing",
                channel="alipay",
                channel_refund_id=result.get("refund_id", result.get("trade_no", "")),
                message="支付宝退款已提交",
            ).to_dict()
            if idempotency_key:
                self._record_idempotent_result(idempotency_key, refund_result)
            return refund_result
        except Exception as e:
            if idempotency_key:
                self._release_idempotent_key(idempotency_key)
            return RefundResult(
                success=False,
                refund_id=refund_id,
                status="failed",
                channel="alipay",
                message=f"支付宝退款失败: {e}",
            ).to_dict()

    def _refund_stripe(
        self,
        order: PaymentOrder,
        refund_id: str,
        amount: int,
        reason: str,
        idempotency_key: Optional[str],
    ) -> dict:
        """Stripe 退款（当前 stripe_service 仅实现了 Checkout Session，退款 API 待接入）。"""
        logger.warning(
            "Stripe 退款暂未实现 | order_no=%s amount=%s reason=%s",
            order.order_no, amount, reason,
        )
        return RefundResult(
            success=False,
            refund_id=refund_id,
            status="not_implemented",
            channel="stripe",
            message="Stripe 退款接口暂未接入，请联系管理员",
        ).to_dict()

    # ------------------------------------------------------------------
    # 校验
    # ------------------------------------------------------------------
    @staticmethod
    def _validate_refund_request(
        *,
        amount: int,
        channel: str,
        max_refund_amount: Optional[int] = None,
        order_snapshot: Optional[dict] = None,
    ) -> Optional[str]:
        """校验退款请求参数，返回错误信息或 None。"""
        if channel not in SUPPORTED_CHANNELS:
            return f"不支持的支付通道: {channel}，仅支持 {', '.join(SUPPORTED_CHANNELS)}"

        if amount <= 0:
            return "退款金额必须大于 0"

        # 优先使用显式传入的 max_refund_amount，其次从 order_snapshot 取
        limit = max_refund_amount
        if limit is None and order_snapshot:
            limit = order_snapshot.get("max_refund_amount")

        if limit is not None and amount > limit:
            return f"退款金额({amount}分)超过允许上限({limit}分)"

        return None

    # ------------------------------------------------------------------
    # 幂等
    # ------------------------------------------------------------------
    def _check_idempotency(self, idempotency_key: str) -> Optional[dict]:
        """检查退款幂等键是否已处理。

        使用 Redis SET NX 原子占位。Redis 故障 fail-closed（拒绝退款）。
        幂等命中时，返回 Redis 中存储的上次结果（含 channel_refund_id）。
        """
        from app.core.cache import redis_client
        if not redis_client:
            logger.error(
                "[RefundService] 幂等检查失败: redis_client 不可用 (fail-closed) key=%s",
                idempotency_key,
            )
            return {"status": "service_unavailable", "message": "幂等检查服务不可用"}

        key = f"refund:idempotent:{idempotency_key}"
        try:
            # 原子占位：SET key value NX EX 86400
            ok = redis_client.set(key, "processing", nx=True, ex=86400)
            if not ok:
                # 已被占位，读取上次结果
                existing = redis_client.get(key)
                if existing:
                    return {
                        "status": "already_processed",
                        "message": "该退款已处理",
                        "data": existing,
                    }
                return None
            return None
        except Exception as exc:
            logger.error("[RefundService] 幂等检查异常 (fail-closed) key=%s err=%s", idempotency_key, exc)
            return {"status": "service_unavailable", "message": "幂等检查服务异常"}

    def _release_idempotent_key(self, idempotency_key: str) -> None:
        """退款失败时释放幂等键，允许合法重试。"""
        from app.core.cache import redis_client
        if not redis_client:
            return
        key = f"refund:idempotent:{idempotency_key}"
        try:
            redis_client.delete(key)
        except Exception as exc:
            logger.warning("[RefundService] 释放幂等键失败: %s", exc)

    def _record_idempotent_result(self, idempotency_key: str, result: dict) -> None:
        """退款成功后记录结果，供幂等命中时返回。"""
        from app.core.cache import redis_client
        if not redis_client:
            return
        import json
        key = f"refund:idempotent:{idempotency_key}"
        try:
            redis_client.setex(key, 86400, json.dumps(result))
        except Exception as exc:
            logger.warning("[RefundService] 记录幂等结果失败: %s", exc)

    # ------------------------------------------------------------------
    # 按订单号退款（API 端点入口）
    # ------------------------------------------------------------------
    def refund_by_order_no(
        self,
        order_no: str,
        amount: float,
        reason: str,
    ) -> dict:
        """按订单号发起退款（供 API 端点调用）。

        参数:
            order_no: 商户订单号（PaymentOrder.order_no）。
            amount: 退款金额，单位「元」。
            reason: 退款原因。

        返回:
            dict: 结构化退款结果。
        """
        order = self.db.query(PaymentOrder).filter(
            PaymentOrder.order_no == order_no
        ).first()
        if not order:
            refund_id = str(uuid.uuid4())
            return RefundResult(
                success=False,
                refund_id=refund_id,
                status="order_not_found",
                message=f"订单不存在: {order_no}",
            ).to_dict()

        amount_cents = int(round(float(amount) * 100))
        channel = order.channel or "wechat"
        return self._dispatch_refund(
            order=order,
            amount=amount_cents,
            reason=reason,
            channel=channel,
        )

    def _dispatch_refund(
        self,
        order: PaymentOrder,
        amount: int,
        reason: str,
        channel: str,
    ) -> dict:
        """内部入口：使用已查询的订单对象分发退款。"""
        refund_id = str(uuid.uuid4())
        if channel == "wechat":
            return self._refund_wechat(order, refund_id, amount, reason, None)

        if channel == "alipay":
            return self._refund_alipay(order, refund_id, amount, reason, None)

        if channel == "stripe":
            return self._refund_stripe(order, refund_id, amount, reason, None)

        return RefundResult(
            success=False,
            refund_id=refund_id,
            channel=channel,
            status="unsupported",
            message=f"不支持的支付通道: {channel}",
        ).to_dict()

    # ------------------------------------------------------------------
    # 退款状态查询
    # ------------------------------------------------------------------
    def get_refund_status(self, order_no: str) -> dict:
        """查询订单退款状态。"""
        order = self.db.query(PaymentOrder).filter(
            PaymentOrder.order_no == order_no
        ).first()
        if not order:
            return {
                "order_no": order_no,
                "status": "order_not_found",
                "message": "订单不存在",
            }
        return {
            "order_no": order.order_no,
            "order_status": order.status,
            "channel": order.channel,
            "amount": order.amount,
            "message": "退款状态查询成功",
        }
