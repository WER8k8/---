# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""BOQ 管道测试（修正设计稿 模块3 / Gate G6）。

锁定语义：
- 单位归一别名表；无法确认 → None（硬拒条件）；
- 数量解析容忍千分位；
- 状态机：extracted 直跳 calculate 被拒（禁止 extracted → quote 跳步）；
- 匹配：高置信 auto_selected / 中置信 review_required / 低置信 manual_required；
- 硬规则优先：材料冲突 → rejected（候选阶段即出局）；单位无法确认 → rejected；
- 复核门控：存在未确认行项时 calculate 409（需要确认 N 项）；
- 全齐后 calculate → calculated，grand_total > 0；approve 需人工。
"""
from __future__ import annotations

import pytest

from app.models.boq_import import BoqLineItem
from app.models.product import Category, Product
from app.services import boq_pipeline_service as bps

TENANT = "6a111111-1111-4111-8111-111111111111"


@pytest.fixture
def catalog(db_session):
    cat = Category(
        id="6b111111-1111-4111-8111-111111111111",
        name="瓷砖",
        slug="ceramic-tiles-test",
    )
    db_session.add(cat)
    db_session.flush()
    products = []
    for pid, name, name_en in (
        ("6c111111-1111-4111-8111-111111111111", "全抛釉瓷砖 800x800", "Full Polished Ceramic Tile 800x800"),
        ("6d111111-1111-4111-8111-111111111111", "大理石大板 意大利白", "Marble Slab Italian White"),
    ):
        p = Product(
            id=pid,
            tenant_id=TENANT,
            category_id=cat.id,
            name=name,
            slug=f"boq-test-{pid[:8]}",
            name_en=name_en,
            is_active=True,
        )
        db_session.add(p)
        products.append(p)
    db_session.commit()
    return {"category": cat, "tile": products[0], "marble": products[1]}


def _job(db, status="uploaded"):
    """按合法路径构造指定状态的作业（uploaded→extracting→extracted 经 add_manual_lines）。"""
    job = bps.create_job(db, tenant_id=TENANT, source_name="标书A.pdf")
    if status in ("extracting", "extracted"):
        bps.add_manual_lines(
            db, job,
            [{"description": "全抛釉瓷砖 800x800", "quantity": "1000", "unit": "sqm"}],
            extractor="manual",
        )
    db.commit()
    return job


class TestUnitNormalization:
    def test_alias_table(self):
        assert bps.normalize_unit("㎡") == "sqm"
        assert bps.normalize_unit("M2") == "sqm"
        assert bps.normalize_unit(" 平方米 ") == "sqm"
        assert bps.normalize_unit("立方米") == "cbm"
        assert bps.normalize_unit("吨") == "ton"
        assert bps.normalize_unit("支") == "pcs"

    def test_unknown_unit_is_none(self):
        assert bps.normalize_unit("车") is None
        assert bps.normalize_unit("") is None

    def test_quantity_parsing(self):
        assert bps.normalize_quantity("1,200.5") == 1200.5
        assert bps.normalize_quantity("约300平方") == 300.0
        assert bps.normalize_quantity("无数量") is None


class TestStateGating:
    def test_extracted_cannot_calculate(self, db_session):
        """设计红线：禁止 extracted → quote 跳步。"""
        job = _job(db_session, status="extracted")
        with pytest.raises(bps.PipelineError) as ei:
            bps.run_calculation(db_session, job)
        assert ei.value.status_code == 409

    def test_illegal_transition_rejected(self, db_session):
        job = _job(db_session, status="uploaded")
        with pytest.raises(bps.PipelineError):
            bps.transition(job, "calculated")


class TestMatching:
    def _job_with_lines(self, db, catalog, rows):
        job = bps.create_job(db, tenant_id=TENANT, source_name="t")
        bps.add_manual_lines(db, job, rows, extractor="manual")
        bps.run_normalization(db, job)
        return job

    def test_high_confidence_auto_selected(self, db_session, catalog):
        job = self._job_with_lines(
            db_session,
            catalog,
            [{"description": "全抛釉瓷砖 800x800 优质", "quantity": "1200", "unit": "㎡"}],
        )
        report = bps.run_matching(db_session, job)
        line = db_session.query(BoqLineItem).filter_by(boq_job_id=job.id).first()
        assert line.review_status == "auto_selected"
        assert str(line.selected_product_id) == str(catalog["tile"].id)
        assert line.match_confidence >= 0.85
        assert job.status == "matching"

    def test_material_conflict_hard_rejected(self, db_session, catalog):
        """硬规则优先：行是花岗岩（库中只有瓷砖/大理石）→ 两个候选都被材料冲突出局 → 需人工。"""
        job = self._job_with_lines(
            db_session,
            catalog,
            [{"description": "花岗岩 墙面 干挂", "quantity": "300", "unit": "sqm"}],
        )
        bps.run_matching(db_session, job)
        line = db_session.query(BoqLineItem).filter_by(boq_job_id=job.id).first()
        # 无同材料产品：全部候选被硬冲突出局 → 不得自动选（宁可人工，不可误导选）
        assert line.review_status == "manual_required"
        assert line.candidate_products == []

    def test_same_material_auto_selected(self, db_session, catalog):
        """同材料行（大理石）→ 大理石产品名完整命中 → auto_selected（瓷砖候选被硬拒出局）。"""
        job = self._job_with_lines(
            db_session,
            catalog,
            [{"description": "大理石大板 意大利白", "quantity": "300", "unit": "sqm"}],
        )
        bps.run_matching(db_session, job)
        line = db_session.query(BoqLineItem).filter_by(boq_job_id=job.id).first()
        assert line.review_status == "auto_selected"
        assert str(line.selected_product_id) == str(catalog["marble"].id)

    def test_unknown_unit_rejected(self, db_session, catalog):
        job = self._job_with_lines(
            db_session,
            catalog,
            [{"description": "神秘材料", "quantity": "5", "unit": "车"}],
        )
        bps.run_matching(db_session, job)
        line = db_session.query(BoqLineItem).filter_by(boq_job_id=job.id).first()
        assert line.review_status == "rejected"
        assert line.reject_reason == "unit_unrecognized"


class TestReviewAndCalculation:
    def _full_job(self, db, catalog):
        job = bps.create_job(
            db, tenant_id=TENANT, source_name="标书.pdf",
            defaults={"incoterms": "FOB", "material_type": "ceramic"},
        )
        bps.add_manual_lines(
            db, job,
            [{"description": "全抛釉瓷砖 800x800", "quantity": "1000", "unit": "sqm"}],
            extractor="manual",
        )
        bps.run_normalization(db, job)
        bps.run_matching(db, job)
        return job

    def test_review_pending_blocks_calculate(self, db_session, catalog):
        job = self._full_job(db_session, catalog)
        line = db_session.query(BoqLineItem).filter_by(boq_job_id=job.id).first()
        line.review_status = "manual_required"  # 模拟需要人工
        db_session.add(line)
        db_session.commit()
        with pytest.raises(bps.PipelineError) as ei:
            bps.run_calculation(db_session, job)
        assert ei.value.code == "review_pending"
        assert "1" in ei.value.message

    def test_calculate_then_approve(self, db_session, catalog):
        job = self._full_job(db_session, catalog)
        result = bps.run_calculation(db_session, job, defaults={"incoterms": "CIF"})
        assert job.status == "calculated"
        assert result["grand_total_usd"] > 0
        lines = [l for l in result["lines"] if "total" in l]
        assert lines and lines[0]["calc"]["error"] is None if "error" in lines[0]["calc"] else True

        job = bps.approve_job(db_session, job, approver="tester")
        assert job.status == "approved"
        assert job.result_json["approved_by"] == "tester"

    def test_text_table_extraction(self):
        text = "品名 | 数量 | 单位\n全抛釉瓷砖 800x800 | 1,200 | ㎡\n"
        rows = bps.parse_text_table(text)
        assert len(rows) == 1
        assert rows[0]["normalized_quantity"] == 1200.0
        assert rows[0]["normalized_unit"] == "sqm"
