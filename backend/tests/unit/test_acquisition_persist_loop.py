# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""compose-next#2：落库仓储 + 经验闭环。"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from app.api.v1.routes import acquisition as acq_api
from app.services.acquisition import buyer_store, ops_card_store
from app.services.acquisition.experience_feed import record_acquisition_event, record_ops_loss
from app.services.acquisition.repo import persist_inquiry, persist_prospect_lead


def _clear():
    buyer_store._by_id.clear()
    buyer_store._by_email.clear()
    ops_card_store._by_id.clear()
    ops_card_store._by_inquiry.clear()


class _FakeInquiry:
    def __init__(self, **kw):
        self.__dict__.update(kw)
        self.id = "inq-db-1"


def test_persist_inquiry_without_db():
    r = persist_inquiry(None, tenant_id="t1", inquiry_id="INQ-1", message="hello")
    assert r["persisted"] is False
    assert r["reason"]


def test_persist_inquiry_with_mock_db(monkeypatch):
    class _I:
        def __init__(self, **kw):
            self.__dict__.update(kw)
            self.id = "x1"
    import app.services.acquisition.repo as repo
    import sys
    class _Mod:
        Inquiry = _I
    old_inq = sys.modules.get("app.models.inquiry")
    old_lead = sys.modules.get("app.models.prospect_lead")
    try:
        sys.modules["app.models.inquiry"] = _Mod  # type: ignore
        db = MagicMock()
        r = persist_inquiry(db, tenant_id="t1", inquiry_id="INQ-2", message="need quote",
                            email="a@b.com", contact_name="Ahmed", country="SA")
        assert r["persisted"] is True
        assert db.add.called and db.commit.called
    finally:
        if old_inq is not None:
            sys.modules["app.models.inquiry"] = old_inq
        else:
            sys.modules.pop("app.models.inquiry", None)
        if old_lead is not None:
            sys.modules["app.models.prospect_lead"] = old_lead


def test_persist_lead_no_identity():
    r = persist_prospect_lead(None, tenant_id="t", email="", company_name="", contact_name="")
    assert r["persisted"] is False


def test_experience_feed_without_db():
    r = record_acquisition_event(None, tenant_id="t1", event="reply_ingest", inquiry_id="i", success=True)
    assert r["recorded"] is False
    assert "db" in r.get("reason", "")


def test_experience_feed_with_engine(monkeypatch):
    db = MagicMock()

    class _Eng:
        def __init__(self, _db):
            pass
        def record_task_execution(self, **kw):
            return SimpleNamespace(id="exp-1", **kw)

    import app.services.acquisition.experience_feed as ef
    import app.services.evolution.engine as evo
    monkeypatch.setattr(evo, "EvolutionEngine", _Eng, raising=False)
    # experience_feed imports inside function - patch module attribute after import
    import importlib
    importlib.import_module("app.services.evolution.engine")
    monkeypatch.setattr("app.services.evolution.engine.EvolutionEngine", _Eng)
    r = record_acquisition_event(db, tenant_id="t1", event="ops_touch", inquiry_id="INQ", success=True, detail="ok")
    assert r["recorded"] is True
    assert r["engine"] == "EvolutionEngine"


def test_reply_ingest_returns_persistence_and_experience():
    _clear()
    body = acq_api.ReplyIngestRequest(
        tenant_id="t1",
        inquiry_id="INQ-P-1",
        message="CIF Jeddah",
        country="IN",
        grade=70,
        email="x@y.com",
        contact_name="Li",
        company_name="CN Panel",
    )
    resp = acq_api.reply_ingest(body, current_user=None, db=None)
    assert resp["card"] is not None
    assert "persistence" in resp
    assert resp["persistence"]["inquiry"]["persisted"] is False
    assert "experience" in resp
    assert resp["experience"]["recorded"] is False
    assert resp["summary"]["负责人"] is not None


def test_ops_loss_experience_shape():
    _clear()
    ops_card_store.materialize(tenant_id="t1", inquiry_id="INQ-LOSS")
    r = acq_api.ops_card_loss(
        "INQ-LOSS",
        acq_api.OpsCardLossRequest(reasons=["价格高"], note="同行更低"),
        current_user=None,
        db=None,
    )
    assert r["experience"]["recorded"] is False
    assert r["experience"]["task_type"].endswith("ops_loss")
    assert r["card"]["stage"] == "lost"


def test_ops_touch_experience_shape():
    _clear()
    ops_card_store.materialize(tenant_id="t1", inquiry_id="INQ-T")
    r = acq_api.ops_card_touch(
        "INQ-T",
        acq_api.OpsCardTouchRequest(summary="已回"),
        current_user=None,
        db=None,
    )
    assert "experience" in r
    assert r["experience"]["recorded"] is False


def test_reply_ingest_with_fake_db_persists(monkeypatch):
    _clear()
    db = MagicMock()

    class _I:
        id = "db-i"
        def __init__(self, **kw):
            self.__dict__.update(kw)

    class _P:
        id = "db-p"
        def __init__(self, **kw):
            self.__dict__.update(kw)

    class _Eng:
        def __init__(self, _db):
            pass
        def record_task_execution(self, **kw):
            return SimpleNamespace(id="e2")

    import sys
    old_inq = sys.modules.get("app.models.inquiry")
    old_lead = sys.modules.get("app.models.prospect_lead")
    try:
        sys.modules["app.models.inquiry"] = SimpleNamespace(Inquiry=_I)
        sys.modules["app.models.prospect_lead"] = SimpleNamespace(
            ProspectLead=_P,
            LeadSource=SimpleNamespace(MANUAL_IMPORT="manual_import", HUNTER_IO="hunter", LINKEDIN="linkedin",
                                       WHATSAPP="whatsapp", GOOGLE_CSE="google", WEBSITE_SCRAPE="web",
                                       REFERRAL="referral"),
        )
        monkeypatch.setattr("app.services.evolution.engine.EvolutionEngine", _Eng)
        body = acq_api.ReplyIngestRequest(
            tenant_id="t1",
            inquiry_id="INQ-DB-1",
            message="hello",
            email="z@z.com",
            contact_name="Bob",
            company_name="Acme",
            country="SA",
        )
        resp = acq_api.reply_ingest(body, current_user=None, db=db)
        assert resp["persistence"]["inquiry"]["persisted"] is True
        assert resp["experience"]["recorded"] is True
        assert db.commit.called
    finally:
        if old_inq is not None:
            sys.modules["app.models.inquiry"] = old_inq
        else:
            sys.modules.pop("app.models.inquiry", None)
        if old_lead is not None:
            sys.modules["app.models.prospect_lead"] = old_lead
        else:
            sys.modules.pop("app.models.prospect_lead", None)
