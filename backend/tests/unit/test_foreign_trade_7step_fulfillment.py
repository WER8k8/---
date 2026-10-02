# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""外贸 7 步履约与单证套打全链路单元测试.

覆盖：
1. Step 1~3: 询盘关联订单与形式发票 (PI) 套打，更新 document_stage='pi_issued'；
2. Step 4: 定金核销 (deposit_received) 联动写入 payments 表并更新 payment_stage='deposit_verified'；
3. Step 5: 生产排期与跟单 (in_production) 联动写入 purchase_orders 表并更新 fulfillment_stage='in_production'；
4. Step 6: 发运单证一键套打 (CI + Packing List) 并联动写入 invoices 与 logistics_shipments；
5. Step 7: 尾款核销 (final_payment_received) 联动写入 payments 表并推进 completed。
"""
import uuid
from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.enums import OrderStatus, PaymentStatus
from app.models.inquiry import Inquiry
from app.models.order import Order
from app.models.user import User
from app.models.trade_fulfillment import (
    BusinessPayment,
    Invoice,
    LogisticsShipment,
    PurchaseOrder,
    ContactEvent,
    Pipeline,
)
from app.schemas.hermes_orchestration import TaskNode
from app.services.hermes.executors.base import ExecutorContext
from app.services.hermes.executors.goodjob_crm_executor import GoodJobCrmExecutor
from app.services.goodjob import native_fulfillment as native


@pytest.fixture
def memory_db():
    engine = create_engine("sqlite://")
    from app.models.admin import AdminRole
    AdminRole.__table__.create(engine)
    Inquiry.__table__.create(engine)
    User.__table__.create(engine)
    Order.__table__.create(engine)
    BusinessPayment.__table__.create(engine)
    Invoice.__table__.create(engine)
    LogisticsShipment.__table__.create(engine)
    PurchaseOrder.__table__.create(engine)
    ContactEvent.__table__.create(engine)
    Pipeline.__table__.create(engine)

    Session = sessionmaker(bind=engine, expire_on_commit=False)
    db = Session()

    buyer_id = str(uuid.uuid4())
    seller_id = str(uuid.uuid4())
    # 预置买家与卖家用户
    buyer = User(
        id=buyer_id,
        username="buyer_test",
        email="buyer@example.com",
        hashed_password="dummy_hash_buyer",
        role="user",
        is_active=True,
    )
    seller = User(
        id=str(uuid.uuid4()),
        username="seller_test",
        email="seller@example.com",
        hashed_password="dummy_hash_seller",
        role="tenant_admin",
        is_active=True,
    )
    db.add_all([buyer, seller])
    db.commit()

    yield db, buyer, seller
    db.close()


def test_7step_fulfillment_complete_cycle(memory_db):
    db, buyer, seller = memory_db
    tenant_id = str(uuid.uuid4())

    # Step 1: 创建询盘 (Inquiry)
    inq = Inquiry(
        id=str(uuid.uuid4()),
        name="Al-Mansoor Construction",
        email="buyer@almansoor.sa",
        phone="+966501234567",
        product="Rockwool Acoustic Ceiling 600x600x15mm",
        message="Request quotation for 2x40HQ containers CIF Dammam",
        status="pending",
        tenant_id=tenant_id,
        source_channel="wecom_ingress",
    )
    db.add(inq)
    db.commit()

    # Step 2: 订单创建 (Order)
    order_num = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    order = Order(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        buyer_id=buyer.id,
        merchant_id=seller.id,
        order_number=order_num,
        total_amount=Decimal("50000.00"),
        currency="USD",
        status=OrderStatus.PENDING,
        payment_status=PaymentStatus.PENDING,
        incoterms="CIF Dammam",
        payment_terms="T/T 30% deposit, 70% against B/L",
        port_of_loading="Shenzhen, China",
        port_of_discharge="Dammam, Saudi Arabia",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    executor = GoodJobCrmExecutor(dry_run=True)
    ctx = ExecutorContext(tenant_id=tenant_id, plan_id="plan-7step", db=db)

    # Step 3: 出具形式发票 (PI) 套打
    node_pi = TaskNode(
        id="n_pi",
        executor="goodjob_crm",
        capability="document.generate_pi",
        input={
            "order_id": str(order.id),
            "inquiry_id": str(inq.id),
            "buyer_name": "Al-Mansoor Construction",
            "product_name": "Rockwool Acoustic Ceiling",
            "quantity": 2000,
            "unit_price": 25.0,
            "currency": "USD",
        },
    )
    res_pi = executor._run_native(node_pi, ctx, "document.generate_pi")
    assert res_pi.status in ("succeeded", "degraded")
    assert res_pi.output.get("pi_number") is not None
    db.refresh(order)
    assert order.document_stage == "pi_issued"

    # Step 4: 定金核销 (deposit_received)
    node_dep = TaskNode(
        id="n_dep",
        executor="goodjob_crm",
        capability="crm.sync_stage",
        input={
            "order_id": str(order.id),
            "stage": "deposit_received",
            "step_number": 4,
            "deposit_ratio": 30.0,
            "payment_ref": "TT-SA-20261002-001",
        },
    )
    res_dep = executor._run_native(node_dep, ctx, "crm.sync_stage")
    assert res_dep.status == "succeeded"
    db.refresh(order)
    assert order.status == OrderStatus.DEPOSIT_RECEIVED
    assert order.payment_stage == "deposit_verified"
    assert float(order.deposit_amount) == 15000.0  # 30% of 50000

    # 验证 payments 表已落盘定金记录
    pay_dep = db.query(BusinessPayment).filter(BusinessPayment.order_id == str(order.id)).first()
    assert pay_dep is not None
    assert float(pay_dep.amount) == 15000.0
    assert pay_dep.status == "confirmed"

    # Step 5: 生产排期与跟单 (in_production)
    node_prod = TaskNode(
        id="n_prod",
        executor="goodjob_crm",
        capability="crm.sync_stage",
        input={
            "order_id": str(order.id),
            "stage": "in_production",
            "step_number": 5,
            "po_number": f"PO-{order.order_number}",
            "product_desc": "Rockwool Ceiling 600x600x15mm Fireproof Grade A",
            "quantity": 2000,
        },
    )
    res_prod = executor._run_native(node_prod, ctx, "crm.sync_stage")
    assert res_prod.status == "succeeded"
    db.refresh(order)
    assert order.status == OrderStatus.IN_PRODUCTION
    assert order.fulfillment_stage == "in_production"

    # 验证 purchase_orders 表已落盘排产工单
    po_row = db.query(PurchaseOrder).filter(PurchaseOrder.order_id == str(order.id)).first()
    assert po_row is not None
    assert po_row.po_number == f"PO-{order.order_number}"
    assert po_row.status == "producing"

    # Step 6: 发运单证 (CI + PL) 双单套打
    node_docs = TaskNode(
        id="n_docs",
        executor="goodjob_crm",
        capability="document.generate_trade_docs",
        input={
            "order_id": str(order.id),
            "docs": ["CI", "PL"],
            "buyer_name": "Al-Mansoor Construction",
            "product_name": "Rockwool Acoustic Ceiling",
            "quantity": 2000,
            "unit_price": 25.0,
            "currency": "USD",
            "bl_number": "COSU6283921980",
            "deposit_paid": 15000.0,
        },
    )
    res_docs = executor._run_native(node_docs, ctx, "document.generate_trade_docs")
    assert res_docs.status == "succeeded"
    assert "CI" in res_docs.output.get("documents", {})
    assert "PL" in res_docs.output.get("documents", {})

    # 推进订单状态至 shipped 并写入发运单
    node_ship = TaskNode(
        id="n_ship",
        executor="goodjob_crm",
        capability="crm.sync_stage",
        input={
            "order_id": str(order.id),
            "stage": "shipped",
            "step_number": 6,
            "tracking_number": "COSU6283921980",
            "carrier": "COSCO SHIPPING",
        },
    )
    res_ship = executor._run_native(node_ship, ctx, "crm.sync_stage")
    assert res_ship.status == "succeeded"
    db.refresh(order)
    assert order.status == OrderStatus.SHIPPED
    assert order.fulfillment_stage == "ready_to_ship"
    assert order.tracking_number == "COSU6283921980"

    # 验证 logistics_shipments 表已落盘
    shipment = db.query(LogisticsShipment).filter(LogisticsShipment.order_id == str(order.id)).first()
    assert shipment is not None
    assert shipment.tracking_no == "COSU6283921980"
    assert shipment.carrier == "COSCO SHIPPING"

    # Step 7: 尾款核销 (final_payment_received) 与订单完成
    node_final = TaskNode(
        id="n_final",
        executor="goodjob_crm",
        capability="crm.sync_stage",
        input={
            "order_id": str(order.id),
            "stage": "final_payment_received",
            "step_number": 7,
            "payment_ref": "TT-SA-20261002-FINAL",
        },
    )
    res_final = executor._run_native(node_final, ctx, "crm.sync_stage")
    assert res_final.status == "succeeded"
    db.refresh(order)
    assert order.status == OrderStatus.FINAL_PAYMENT_RECEIVED
    assert order.payment_stage == "paid"

    # 验证 payments 表已落盘尾款 35000.0 (50000 - 15000)
    payments = db.query(BusinessPayment).filter(BusinessPayment.order_id == str(order.id)).all()
    assert len(payments) == 2
    bal_pay = [p for p in payments if "尾款" in (p.notes or "")][0]
    assert float(bal_pay.amount) == 35000.0

    # 最终订单交付完成
    node_comp = TaskNode(
        id="n_comp",
        executor="goodjob_crm",
        capability="crm.sync_stage",
        input={"order_id": str(order.id), "stage": "completed", "step_number": 7},
    )
    res_comp = executor._run_native(node_comp, ctx, "crm.sync_stage")
    assert res_comp.status == "succeeded"
    db.refresh(order)
    assert order.status == OrderStatus.COMPLETED
    assert order.fulfillment_stage == "completed"
