# -*- coding: utf-8 -*-
"""trade_ai_agent = 本项目拓客 · 优丁原生路径单测。"""
from __future__ import annotations

import asyncio
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app.models.inquiry import Inquiry
from app.models.prospect_lead import ProspectLead
from app.models.trade_fulfillment import ContactEvent, WhatsappMessage
from app.schemas.hermes_orchestration import TaskNode
from app.services.hermes.executors.trade_ai_agent_executor import TradeAiAgentExecutor
from app.services.tradeai import native_acquisition as native


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


class _Ctx:
    def __init__(self, db, tenant_id=None):
        self.db = db
        self.tenant_id = tenant_id
        self.plan_id = "plan_tradeai"


def test_prospect_local_hit_success(db):
    tid = str(uuid.uuid4())
    db.add(
        Inquiry(
            id=str(uuid.uuid4()),
            name="Rock Wool Buyer",
            email="buyer@rock.example",
            product="rock wool board",
            message="Need rock wool 50mm FOB",
            status="pending",
            is_active=True,
            tenant_id=tid,
        )
    )
    db.commit()
    out = native.prospect_scrape(tenant_id=tid, keyword="rock wool", db=db)
    assert out["success"] is True
    assert out["native"] is True
    assert out["hit_count"] >= 1
    assert out["source"] == "youding_pg"
    assert db.query(ContactEvent).count() >= 1


def test_prospect_empty_no_engine_honest_fail(db):
    out = native.prospect_scrape(tenant_id=str(uuid.uuid4()), keyword="zzz_no_such_lead_zzz", db=db)
    assert out["success"] is False
    assert "youding_pg_empty" in (out.get("error") or "")


def test_whatsapp_no_key_fails_and_persists(db):
    # 确保无 Key
    import os
    os.environ.pop("WHATSAPP_ACCESS_TOKEN", None)
    os.environ.pop("WHATSAPP_PHONE_NUMBER_ID", None)
    out = native.outreach_whatsapp(
        tenant_id=str(uuid.uuid4()),
        phone="+8613800000000",
        message="hello",
        db=db,
    )
    assert out["success"] is False
    assert "whatsapp_key_missing" in (out.get("error") or "")
    assert db.query(WhatsappMessage).count() == 1
    row = db.query(WhatsappMessage).first()
    assert row.status == "failed"
    assert row.degraded is True


def test_email_no_smtp_fail(db):
    out = native.outreach_email(
        tenant_id=str(uuid.uuid4()),
        to_email="x@example.com",
        subject="hi",
        body="body",
        db=db,
    )
    assert out["success"] is False
    assert "smtp" in (out.get("error") or "").lower()
    assert db.query(ContactEvent).count() >= 1


def test_classify_native(db):
    out = native.classify_inbox(
        tenant_id=str(uuid.uuid4()),
        message="Please send PI and T/T 30% deposit terms for rock wool",
        db=db,
    )
    assert out["success"] is True
    assert out["detected_intent"] == "trade_document"
    assert out["priority_tier"] == "hot"
    assert out["native"] is True


def test_executor_prospect_and_classify(db):
    tid = str(uuid.uuid4())
    db.add(
        Inquiry(
            id=str(uuid.uuid4()),
            name="Acme",
            email="a@acme.example",
            product="insulation",
            message="quotation for insulation panels",
            status="pending",
            is_active=True,
            tenant_id=tid,
        )
    )
    db.commit()
    ex = TradeAiAgentExecutor()
    node = TaskNode(
        id="n1",
        executor="trade_ai_agent",
        capability="prospect.scrape",
        input={"keyword": "insulation", "limit": 10},
    )
    res = asyncio.run(ex.run(node, _Ctx(db, tid)))
    assert res.status == "succeeded"
    assert res.output.get("native") is True

    node2 = TaskNode(
        id="n2",
        executor="trade_ai_agent",
        capability="inbox.classify",
        input={"message": "What is your best FOB price and MOQ?"},
    )
    res2 = asyncio.run(ex.run(node2, _Ctx(db, tid)))
    assert res2.status == "succeeded"
    assert res2.output.get("detected_intent") == "pricing"
