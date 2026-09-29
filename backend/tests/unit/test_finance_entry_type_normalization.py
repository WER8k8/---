# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""R-4 · finance_ledger_entries.entry_type 读侧归一配对反证测试。

背景：种子历史写入 income/expense 与标准词表 {revenue, cost} 漂移，营收/成本
统计读不到任何行。裁定 R-4 = 读侧归一（IN 词表）+ 数据订正脚本。

配对反证（缺任一侧 = 空真）：
- 正向：income/expense 脏行必须能被营收/成本统计读到（止血生效）；
- 负向：mock_pay 类目仍被 revenue_ledger_conditions 排除；cost 不混入营收；
- 入参归一：export/list 的 entry_type 参数 income→revenue、expense→cost；
- 写侧冻结：Pydantic LedgerCreate 仍拒 income/expense（不得写侧放开）；
- 回归：export_ledger_csv 支持 tenant_id 过滤（修复 export/excel-report TypeError）。
"""
from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from app.models.finance_ledger import (
    ENTRY_TYPE_COST,
    ENTRY_TYPE_REVENUE,
    FinanceLedgerEntry,
    normalize_entry_type,
)
from app.services.finance_honesty import revenue_ledger_conditions
from app.services.finance_service import FinanceService

TENANT = "4b222222-2222-4222-8222-222222222222"


def _add_entry(db, *, entry_type: str, category: str, amount: int, tenant_id=TENANT,
               reference_id: str | None = None) -> FinanceLedgerEntry:
    row = FinanceLedgerEntry(
        entry_type=entry_type,
        category=category,
        amount_cents=amount,
        tenant_id=tenant_id,
        reference_id=reference_id,
        note="r4-test",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@pytest.fixture
def clean_ledger(db_session):
    """登记并清理本测试写入的台账行（测试库非现网，只清自己的痕迹）。"""
    ids: list[str] = []

    def _register(row: FinanceLedgerEntry) -> FinanceLedgerEntry:
        ids.append(str(row.id))
        return row

    yield _register
    try:
        db_session.query(FinanceLedgerEntry).filter(
            FinanceLedgerEntry.id.in_(ids)
        ).delete(synchronize_session=False)
        db_session.commit()
    except Exception:  # noqa: BLE001
        db_session.rollback()


class TestNormalizeEntryType:
    def test_dirty_words_map_to_canonical(self):
        assert normalize_entry_type("income") == "revenue"
        assert normalize_entry_type("expense") == "cost"

    def test_canonical_and_unknown_pass_through(self):
        assert normalize_entry_type("revenue") == "revenue"
        assert normalize_entry_type("cost") == "cost"
        assert normalize_entry_type("  Revenue ") == "revenue"
        assert normalize_entry_type("weird") == "weird"
        assert normalize_entry_type(None) in ("", None)

    def test_vocab_tuples(self):
        assert ENTRY_TYPE_REVENUE == ("revenue", "income")
        assert ENTRY_TYPE_COST == ("cost", "expense")


class TestReadSideHealing:
    def test_revenue_stats_see_income_rows(self, db_session, clean_ledger):
        clean_ledger(_add_entry(db_session, entry_type="revenue", category="subscription", amount=10000))
        clean_ledger(_add_entry(db_session, entry_type="income", category="subscription", amount=20000))
        q = db_session.query(FinanceLedgerEntry).filter(*revenue_ledger_conditions(db_session))
        types = {r.entry_type for r in q.all()}
        assert types == {"revenue", "income"}, "读侧归一后营收统计必须能读到 income 脏行"

    def test_revenue_stats_exclude_cost_and_mock(self, db_session, clean_ledger):
        clean_ledger(_add_entry(db_session, entry_type="income", category="subscription", amount=30000))
        clean_ledger(_add_entry(db_session, entry_type="cost", category="llm_api_cogs", amount=100))
        clean_ledger(_add_entry(db_session, entry_type="revenue", category="mock_pay", amount=999))
        rows = (
            db_session.query(FinanceLedgerEntry)
            .filter(*revenue_ledger_conditions(db_session))
            .all()
        )
        assert {r.entry_type for r in rows} == {"income"}
        assert all(r.category != "mock_pay" for r in rows), "mock_pay 必须仍被排除"

    def test_cost_stats_see_expense_rows(self, db_session, clean_ledger):
        clean_ledger(_add_entry(db_session, entry_type="expense", category="llm_api_cogs", amount=500))
        rows = (
            db_session.query(FinanceLedgerEntry)
            .filter(FinanceLedgerEntry.entry_type.in_(ENTRY_TYPE_COST))
            .all()
        )
        assert {r.entry_type for r in rows} == {"expense"}


class TestParamNormalization:
    def test_export_ledger_csv_accepts_dirty_param(self, db_session, clean_ledger):
        clean_ledger(_add_entry(db_session, entry_type="income", category="subscription", amount=700))
        csv_text = FinanceService(db_session).export_ledger_csv(entry_type="income")
        assert "income" in csv_text

    def test_export_ledger_csv_tenant_filter(self, db_session, clean_ledger):
        other = str(uuid.uuid4())
        mine = clean_ledger(
            _add_entry(db_session, entry_type="revenue", category="subscription", amount=800)
        )
        clean_ledger(
            _add_entry(db_session, entry_type="revenue", category="subscription",
                       amount=900, tenant_id=other)
        )
        csv_text = FinanceService(db_session).export_ledger_csv(tenant_id=TENANT)
        assert str(mine.id) in csv_text
        assert other not in csv_text


class TestWriteSideFrozen:
    def test_ledger_create_rejects_dirty_words(self):
        from app.api.v1.routes.finance import LedgerCreate

        with pytest.raises(ValidationError):
            LedgerCreate(entry_type="income", category="subscription", amount_cents=100)
        with pytest.raises(ValidationError):
            LedgerCreate(entry_type="expense", category="llm_api_cogs", amount_cents=100)
        ok = LedgerCreate(entry_type="revenue", category="subscription", amount_cents=100)
        assert ok.entry_type == "revenue"
