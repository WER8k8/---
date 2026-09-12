"""统一计量埋点与账单对账（总纲 §4.6-8 / §6.6 P4 / §7.6）

- emit*：7 类埋点动作，append-only 写入 meter_events（event_key 幂等去重）。
- aggregate_to_billing：周期汇总（Celery beat）——ai_generation 扣减 token_ledger；
  其余 6 类可计费动作写 finance_ledger 营收；aggregated_at 标记避免重复汇总。
- reconcile：meter_events 与 token_ledger / finance_ledger 对账，报告误差
  （P4 验收：7 类计量与账单对账误差 0）。
- 配额：ai_generation 走 plan_gate_service 判定套餐能力与 AI 额度。

红线 R3：计费复用既有四表（wallet/token_ledger/payment/finance_ledger），禁止重建；
本服务只写计量与两本账的追加流水，不新建任何计费账本。
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.finance_ledger import FinanceLedgerEntry
from app.models.meter import METER_TYPES, MeterEvent
from app.models.token_ledger import TokenLedgerEntry

# ai_generation 只扣 token（走 token_ledger）；其余 6 类按动作写 finance_ledger 营收
TOKEN_METER_TYPES = ("ai_generation",)
REVENUE_METER_TYPES = (
    "content_publish",
    "lead_generated",
    "rfq_created",
    "api_call",
    "export",
    "video_job",
)

# meter_type → finance_ledger.category
REVENUE_CATEGORY: dict[str, str] = {
    "content_publish": "content_publish",
    "lead_generated": "lead",
    "rfq_created": "rfq",
    "api_call": "api",
    "export": "export",
    "video_job": "video",
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MeterEventService:
    """计量服务：埋点 / 汇总 / 对账 / 配额。"""

    def __init__(self, db: Session):
        self.db = db

    # ---- 核心写入（append-only，event_key 幂等）----
    def emit(
        self,
        *,
        meter_type: str,
        tenant_id: Optional[str] = None,
        event_key: Optional[str] = None,
        quantity: int = 1,
        unit: str = "count",
        token_delta: int = 0,
        cost_cents: int = 0,
        currency: str = "CNY",
        source_ref_type: Optional[str] = None,
        source_ref_id: Optional[str] = None,
        model_name: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        occurred_at: Optional[datetime] = None,
    ) -> MeterEvent:
        """写入一条计量事件；event_key 重复时直接返回已存在事件（幂等，不覆盖）。"""
        if meter_type not in METER_TYPES:
            raise ValueError(
                f"非法埋点类型: {meter_type}，允许: {list(METER_TYPES)}"
            )
        if event_key:
            existing = (
                self.db.query(MeterEvent)
                .filter(MeterEvent.event_key == event_key)
                .first()
            )
            if existing:
                return existing
        event = MeterEvent(
            tenant_id=tenant_id,
            event_key=event_key,
            meter_type=meter_type,
            quantity=quantity,
            unit=unit,
            token_delta=token_delta,
            cost_cents=cost_cents,
            currency=currency,
            source_ref_type=source_ref_type,
            source_ref_id=source_ref_id,
            model_name=model_name,
            metadata_json=metadata or {},
            occurred_at=occurred_at or _utcnow(),
        )
        self.db.add(event)
        try:
            self.db.commit()
        except IntegrityError:
            # 并发重复 event_key：回滚并返回已存在事件
            self.db.rollback()
            if event_key:
                existing = (
                    self.db.query(MeterEvent)
                    .filter(MeterEvent.event_key == event_key)
                    .first()
                )
                if existing:
                    return existing
            raise
        self.db.refresh(event)
        return event

    # ---- 7 类埋点动作（§4.6-8）----
    def emit_ai_generation(
        self,
        *,
        tenant_id: Optional[str] = None,
        event_key: Optional[str] = None,
        token_delta: int = 0,
        cost_cents: int = 0,
        model_name: Optional[str] = None,
        source_ref_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> MeterEvent:
        return self.emit(
            meter_type="ai_generation", tenant_id=tenant_id, event_key=event_key,
            unit="call", token_delta=token_delta, cost_cents=cost_cents,
            source_ref_type="task", source_ref_id=source_ref_id,
            model_name=model_name, metadata=metadata,
        )

    def emit_content_publish(
        self,
        *,
        tenant_id: Optional[str] = None,
        event_key: Optional[str] = None,
        quantity: int = 1,
        cost_cents: int = 0,
        source_ref_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> MeterEvent:
        return self.emit(
            meter_type="content_publish", tenant_id=tenant_id, event_key=event_key,
            quantity=quantity, unit="publish", cost_cents=cost_cents,
            source_ref_type="content", source_ref_id=source_ref_id, metadata=metadata,
        )

    def emit_lead_generated(
        self,
        *,
        tenant_id: Optional[str] = None,
        event_key: Optional[str] = None,
        quantity: int = 1,
        cost_cents: int = 0,
        source_ref_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> MeterEvent:
        return self.emit(
            meter_type="lead_generated", tenant_id=tenant_id, event_key=event_key,
            quantity=quantity, unit="lead", cost_cents=cost_cents,
            source_ref_type="lead", source_ref_id=source_ref_id, metadata=metadata,
        )

    def emit_rfq_created(
        self,
        *,
        tenant_id: Optional[str] = None,
        event_key: Optional[str] = None,
        quantity: int = 1,
        cost_cents: int = 0,
        source_ref_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> MeterEvent:
        return self.emit(
            meter_type="rfq_created", tenant_id=tenant_id, event_key=event_key,
            quantity=quantity, unit="rfq", cost_cents=cost_cents,
            source_ref_type="rfq", source_ref_id=source_ref_id, metadata=metadata,
        )

    def emit_api_call(
        self,
        *,
        tenant_id: Optional[str] = None,
        event_key: Optional[str] = None,
        quantity: int = 1,
        cost_cents: int = 0,
        source_ref_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> MeterEvent:
        return self.emit(
            meter_type="api_call", tenant_id=tenant_id, event_key=event_key,
            quantity=quantity, unit="call", cost_cents=cost_cents,
            source_ref_type="api", source_ref_id=source_ref_id, metadata=metadata,
        )

    def emit_export(
        self,
        *,
        tenant_id: Optional[str] = None,
        event_key: Optional[str] = None,
        quantity: int = 1,
        cost_cents: int = 0,
        source_ref_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> MeterEvent:
        return self.emit(
            meter_type="export", tenant_id=tenant_id, event_key=event_key,
            quantity=quantity, unit="export", cost_cents=cost_cents,
            source_ref_type="export", source_ref_id=source_ref_id, metadata=metadata,
        )

    def emit_video_job(
        self,
        *,
        tenant_id: Optional[str] = None,
        event_key: Optional[str] = None,
        quantity: int = 1,
        cost_cents: int = 0,
        source_ref_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> MeterEvent:
        return self.emit(
            meter_type="video_job", tenant_id=tenant_id, event_key=event_key,
            quantity=quantity, unit="job", cost_cents=cost_cents,
            source_ref_type="video", source_ref_id=source_ref_id, metadata=metadata,
        )

    # ---- 周期汇总进既有计费账本（幂等）----
    def aggregate_to_billing(
        self,
        *,
        tenant_id: Optional[str] = None,
        meter_types: Optional[list[str]] = None,
        up_to: Optional[datetime] = None,
    ) -> dict[str, int]:
        """将未汇总（aggregated_at IS NULL）的计量事件并入既有计费账本。

        - ai_generation → token_ledger_entries 扣减（delta = -token_delta）
        - 其余可计费 → finance_ledger_entries 营收（amount_cents = cost_cents）
        返回 {token_events, token_delta, finance_events, finance_cents}。
        """
        query = self.db.query(MeterEvent).filter(MeterEvent.aggregated_at.is_(None))
        if tenant_id is not None:
            query = query.filter(MeterEvent.tenant_id == tenant_id)
        if meter_types:
            query = query.filter(MeterEvent.meter_type.in_(meter_types))
        if up_to:
            query = query.filter(MeterEvent.occurred_at <= up_to)
        events = query.order_by(MeterEvent.occurred_at.asc()).all()

        now = _utcnow()
        token_events = 0
        token_delta = 0
        finance_events = 0
        finance_cents = 0
        for ev in events:
            if ev.meter_type in TOKEN_METER_TYPES and ev.tenant_id is not None and ev.token_delta:
                self._append_token_deduction(ev)
                token_events += 1
                token_delta += ev.token_delta
            elif ev.meter_type in REVENUE_METER_TYPES and ev.cost_cents:
                self._append_finance_revenue(ev)
                finance_events += 1
                finance_cents += ev.cost_cents
            ev.aggregated_at = now
        self.db.commit()
        return {
            "token_events": token_events,
            "token_delta": token_delta,
            "finance_events": finance_events,
            "finance_cents": finance_cents,
        }

    def _append_token_deduction(self, ev: MeterEvent) -> None:
        last = (
            self.db.query(TokenLedgerEntry)
            .filter(TokenLedgerEntry.tenant_id == ev.tenant_id)
            .order_by(TokenLedgerEntry.created_at.desc())
            .first()
        )
        balance_after = (last.balance_after if last else 0) - ev.token_delta
        self.db.add(
            TokenLedgerEntry(
                tenant_id=ev.tenant_id,
                delta=-ev.token_delta,
                balance_after=balance_after,
                reason="meter_event",
                reference_id=str(ev.id),
                created_at=ev.occurred_at,
            )
        )

    def _append_finance_revenue(self, ev: MeterEvent) -> None:
        self.db.add(
            FinanceLedgerEntry(
                entry_type="revenue",
                category=REVENUE_CATEGORY.get(ev.meter_type, ev.meter_type),
                amount_cents=ev.cost_cents,
                tenant_id=ev.tenant_id,
                reference_id=str(ev.id),
                note=f"meter_event:{ev.meter_type}",
                recorded_at=ev.occurred_at,
            )
        )

    # ---- 对账（P4 验收：误差 0）----
    def reconcile(
        self,
        *,
        tenant_id: Optional[str] = None,
        window_start: Optional[datetime] = None,
        window_end: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """计量侧 vs 账本侧对账。返回差异与 error_free 结论。"""
        end = window_end or _utcnow()
        start = window_start or (end - timedelta(days=7))
        query = self.db.query(MeterEvent).filter(
            MeterEvent.occurred_at >= start,
            MeterEvent.occurred_at <= end,
        )
        if tenant_id is not None:
            query = query.filter(MeterEvent.tenant_id == tenant_id)
        events = query.all()

        token_metered = sum(
            e.token_delta for e in events if e.meter_type in TOKEN_METER_TYPES
        )
        revenue_metered = sum(
            e.cost_cents for e in events if e.meter_type in REVENUE_METER_TYPES
        )
        event_ids = [str(e.id) for e in events]

        token_ledgered = 0
        revenue_ledgered = 0
        if event_ids:
            token_ledgered = sum(
                r.delta
                for r in self.db.query(TokenLedgerEntry)
                .filter(TokenLedgerEntry.reference_id.in_(event_ids))
                .all()
            )
            revenue_ledgered = sum(
                r.amount_cents
                for r in self.db.query(FinanceLedgerEntry)
                .filter(FinanceLedgerEntry.reference_id.in_(event_ids))
                .all()
            )

        # token_ledger 扣减为负：计量侧(token_delta) + 账本侧(delta) = 0 即对齐
        token_diff = token_metered + token_ledgered
        revenue_diff = revenue_metered - revenue_ledgered
        pending = (
            self.db.query(MeterEvent)
            .filter(MeterEvent.aggregated_at.is_(None))
            .filter(MeterEvent.occurred_at >= start, MeterEvent.occurred_at <= end)
        )
        if tenant_id is not None:
            pending = pending.filter(MeterEvent.tenant_id == tenant_id)
        pending_count = pending.count()

        discrepancies: list[str] = []
        if token_diff != 0:
            discrepancies.append(
                f"ai_generation token 误差 {token_diff}（计量 {token_metered} / 账本 {token_ledgered}）"
            )
        if revenue_diff != 0:
            discrepancies.append(
                f"营收金额误差 {revenue_diff}（计量 {revenue_metered} / 账本 {revenue_ledgered}）"
            )
        if pending_count:
            discrepancies.append(f"尚有 {pending_count} 条计量事件未汇总进账本")

        # 对账不平必须主动告警（审计 P2：不能只把误差放进返回值等调用方发现）
        if discrepancies:
            import logging

            _reconcile_logger = logging.getLogger("uj.billing.reconcile")
            _reconcile_logger.error(
                "[对账告警] tenant=%s window=[%s, %s] token_diff=%s revenue_diff=%s "
                "pending=%s discrepancies=%s",
                tenant_id,
                start.isoformat(),
                end.isoformat(),
                token_diff,
                revenue_diff,
                pending_count,
                "; ".join(discrepancies),
            )

        return {
            "window_start": start.isoformat(),
            "window_end": end.isoformat(),
            "tenant_id": tenant_id,
            "ai_generation": {
                "metered_token_delta": token_metered,
                "ledgered_token_delta": token_ledgered,
                "difference": token_diff,
            },
            "revenue": {
                "metered_cost_cents": revenue_metered,
                "ledgered_amount_cents": revenue_ledgered,
                "difference": revenue_diff,
            },
            "pending_events": pending_count,
            "discrepancies": discrepancies,
            "error_free": not discrepancies,
        }

    # ---- 配额（走 plan_gate_service）----
    def evaluate_ai_quota(self, tenant) -> dict[str, Any]:
        """AI 配额判定：只读，路由到 plan_gate_service（套餐能力 + AI 额度）。"""
        from app.services.plan_gate_service import evaluate_ai_quota  # noqa: PLC0415

        return evaluate_ai_quota(tenant)

    def consume_ai_quota(self, tenant, quantity: int = 1) -> None:
        """消费 AI 配额（写入 tenant.ai_quota_used）。"""
        if tenant is None:
            return
        tenant.ai_quota_used = (tenant.ai_quota_used or 0) + quantity
        self.db.commit()


async def emit_ai_generation_best_effort(
    *,
    tenant_id: Optional[str] = None,
    token_delta: int = 0,
    cost_usd: float = 0.0,
    model_name: Optional[str] = None,
    source_ref_id: Optional[str] = None,
    event_key: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> bool:
    """旁路 ai_generation 埋点（轮23）：SessionLocal + asyncio.to_thread，异常全吞。

    供 Model Gateway 等无请求级 Session 的异步调用方使用（复用
    model_gateway/ledger.py 的旁路写入模式，故障绝不阻断主链路）。
    返回是否写入成功。注意：本路径计量经 meter_events 汇总进 token_ledger，
    与 model_call_ledger→token_ledger 聚合二选一启用，避免双重扣减。
    """
    def _write() -> bool:
        try:
            from app.core.database import SessionLocal  # noqa: PLC0415
        except Exception:  # noqa: BLE001
            return False
        try:
            with SessionLocal() as session:
                MeterEventService(session).emit_ai_generation(
                    tenant_id=tenant_id,
                    event_key=event_key,
                    token_delta=token_delta,
                    cost_cents=int(round((cost_usd or 0.0) * 100)),
                    model_name=model_name,
                    source_ref_id=source_ref_id,
                    metadata=metadata,
                )
                return True
        except Exception:  # noqa: BLE001
            return False

    return await asyncio.to_thread(_write)


# ---- 模块级薄封装（B-6：让 BillingExecutor 降级路径转正）----
# billing_executor 以 `from app.services.billing.meter_event import record_meter_event`
# 调用；此前无此函数 → 永久 ImportError → 走 metered_degraded 降级分支。
# 本封装内部复用 MeterEventService，把调用方的自由 event_type 安全映射到
# 合法 METER_TYPES，绝不抛 ValueError 阻断主链路。
_EVENT_TYPE_TO_METER_TYPE: dict[str, str] = {
    "ai_call": "ai_generation",
    "ai_generation": "ai_generation",
    "ai": "ai_generation",
    "content_publish": "content_publish",
    "publish": "content_publish",
    "lead_generated": "lead_generated",
    "lead": "lead_generated",
    "rfq_created": "rfq_created",
    "rfq": "rfq_created",
    "export": "export",
    "video_job": "video_job",
    "video": "video_job",
}


def record_meter_event(
    db: Session,
    *,
    tenant_id: Optional[str] = None,
    event_type: str = "api_call",
    amount: int = 1,
    cost_cents: int = 0,
    event_key: Optional[str] = None,
    model_name: Optional[str] = None,
    source_ref_id: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """模块级计量记录薄封装（供 Hermes BillingExecutor 调用，降级→真跑）。

    - 把调用方自由 event_type 映射到合法 METER_TYPES：AI 类走 ai_generation
      （token_delta=amount），其余（含 invoice/api 等）走 api_call（quantity=amount）。
    - 映射不到则兜底 api_call，绝不抛 ValueError。
    - 幂等：传入 event_key 时同键去重；未传则不强制生成，交由并发安全。
    - 失败回滚并返回带 degraded=True 的 dict（保留降级语义，不再触发 ImportError）。
    """
    etype = str(event_type or "api_call").strip().lower()
    if etype in _EVENT_TYPE_TO_METER_TYPE:
        meter_type = _EVENT_TYPE_TO_METER_TYPE[etype]
    elif etype in METER_TYPES:
        meter_type = etype
    else:
        # 未知类型兜底为 api_call 营收口径，不影响主链路
        meter_type = "api_call"

    qty = int(amount or 0)
    svc = MeterEventService(db)
    try:
        if meter_type == "ai_generation":
            ev = svc.emit(
                meter_type=meter_type,
                tenant_id=tenant_id,
                event_key=event_key,
                unit="call",
                token_delta=qty,
                cost_cents=cost_cents,
                source_ref_type="task",
                source_ref_id=source_ref_id,
                model_name=model_name,
                metadata=metadata,
            )
        else:
            ev = svc.emit(
                meter_type=meter_type,
                tenant_id=tenant_id,
                event_key=event_key,
                quantity=qty if qty else 1,
                unit="call",
                cost_cents=cost_cents,
                source_ref_type="api",
                source_ref_id=source_ref_id,
                model_name=model_name,
                metadata=metadata,
            )
        return {
            "event_id": str(ev.id) if getattr(ev, "id", None) else None,
            "meter_type": meter_type,
            "event_type": event_type,
            "quantity": qty,
            "status": "metered",
            "degraded": False,
        }
    except Exception:  # noqa: BLE001
        # 写入失败（含 event_key 冲突/DB 异常）：回滚并降级，不打挂主链路
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass
        return {
            "event_id": None,
            "meter_type": meter_type,
            "event_type": event_type,
            "quantity": qty,
            "status": "metered_degraded",
            "degraded": True,
        }
