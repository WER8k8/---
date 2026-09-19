# -*- coding: utf-8 -*-
"""goodjob_crm = 本项目 CRM · 优丁原生路径单测（无外桥）。"""
from __future__ import annotations

import asyncio
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app.models.enums import OrderStatus
from app.models.inquiry import Inquiry
from app.models.opportunity import Opportunity
from app.models.order import Order
from app.models.trade_fulfillment import Invoice
from app.schemas.hermes_orchestration import TaskNode
from app.services.goodjob import native_fulfillment as nf
from app.services.hermes.executors.goodjob_crm_executor import GoodJobCrmExecutor


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


@pytest.fixture()
def tenant_order(db):
    tid = str(uuid.uuid4())
    order = Order(
        id=str(uuid.uuid4()),
        tenant_id=tid,
        buyer_id=str(uuid.uuid4()),
        merchant_id=str(uuid.uuid4()),
        order_number=f"ORD-NAT-{uuid.uuid4().hex[:6].upper()}",
        total_amount=1000.0,
        currency="USD",
        status=OrderStatus.PENDING,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return tid, order


class _Ctx:
    def __init__(self, db, tenant_id):
        self.db = db
        self.tenant_id = tenant_id
        self.plan_id = "plan_test"


def test_native_pi_no_fake_bank(db):
    out = nf.generate_trade_document(
        doc_type="PI",
        tenant_id=str(uuid.uuid4()),
        params={
            "product_name": "Rock Wool Board 50mm",
            "quantity": 100,
            "unit_price": 12.5,
            "buyer_name": "Acme GmbH",
        },
        db=db,
    )
    assert out["success"] is True
    assert out["native"] is True
    assert out["bank_configured"] is False
    bank = (out.get("document") or {}).get("bank_details") or {}
    assert bank.get("account_no") in (None, "", "PENDING_CONFIGURATION")
    assert db.query(Invoice).filter(Invoice.invoice_no == out["doc_no"]).count() == 1


def test_native_stage_updates_order(db, tenant_order):
    tid, order = tenant_order
    out = nf.sync_fulfillment_stage(
        tenant_id=tid,
        order_id=str(order.id),
        stage="deposit_received",
        step_number=4,
        db=db,
    )
    assert out["success"] is True
    db.refresh(order)
    assert OrderStatus(order.status) == OrderStatus.DEPOSIT_RECEIVED
    assert out["native"] is True


def test_native_lead_creates_inquiry_and_opportunity(db):
    tid = str(uuid.uuid4())
    out = nf.sync_lead(
        tenant_id=tid,
        lead_data={
            "company_name": "Nordic Tools AB",
            "contact_name": "Erik",
            "email": "erik@nordic.example",
            "country": "SE",
        },
        db=db,
    )
    assert out["success"] is True
    assert out["lead_id"]
    assert db.query(Inquiry).count() == 1
    assert db.query(Opportunity).filter(Opportunity.id == out["lead_id"]).first().stage == "prospecting"


def test_executor_native_pi_degraded_without_bank(db, tenant_order):
    tid, order = tenant_order
    ex = GoodJobCrmExecutor()
    node = TaskNode(
        id="n3",
        executor="goodjob_crm",
        capability="document.generate_pi",
        input={
            "product_name": "Insulation Panel",
            "quantity": 10,
            "unit_price": 40,
            "buyer_name": "Buyer Co",
            "order_id": str(order.id),
        },
    )
    result = asyncio.run(ex.run(node, _Ctx(db, tid)))
    assert result.status == "degraded"
    assert result.output.get("native") is True
    assert result.output.get("bank_configured") is False


def test_executor_native_stage_success(db, tenant_order):
    tid, order = tenant_order
    ex = GoodJobCrmExecutor()
    node = TaskNode(
        id="n5",
        executor="goodjob_crm",
        capability="crm.sync_stage",
        input={"order_id": str(order.id), "stage": "in_production", "step_number": 5},
    )
    result = asyncio.run(ex.run(node, _Ctx(db, tid)))
    assert result.status == "succeeded"
    assert result.output.get("native") is True
    db.refresh(order)
    assert OrderStatus(order.status) == OrderStatus.IN_PRODUCTION
