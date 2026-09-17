"""事实内核落库（content_masters.fact_kernel_json）单元测试。

覆盖蓝图 §2 的持久化交付：母版发布/建档时把 FactKernel 落成 JSON 快照，
并验证「一核」稳定复用、事实字段变更作废旧核、组不出核不写假值三条不变量。
用内存 SQLite 只建 content_masters 表，避开全库 create_all 的无关依赖。
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.v1.routes.content_master import _serialize
from app.models.content_master import ContentMaster
from app.services.geo.content_kernel_bridge import (
    kernel_from_master,
    persist_kernel,
    touch_kernel_on_update,
)

_SNAP = {
    "trade": {"moq": "100 pieces", "lead_time": "15 days", "certifications": ["ISO 9001"]},
    "evidence": [{"label": "SGS report", "level": "strong"}],
    "copy": {"en": "ISO ceramic fiber board"},
}


@pytest.fixture()
def session():
    engine = create_engine("sqlite://")
    ContentMaster.__table__.create(engine)
    maker = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = maker()
    try:
        yield db
    finally:
        db.close()


def _master(**kw) -> ContentMaster:
    base = dict(
        tenant_id=str(uuid.uuid4()),
        title="Ceramic Fiber Board",
        body="High-temp insulation board, ISO/CE, MOQ 100.",
        media_urls=["https://x/img.jpg"],
        tenant_canonical_url="https://t.example/products/cfb",
        status="draft",
    )
    base.update(kw)
    return ContentMaster(**base)


# ---------------------------------------------------------------- 落库往返
def test_persist_writes_json_column(session):
    row = _master()
    session.add(row)
    session.commit()

    kernel = persist_kernel(row, _SNAP)
    session.commit()
    assert kernel is not None

    session.expire_all()
    reloaded = session.query(ContentMaster).filter(ContentMaster.id == row.id).one()
    assert isinstance(reloaded.fact_kernel_json, dict)
    assert reloaded.fact_kernel_json["trade"]["moq"] == "100 pieces"
    assert reloaded.fact_kernel_json["schema_ready"] is True


def test_persist_marks_degraded_honestly(session):
    """无产品快照 → 只有文案，落库必须带降级标记，不用假值充数。"""
    row = _master()
    kernel = persist_kernel(row)
    assert kernel is not None
    assert row.fact_kernel_json["schema_ready"] is False
    assert row.fact_kernel_json["completeness"] < 1


def test_blank_title_writes_no_fake_snapshot(session):
    row = _master(title="   ")
    assert persist_kernel(row, _SNAP) is None
    assert row.fact_kernel_json is None


# ---------------------------------------------------------------- 一核稳定
def test_cached_kernel_is_reused_not_rebuilt(session):
    row = _master()
    persist_kernel(row, _SNAP)
    # 文案随后被改写：已落库的核仍是发布当时那份（可回溯），不跟着漂移
    row.title = "Totally Different Product"
    cached = kernel_from_master(row)
    assert cached is not None
    assert cached.entity_name == "Ceramic Fiber Board"
    assert cached.trade.moq == "100 pieces"


def test_new_snapshot_forces_rebuild(session):
    row = _master()
    persist_kernel(row, _SNAP)
    rebuilt = kernel_from_master(row, {"trade": {"moq": "500 rolls", "lead_time": "30 days"}})
    assert rebuilt is not None
    assert rebuilt.trade.moq == "500 rolls"


def test_fact_field_update_invalidates_stale_kernel(session):
    row = _master()
    persist_kernel(row, _SNAP)
    row.title = "Silica Brick"
    touch_kernel_on_update(row, {"title"})
    assert row.fact_kernel_json is None
    fresh = persist_kernel(row, _SNAP)
    assert fresh is not None
    assert fresh.entity_name == "Silica Brick"


def test_unrelated_field_update_keeps_kernel(session):
    row = _master()
    persist_kernel(row, _SNAP)
    before = dict(row.fact_kernel_json)
    touch_kernel_on_update(row, {"status"})
    assert row.fact_kernel_json == before


# ---------------------------------------------------------------- 序列化
def test_serialize_exposes_kernel_readiness():
    row = SimpleNamespace(
        id="m-1",
        tenant_id="t-1",
        title="A",
        body="b",
        media_urls=[],
        content_type="article",
        tenant_canonical_url=None,
        status="draft",
        hub_slug=None,
        hub_summary=None,
        show_on_hub=True,
        preflight_checklist_json=None,
        preflight_approved_at=None,
        created_at=None,
        updated_at=None,
        fact_kernel_json={"schema_ready": False, "completeness": 0.2},
    )
    data = _serialize(row)
    assert data["fact_kernel_ready"] is False
    assert data["fact_kernel_completeness"] == 0.2


def test_serialize_tolerates_missing_kernel():
    row = SimpleNamespace(
        id="m-1",
        tenant_id="t-1",
        title="A",
        body="b",
        media_urls=[],
        content_type="article",
        tenant_canonical_url=None,
        status="draft",
        hub_slug=None,
        hub_summary=None,
        show_on_hub=True,
        preflight_checklist_json=None,
        preflight_approved_at=None,
        created_at=None,
        updated_at=None,
        fact_kernel_json=None,
    )
    data = _serialize(row)
    assert data["fact_kernel"] is None
    assert data["fact_kernel_ready"] is False
