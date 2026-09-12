"""成本记账（总纲 §4.6）：每次 LLM 调用写 model_call_ledger，可汇总至 token_ledger。

设计原则：
- 复用既有数据库 SessionLocal（同步），在 asyncio.to_thread 中写入，避免阻塞事件循环。
- 任何异常都被吞掉并记录 warning，**绝不中断主链路**（总纲 禁止假交付：仅旁路记录）。
- 明细表 model_call_ledger 由迁移 095 建立；token_ledger_entries 为既有余额账本，
  聚合由 aggregate_to_token_ledger() 提供（供 086 MeterEvent 调用）。
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import text as sa_text


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _coerce_dt(value: Any) -> datetime:
    """raw SQL 读回的时间做类型强制（SQLite 驱动返回字符串；PG 返回 datetime）。"""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass
    return _now()


class CostLedger:
    """model_call_ledger 写入器（同步 session，最佳努力）。"""

    def record(self, entry: Dict[str, Any]) -> None:
        """同步写一条调用明细；异常吞掉，不影响主链路。"""
        try:
            from app.core.database import SessionLocal  # noqa: PLC0415
        except Exception:
            return
        try:
            with SessionLocal() as session:
                session.execute(
                    sa_text(
                        """
                        INSERT INTO model_call_ledger
                          (id, tenant_id, task_id, provider, model_name, capability_tag,
                           prompt_tokens, completion_tokens, total_tokens, cost_usd,
                           latency_ms, status, error_message, called_at, request_id, metadata_json)
                        VALUES
                          (:id, :tenant_id, :task_id, :provider, :model_name, :capability_tag,
                           :prompt_tokens, :completion_tokens, :total_tokens, :cost_usd,
                           :latency_ms, :status, :error_message, :called_at, :request_id, :metadata_json)
                        """
                    ),
                    entry,
                )
                session.commit()
        except Exception as exc:  # noqa: BLE001
            try:
                from app.core.logging import logger  # noqa: PLC0415
                logger.warning("model_call_ledger 写入失败（已忽略，不影响主链路）: %s", exc)
            except Exception:
                pass

    async def record_async(self, entry: Dict[str, Any]) -> None:
        await asyncio.to_thread(self.record, entry)

    def build_entry(
        self,
        *,
        tenant_id: Optional[str] = None,
        task_id: Optional[str] = None,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        capability_tag: Optional[str] = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        cost_usd: float = 0.0,
        latency_ms: Optional[int] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "task_id": task_id,
            "provider": provider,
            "model_name": model_name,
            "capability_tag": capability_tag,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cost_usd": cost_usd,
            "latency_ms": latency_ms,
            "status": status,
            "error_message": error_message,
            "called_at": _now(),
            "request_id": request_id,
            "metadata_json": json.dumps(metadata or {}, ensure_ascii=False),
        }


def aggregate_to_token_ledger(tenant_id: Optional[str] = None) -> int:
    """将 model_call_ledger 中尚未汇总且成功的明细，追加为 token_ledger_entries 的扣减流水。

    幂等：以 model_call_ledger.id 作为 token_ledger_entries.reference_id 去重；
    仅当 tenant_id 非空时聚合（token_ledger_entries.tenant_id NOT NULL）。
    返回本次新增的流水条数；失败时返回 0（不抛，供 086 MeterEvent 周期调用）。

    双记账防护（轮24 决策落地）：meter_events 路径（TASK_CONTROL_ENABLED，gateway
    ai_generation 埋点→小时汇总）与 本函数（model_call_ledger→token_ledger）都会向
    token_ledger 扣减，同时启用会双重扣减。默认本函数停用（返回 0）；确要切换记账
    主路径时，先关 TASK_CONTROL_ENABLED 再显式开 MODEL_CALL_LEDGER_AGGREGATE_ENABLED。
    """
    try:
        from app.core.config import settings  # noqa: PLC0415

        if not getattr(settings, "MODEL_CALL_LEDGER_AGGREGATE_ENABLED", False):
            return 0
    except Exception:  # noqa: BLE001
        return 0
    if not tenant_id:
        return 0
    try:
        from app.core.database import SessionLocal  # noqa: PLC0415
        from app.models.token_ledger import TokenLedgerEntry  # noqa: PLC0415
    except Exception:
        return 0
    try:
        with SessionLocal() as session:
            pending = session.execute(
                sa_text(
                    """
                    SELECT mcl.id AS cid, mcl.total_tokens AS tok, mcl.called_at AS ts
                    FROM model_call_ledger mcl
                    WHERE mcl.status = 'success'
                      AND mcl.tenant_id = :tid
                      AND NOT EXISTS (
                        SELECT 1 FROM token_ledger_entries tl
                        WHERE tl.reference_id = mcl.id
                      )
                    ORDER BY mcl.called_at ASC
                    """
                ),
                {"tid": tenant_id},
            ).fetchall()
            count = 0
            for row in pending:
                cid, tok, ts = row
                last = (
                    session.query(TokenLedgerEntry)
                    .filter(TokenLedgerEntry.tenant_id == tenant_id)
                    .order_by(TokenLedgerEntry.created_at.desc())
                    .first()
                )
                balance_after = (last.balance_after if last else 0) - (tok or 0)
                session.add(
                    TokenLedgerEntry(
                        tenant_id=tenant_id,
                        delta=-(tok or 0),
                        balance_after=balance_after,
                        reason="model_call",
                        reference_id=cid,
                        created_at=_coerce_dt(ts),
                    )
                )
                count += 1
            session.commit()
            return count
    except Exception:  # noqa: BLE001
        return 0


# 模块级便捷实例
ledger = CostLedger()
