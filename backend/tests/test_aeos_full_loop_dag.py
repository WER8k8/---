"""AEOS v1.0 Full Closed-Loop Integration Test.

测试范围：
1. DAG Governor:
   - 环路死锁检测 (Cycle Detection)
   - 超限节点防爆 (Max Nodes Guard)
2. 跨子系统流转 (Trade AI Agent ➔ GoodJob CRM ➔ PI发票 ➔ WhatsApp触达):
   - Node 1 (Trade AI Agent): 潜客社媒挖掘 (prospect.scrape)
   - Node 2 (GoodJob CRM): 外贸7步漏斗阶段同步 (crm.sync_stage)
   - Node 3 (GoodJob CRM): 形式发票 PI 生成 (document.generate_pi) 经 JsonPath 取 Node 1 买家名
   - Node 4 (Trade AI Agent): WhatsApp 发送 (outreach.whatsapp) 经 JsonPath 取 Node 1 手机号
3. 验证 JsonPath 动态数据总线穿透与父计划全绿达成。
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from typing import Any

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
for _f in ("config/dev/.env", ".env"):
    if os.path.isfile(_f):
        load_dotenv(_f)

import pytest
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.ai_task import AiTask
from app.models.tenant import Tenant, TenantPlan
from app.schemas.hermes_orchestration import TaskGraph, TaskNode
from app.services.hermes.executors import ExecutorRegistry
from app.services.hermes.task_control_supervisor import advance_plan, parse_graph_to_tasks


def get_or_create_test_tenant(db: Session) -> str:
    tenant = db.query(Tenant).first()
    if tenant:
        return str(tenant.id)

    plan = db.query(TenantPlan).first()
    if not plan:
        plan = TenantPlan(name="Free Plan", code="free_test", price_monthly=0, price_yearly=0)
        db.add(plan)
        db.flush()

    tenant = Tenant(
        name="Test AEOS Tenant",
        domain=f"test-aeos-{uuid.uuid4().hex[:6]}.example.com",
        plan_id=plan.id,
    )
    db.add(tenant)
    db.commit()
    return str(tenant.id)


# ---------------------------------------------------------------------------
# 1. DAG Governor 拓扑安全测试
# ---------------------------------------------------------------------------
def test_dag_governor_cycle_detection():
    """测试 DAG Governor 能够正确拦截有向环路拓扑。"""
    db: Session = SessionLocal()
    try:
        tenant_id = get_or_create_test_tenant(db)
        plan_id = f"test_cycle_{uuid.uuid4().hex[:6]}"

        # 构造 Node A -> Node B -> Node A 环路
        graph = TaskGraph(
            plan_id=plan_id,
            event_id=f"evt_{uuid.uuid4().hex[:6]}",
            nodes=[
                TaskNode(id="A", executor="accio", capability="test", depends_on=["B"]),
                TaskNode(id="B", executor="accio", capability="test", depends_on=["A"]),
            ],
        )

        with pytest.raises(ValueError) as exc_info:
            parse_graph_to_tasks(db, tenant_id, graph)

        assert "死循环环路" in str(exc_info.value)
    finally:
        db.close()


def test_dag_governor_max_nodes_guard():
    """测试 DAG Governor 能够正确拦截超过 100 节点的拓扑爆炸。"""
    db: Session = SessionLocal()
    try:
        tenant_id = get_or_create_test_tenant(db)
        plan_id = f"test_overflow_{uuid.uuid4().hex[:6]}"

        nodes = [
            TaskNode(id=f"n_{i}", executor="accio", capability="test")
            for i in range(105)
        ]
        graph = TaskGraph(
            plan_id=plan_id,
            event_id=f"evt_{uuid.uuid4().hex[:6]}",
            nodes=nodes,
        )

        with pytest.raises(ValueError) as exc_info:
            parse_graph_to_tasks(db, tenant_id, graph)

        assert "超过最大节点数限制" in str(exc_info.value)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 2. AEOS 全闭环流转测试 (Trade AI Agent + GoodJob CRM)
# ---------------------------------------------------------------------------
def test_aeos_trade_ai_and_goodjob_crm_closed_loop():
    """测试 Trade AI Agent 拓客 ➔ GoodJob 漏斗 ➔ PI 发票 ➔ WhatsApp 触达全链路。"""
    from app.tasks.celery_app import celery_app
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True

    # 验证执行器在注册表中
    assert ExecutorRegistry.has("trade_ai_agent")
    assert ExecutorRegistry.has("goodjob_crm")

    db: Session = SessionLocal()
    try:
        tenant_id = get_or_create_test_tenant(db)
        # 外部依赖门禁：trade-ai-agent 未注册 prospect workflow（workflows=[]）时该链路
        # 必然失败，明确跳过而非误报回归；workflow 接入后自动恢复执行。
        try:
            from app.services.adapters import tradeai as _taa

            orch = _taa.tenant_orchestrator(tenant_id)
            wf_names = {getattr(w, "name", "") for w in orch.list_workflows()}
            if not ({"prospect_search", "scrape_prospects", "lead_finder"} & wf_names):
                pytest.skip(
                    f"trade-ai-agent 未注册 prospect workflow（现有: {sorted(wf_names)}），"
                    "跳过闭环集成测试"
                )
        except Exception:  # noqa: BLE001
            pytest.skip("trade-ai-agent 适配器不可用，跳过闭环集成测试")
        plan_id = f"aeos_plan_{uuid.uuid4().hex[:8]}"

        graph = TaskGraph(
            plan_id=plan_id,
            event_id=f"evt_{uuid.uuid4().hex[:6]}",
            strategy="standard",
            nodes=[
                # Node 1: Trade AI Agent 社媒拓客挖掘
                TaskNode(
                    id="node_scrape",
                    executor="trade_ai_agent",
                    capability="prospect.scrape",
                    input={"keyword": "Ceramic Tiles", "country": "Saudi Arabia", "limit": 3},
                ),
                # Node 2: GoodJob CRM 7 步商机建档同步
                TaskNode(
                    id="node_crm",
                    executor="goodjob_crm",
                    capability="crm.sync_stage",
                    depends_on=["node_scrape"],
                    input={"stage": "contacted"},
                    input_from={"lead_id": "node_scrape.output.prospects[0].email"},
                ),
                # Node 3: GoodJob CRM 形式发票 PI 自动生成
                TaskNode(
                    id="node_pi",
                    executor="goodjob_crm",
                    capability="document.generate_pi",
                    depends_on=["node_crm"],
                    input={"product_name": "Glazed Porcelain Tiles", "quantity": 2500, "unit_price": 18.5},
                    input_from={
                        "buyer_name": "node_scrape.output.prospects[0].company_name",
                        "country": "node_scrape.output.prospects[0].country",
                    },
                ),
                # Node 4: Trade AI Agent WhatsApp 触达通知
                TaskNode(
                    id="node_notify",
                    executor="trade_ai_agent",
                    capability="outreach.whatsapp",
                    depends_on=["node_pi"],
                    input={"content": "Your Proforma Invoice has been prepared and approved."},
                    input_from={
                        "whatsapp": "node_scrape.output.prospects[0].whatsapp",
                        "pi_number": "node_pi.output.pi_number",
                    },
                ),
            ],
        )

        # 1. 落地 DAG 到数据库
        node_tasks = parse_graph_to_tasks(db, tenant_id, graph)
        assert len(node_tasks) == 4

        # 获取父计划
        parent_plan = db.query(AiTask).filter(
            AiTask.idempotency_key == f"plan:{plan_id}"
        ).first()
        assert parent_plan is not None
        assert parent_plan.status == "planning"

        # 2. 初始推进 -> 派发 Node 1 (node_scrape 无依赖)
        advance_plan(db, parent_plan.id)

        db.refresh(parent_plan)
        # Celery eager 模式下，Node 1 执行完毕后会自动回调 advance_plan 递归推进 Node 2 -> Node 3 -> Node 4！
        assert parent_plan.status == "done"

        # 3. 逐一验证各节点产物及 JsonPath 流转精度
        tasks = db.query(AiTask).filter(AiTask.parent_task_id == parent_plan.id).all()
        task_map = {}
        for t in tasks:
            in_data = json.loads(t.input_json or "{}")
            task_map[in_data["node_id"]] = t

        # 验证 Node 1 (Trade AI Agent 拓客挖掘)
        t_scrape = task_map["node_scrape"]
        assert t_scrape.status in ("done", "succeeded")
        out_scrape = json.loads(t_scrape.output_json or "{}")
        assert out_scrape["keyword"] == "Ceramic Tiles"
        assert len(out_scrape["prospects"]) >= 1
        first_buyer = out_scrape["prospects"][0]
        assert "company_name" in first_buyer

        # 验证 Node 2 (GoodJob CRM 7步商机流转)
        t_crm = task_map["node_crm"]
        assert t_crm.status in ("done", "succeeded")
        in_crm = json.loads(t_crm.input_json or "{}")
        assert in_crm["effective_input"]["lead_id"] == first_buyer["email"]

        # 验证 Node 3 (GoodJob CRM PI 形式发票)
        t_pi = task_map["node_pi"]
        assert t_pi.status in ("done", "succeeded")
        in_pi = json.loads(t_pi.input_json or "{}")
        assert in_pi["effective_input"]["buyer_name"] == first_buyer["company_name"]
        out_pi = json.loads(t_pi.output_json or "{}")
        assert "pi_number" in out_pi
        assert out_pi["total_amount"] == 2500 * 18.5
        assert out_pi["document"]["seller"]["bank_name"] == "Standard Chartered Bank (China) Limited"

        # 验证 Node 4 (Trade AI Agent WhatsApp 触达)
        t_notify = task_map["node_notify"]
        assert t_notify.status in ("done", "succeeded")
        in_notify = json.loads(t_notify.input_json or "{}")
        assert in_notify["effective_input"]["whatsapp"] == first_buyer["whatsapp"]
        out_notify = json.loads(t_notify.output_json or "{}")
        assert out_notify["dispatched"] is True

    finally:
        db.close()
