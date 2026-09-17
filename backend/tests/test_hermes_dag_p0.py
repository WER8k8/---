"""Unit test for Phase P0: Hermes TaskGraph DAG Dispatcher & JsonPath Data Bus.
Verifies that:
1. ExecutorRegistry can register custom/fake executors.
2. A 2-node TaskGraph with dependencies and input_from can execute step-by-step.
3. Node 1 output is dynamically resolved and passed to Node 2.
4. When all child nodes succeed, the parent plan status flips to 'done'.
"""
import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
for _f in ("config/dev/.env", ".env"):
    if os.path.isfile(_f):
        load_dotenv(_f)

import pytest
import json
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.ai_task import AiTask
from app.schemas.hermes_orchestration import TaskGraph, TaskNode, ExecutorResult
from app.services.hermes.executors.base import BaseExecutor, ExecutorContext, ExecutorRegistry
from app.services.hermes.task_control_supervisor import parse_graph_to_tasks, advance_plan


class FakeTestExecutor(BaseExecutor):
    @classmethod
    def get_executor_name(cls) -> str:
        return "fake_p0_executor"

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        if node.capability == "step1":
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={"greeting": "hello_from_step1", "secret_number": 999}
            )
        elif node.capability == "step2":
            received_number = node.input.get("injected_secret")
            return ExecutorResult(
                node_id=node.id,
                status="succeeded",
                output={"status": "step2_confirmed", "received": received_number}
            )
        return ExecutorResult(node_id=node.id, status="failed", error="Unknown capability")


def get_or_create_test_tenant(db: Session) -> str:
    from app.models.tenant import Tenant, TenantPlan
    tenant = db.query(Tenant).first()
    if tenant:
        return str(tenant.id)
        
    plan = db.query(TenantPlan).first()
    if not plan:
        plan = TenantPlan(name="Free Plan", code="free_test", price_monthly=0, price_yearly=0)
        db.add(plan)
        db.flush()
        
    import uuid
    tenant = Tenant(
        name="Test P0 Tenant",
        domain=f"test-p0-{uuid.uuid4().hex[:6]}.example.com",
        plan_id=plan.id
    )
    db.add(tenant)
    db.commit()
    return str(tenant.id)


def test_hermes_p0_dag_end_to_end():
    from app.tasks.celery_app import celery_app
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True

    # 1. Register test executor
    fake_exec = FakeTestExecutor()
    ExecutorRegistry.register(fake_exec)
    assert ExecutorRegistry.has("fake_p0_executor")

    db: Session = SessionLocal()
    try:
        tenant_id = get_or_create_test_tenant(db)
        
        import uuid
        plan_id = f"test_plan_p0_{uuid.uuid4().hex[:8]}"
        
        # 2. Build 2-node TaskGraph with dependency & input_from
        graph = TaskGraph(
            plan_id=plan_id,
            event_id=f"evt_{uuid.uuid4().hex[:6]}",
            strategy="fast",
            nodes=[
                TaskNode(
                    id="node_1",
                    executor="fake_p0_executor",
                    capability="step1",
                    depends_on=[],
                    input={"initial_val": "start"}
                ),
                TaskNode(
                    id="node_2",
                    executor="fake_p0_executor",
                    capability="step2",
                    depends_on=["node_1"],
                    input_from={"injected_secret": "node_1.output.secret_number"}
                )
            ]
        )

        # 3. Shred into DB AiTasks
        tasks = parse_graph_to_tasks(db, tenant_id, graph)
        assert len(tasks) == 2
        plan_task_id = tasks[0].parent_task_id
        assert plan_task_id is not None

        # 4. Trigger initial advance_plan (Node 1 should be dispatched and run)
        dispatched = advance_plan(db, plan_task_id)
        assert len(dispatched) >= 1  # Node 1 triggered

        # Refresh from DB
        db.expire_all()
        plan_task = db.query(AiTask).filter(AiTask.id == plan_task_id).first()
        child_1 = db.query(AiTask).filter(AiTask.idempotency_key == f"node:{graph.plan_id}:node_1").first()
        child_2 = db.query(AiTask).filter(AiTask.idempotency_key == f"node:{graph.plan_id}:node_2").first()

        # Both nodes should have executed to done via local synchronous fallback
        assert child_1.status == "done"
        assert child_2.status == "done"
        
        out1 = json.loads(child_1.output_json or "{}")
        assert out1.get("secret_number") == 999
        
        out2 = json.loads(child_2.output_json or "{}")
        assert out2.get("received") == 999
        assert out2.get("status") == "step2_confirmed"

        # Parent plan should be marked as done!
        assert plan_task.status == "done"

        print("P0 DAG End-to-End Test Passed with Success!")
    finally:
        db.close()

if __name__ == "__main__":
    test_hermes_p0_dag_end_to_end()
