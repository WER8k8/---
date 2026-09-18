# -*- coding: utf-8 -*-
"""P0-1 履约写路径单测：trade_fulfillment_store 九表写读。"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app.models.trade_fulfillment import (
    BusinessPayment,
    ContactEvent,
    ExperienceRecord,
    Invoice,
    KnowledgeBase,
    LogisticsShipment,
    Pipeline,
    PurchaseOrder,
    WhatsappMessage,
)
from app.services.trade_fulfillment_store import (
    ensure_default_pipeline,
    ensure_knowledge_base,
    persist_business_payment,
    persist_contact_event,
    persist_experience_record,
    persist_invoice,
    persist_logistics_shipment,
    persist_purchase_order,
    persist_whatsapp_message,
)


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


def test_persist_whatsapp_message_honest_flags(db):
    tid = str(uuid.uuid4())
    out = persist_whatsapp_message(
        db,
        tenant_id=tid,
        phone_e164="+8613800000000",
        message_body="hello",
        status="failed",
        simulated=True,
        degraded=True,
        error="not_configured",
    )
    assert out["persisted"] is True
    row = db.query(WhatsappMessage).filter(WhatsappMessage.id == out["id"]).first()
    assert row is not None
    assert row.simulated is True
    assert row.degraded is True
    assert row.status == "failed"


def test_persist_logistics_shipment_simulated(db):
    out = persist_logistics_shipment(
        db,
        tenant_id=str(uuid.uuid4()),
        tracking_no="SF123",
        carrier="demo",
        status="in_transit",
        simulated=True,
        payload={"demo": True},
    )
    assert out["persisted"] is True
    row = db.query(LogisticsShipment).filter(LogisticsShipment.id == out["id"]).first()
    assert row.tracking_no == "SF123"
    assert "simulated" in (row.payload_json or "")


def test_persist_experience_and_contact(db):
    e = persist_experience_record(
        db, title="order.create ok", content="path wired", source_type="task", source_id="order.create"
    )
    c = persist_contact_event(
        db,
        tenant_id=str(uuid.uuid4()),
        channel="whatsapp",
        event_type="inquiry",
        summary="need rock wool",
    )
    assert e["persisted"] is True and c["persisted"] is True
    assert db.query(ExperienceRecord).count() == 1
    assert db.query(ContactEvent).count() == 1


def test_purchase_invoice_payment_chain(db):
    tid = str(uuid.uuid4())
    po = persist_purchase_order(db, po_number="PO-T1", tenant_id=tid, status="draft")
    inv = persist_invoice(db, invoice_no="PI-T1", tenant_id=tid, amount=100.0, status="draft")
    pay = persist_business_payment(
        db, amount=30.0, tenant_id=tid, invoice_id=inv.get("id"), status="received", method="tt"
    )
    assert po["persisted"] and inv["persisted"] and pay["persisted"]
    assert db.query(PurchaseOrder).count() == 1
    assert db.query(Invoice).count() == 1
    assert db.query(BusinessPayment).count() == 1


def test_ensure_pipeline_and_kb_idempotent(db):
    tid = str(uuid.uuid4())
    p1 = ensure_default_pipeline(db, tenant_id=tid)
    p2 = ensure_default_pipeline(db, tenant_id=tid)
    k1 = ensure_knowledge_base(db, tenant_id=tid, name="产品知识库")
    k2 = ensure_knowledge_base(db, tenant_id=tid, name="产品知识库")
    assert p1["persisted"] and p2["created"] is False
    assert k1["persisted"] and k2["created"] is False
    assert db.query(Pipeline).count() == 1
    assert db.query(KnowledgeBase).count() == 1
