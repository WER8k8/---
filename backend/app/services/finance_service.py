"""财务中台业务逻辑：成本归集、对账导出。"""

from __future__ import annotations

import csv
import io
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ai_config import AIUsageLog
from app.models.commission_settlement import AgentCommissionSettlement
from app.models.finance_ledger import FinanceLedgerEntry
from app.services.finance_honesty import revenue_ledger_conditions


def _parse_cost_cents(raw: str | None) -> int:
    """_parse_cost_cents。

    参数说明：
    :param raw: 参数 raw
    :return: 返回处理结果。
    """
    if not raw:
        return 0
    try:
        value = Decimal(str(raw).strip().replace(",", ""))
    except (InvalidOperation, ValueError):
        return 0
    if value < 0:
        return 0
    # cost 字段若为「元」则 *100；若已 >1000 视为分
    if value < 1000:
        return int(value * 100)
    return int(value)


class FinanceService:
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.db = db

    def sync_ai_model_costs(
        self,
        *,
        day: Optional[date] = None,
        dry_run: bool = False,
    ) -> dict:
        """将 ai_usage_logs 当日成本汇总写入 cost 台账（幂等 reference_id）。"""
        target = day or datetime.now(timezone.utc).date()
        start = datetime(target.year, target.month, target.day, tzinfo=timezone.utc)
        end = datetime(
            target.year,
            target.month,
            target.day,
            23,
            59,
            59,
            tzinfo=timezone.utc,
        )
        ref = f"ai_sync:{target.isoformat()}"
        existing = (
            self.db.query(FinanceLedgerEntry.id)
            .filter(
                FinanceLedgerEntry.reference_id == ref,
                FinanceLedgerEntry.entry_type == "cost",
            )
            .first()
        )
        if existing:
            return {
                "day": target.isoformat(),
                "reference_id": ref,
                "skipped": True,
                "reason": "already_synced",
            }

        rows = (
            self.db.query(AIUsageLog.cost)
            .filter(
                AIUsageLog.created_at >= start,
                AIUsageLog.created_at <= end,
                AIUsageLog.success.is_(True),
            )
            .all()
        )
        total_cents = sum(_parse_cost_cents(r.cost) for r in rows)
        if total_cents <= 0:
            return {
                "day": target.isoformat(),
                "reference_id": ref,
                "amount_cents": 0,
                "skipped": True,
                "reason": "no_cost_data",
            }

        if not dry_run:
            self.db.add(
                FinanceLedgerEntry(
                    entry_type="cost",
                    category="model_api",
                    amount_cents=total_cents,
                    reference_id=ref,
                    note=f"AI 用量成本归集 {target.isoformat()}",
                    recorded_at=start,
                )
            )
            self.db.commit()

        return {
            "day": target.isoformat(),
            "reference_id": ref,
            "amount_cents": total_cents,
            "log_rows": len(rows),
            "dry_run": dry_run,
            "skipped": False,
        }

    def revenue_this_month_cents(self) -> int:
        """revenue_this_month_cents。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        now = datetime.now(timezone.utc)
        month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        cents = (
            self.db.query(func.coalesce(func.sum(FinanceLedgerEntry.amount_cents), 0))
            .filter(
                *revenue_ledger_conditions(self.db),
                FinanceLedgerEntry.recorded_at >= month_start,
            )
            .scalar()
        )
        return int(cents or 0)

    def revenue_by_day(self, *, days: int = 30) -> dict[str, int]:
        """按日实收（分），仅真实 revenue 台账。"""
        since = datetime.now(timezone.utc) - timedelta(days=max(1, days))
        rows = (
            self.db.query(
                func.date(FinanceLedgerEntry.recorded_at),
                func.coalesce(func.sum(FinanceLedgerEntry.amount_cents), 0),
            )
            .filter(
                *revenue_ledger_conditions(self.db),
                FinanceLedgerEntry.recorded_at >= since,
            )
            .group_by(func.date(FinanceLedgerEntry.recorded_at))
            .all()
        )
        out: dict[str, int] = {}
        for day_val, amt in rows:
            if day_val is None:
                continue
            key = str(day_val)[:10]
            out[key] = int(amt or 0)
        return out

    def profit_summary(self) -> dict:
        """profit_summary。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        revenue = (
            self.db.query(func.coalesce(func.sum(FinanceLedgerEntry.amount_cents), 0))
            .filter(*revenue_ledger_conditions(self.db))
            .scalar()
        )
        cost = (
            self.db.query(func.coalesce(func.sum(FinanceLedgerEntry.amount_cents), 0))
            .filter(FinanceLedgerEntry.entry_type == "cost")
            .scalar()
        )
        commission_settled = (
            self.db.query(
                func.coalesce(func.sum(AgentCommissionSettlement.commission_cents), 0)
            )
            .filter(AgentCommissionSettlement.status == "settled")
            .scalar()
        )
        commission_pending = (
            self.db.query(
                func.coalesce(func.sum(AgentCommissionSettlement.commission_cents), 0)
            )
            .filter(AgentCommissionSettlement.status == "pending")
            .scalar()
        )
        rev, cst = int(revenue or 0), int(cost or 0)
        settled = int(commission_settled or 0)
        pending = int(commission_pending or 0)
        gross = rev - cst
        return {
            "revenue_cents": rev,
            "cost_cents": cst,
            "profit_cents": gross,
            "commission_settled_cents": settled,
            "commission_pending_cents": pending,
            "net_profit_cents": gross - settled,
        }

    def revenue_by_tenant(self, limit: int = 10) -> list[dict]:
        """revenue_by_tenant。

        参数说明：
        :param self: 参数 self
        :param limit: 参数 limit
        :return: 返回处理结果。
        """
        rows = (
            self.db.query(
                FinanceLedgerEntry.tenant_id,
                func.coalesce(func.sum(FinanceLedgerEntry.amount_cents), 0),
            )
            .filter(
                *revenue_ledger_conditions(self.db),
                FinanceLedgerEntry.tenant_id.isnot(None),
            )
            .group_by(FinanceLedgerEntry.tenant_id)
            .order_by(func.sum(FinanceLedgerEntry.amount_cents).desc())
            .limit(limit)
            .all()
        )
        return [
            {"tenant_id": tid, "revenue_cents": int(amt or 0)}
            for tid, amt in rows
            if tid
        ]

    def validate_import_csv(self, csv_text: str) -> dict:
        """P1 财务：对账 CSV 导入预检（不写库）。"""
        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        required = {"entry_type", "category", "amount_cents"}
        errors: list[str] = []
        preview: list[dict] = []
        rows = list(reader)
        if not rows:
            return {"ok": False, "errors": ["CSV 无数据行"], "preview": [], "row_count": 0}
        for i, row in enumerate(rows, start=2):
            if not required.issubset(row.keys()):
                errors.append(f"第 {i} 行缺少列：需要 {sorted(required)}")
                break
            et = (row.get("entry_type") or "").strip().lower()
            if et not in ("revenue", "cost"):
                errors.append(f"第 {i} 行 entry_type 无效：{et}")
            try:
                cents = int((row.get("amount_cents") or "0").strip())
                if cents <= 0:
                    errors.append(f"第 {i} 行 amount_cents 须为正整数")
            except ValueError:
                errors.append(f"第 {i} 行 amount_cents 非数字")
            if len(preview) < 5:
                preview.append(
                    {
                        "line": i,
                        "entry_type": et,
                        "category": (row.get("category") or "")[:40],
                        "amount_cents": row.get("amount_cents"),
                    }
                )
        return {
            "ok": len(errors) == 0,
            "errors": errors[:20],
            "preview": preview,
            "row_count": len(rows),
        }

    def commit_import_csv(self, csv_text: str, *, dry_run: bool = False) -> dict:
        """对账 CSV 写入台账（reference_id 幂等跳过）。"""
        import uuid as _uuid
        report = self.validate_import_csv(csv_text)
        if not report.get("ok"):
            return {
                "ok": False,
                "inserted": 0,
                "skipped": 0,
                "errors": report.get("errors", []),
                "row_count": report.get("row_count", 0),
            }
        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        inserted = 0
        skipped = 0
        for row in reader:
            ref = (row.get("reference_id") or "").strip()
            if ref:
                exists = (
                    self.db.query(FinanceLedgerEntry)
                    .filter(FinanceLedgerEntry.reference_id == ref)
                    .first()
                )
                if exists:
                    skipped += 1
                    continue
            if dry_run:
                continue
            et = (row.get("entry_type") or "").strip().lower()
            cents = int((row.get("amount_cents") or "0").strip())
            recorded_raw = (row.get("recorded_at") or "").strip()
            recorded_at = datetime.now(timezone.utc)
            if recorded_raw:
                try:
                    recorded_at = datetime.fromisoformat(
                        recorded_raw.replace("Z", "+00:00")
                    )
                except ValueError:
                    pass
            tenant_raw = (row.get("tenant_id") or "").strip()
            self.db.add(
                FinanceLedgerEntry(
                    id=str(_uuid.uuid4()),
                    entry_type=et,
                    category=(row.get("category") or "import")[:50],
                    amount_cents=cents,
                    tenant_id=tenant_raw or None,
                    reference_id=ref or None,
                    note=(row.get("note") or "")[:2000] or None,
                    recorded_at=recorded_at,
                )
            )
            inserted += 1
        if not dry_run and inserted:
            self.db.commit()
        return {
            "ok": True,
            "inserted": inserted,
            "skipped": skipped,
            "dry_run": dry_run,
            "row_count": report.get("row_count", 0),
        }

    def reconciliation_template_csv(self) -> str:
        """财务对账 Excel/CSV 导入模板（表头行）。"""
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(
            [
                "entry_type",
                "category",
                "amount_cents",
                "tenant_id",
                "reference_id",
                "note",
                "recorded_at",
            ]
        )
        writer.writerow(
            ["revenue", "subscription", "9900", "", "ORD-EXAMPLE", "示例营收", ""]
        )
        writer.writerow(
            ["cost", "model_api", "1200", "", "ai_sync:2026-01-01", "示例成本", ""]
        )
        return buf.getvalue()

    def export_ledger_csv(
        self,
        *,
        entry_type: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> str:
        """export_ledger_csv。

        参数说明：
        :param self: 参数 self
        :param entry_type: 参数 entry_type
        :param from_date: 参数 from_date
        :param to_date: 参数 to_date
        :return: 返回处理结果。
        """
        q = self.db.query(FinanceLedgerEntry)
        if entry_type:
            q = q.filter(FinanceLedgerEntry.entry_type == entry_type)
        if from_date:
            q = q.filter(FinanceLedgerEntry.recorded_at >= from_date)
        if to_date:
            q = q.filter(FinanceLedgerEntry.recorded_at <= to_date)
        rows = q.order_by(FinanceLedgerEntry.recorded_at.desc()).all()
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(
            [
                "id",
                "entry_type",
                "category",
                "amount_cents",
                "tenant_id",
                "reference_id",
                "note",
                "recorded_at",
            ]
        )
        for r in rows:
            writer.writerow(
                [
                    r.id,
                    r.entry_type,
                    r.category,
                    r.amount_cents,
                    r.tenant_id or "",
                    r.reference_id or "",
                    (r.note or "").replace("\n", " "),
                    r.recorded_at.isoformat() if r.recorded_at else "",
                ]
            )
        return buf.getvalue()
