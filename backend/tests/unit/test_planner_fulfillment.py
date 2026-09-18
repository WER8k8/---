"""贸易履约意图 → L1 模板：订单/单证/CRM/物流执行器被主链驱动（串联缺口补齐）"""
from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

from app.schemas.hermes_orchestration import IntentEvent


def _decompose(intent: str, payload: dict):
    from app.services.hermes.planner_service import decompose

    ev = IntentEvent(event_id="e1", tenant_id="t1", channel="api", intent=intent, payload=payload)
    return asyncio.run(decompose(ev, MagicMock()))


# 真实执行器契约：executor -> capability -> 已声明输出键（防"引用不存在字段"的假交付）
from app.services.hermes.executors.goodjob_crm_executor import GoodJobCrmExecutor  # noqa: E402
from app.services.hermes.executors.inquiry_executor import InquiryExecutor  # noqa: E402
from app.services.hermes.executors.logistics_executor import LogisticsExecutor  # noqa: E402
from app.services.hermes.executors.order_executor import OrderExecutor  # noqa: E402

_REAL_OUTPUTS: dict[tuple[str, str], set[str]] = {}
for _E in (InquiryExecutor, OrderExecutor, GoodJobCrmExecutor, LogisticsExecutor):
    for _cap, _meta in _E.get_capabilities().items():
        _REAL_OUTPUTS[(_E.get_executor_name(), _cap)] = set(_meta.get("output") or [])


def test_fulfillment_cross_node_refs_are_real_outputs():
    """防假交付：每条 input_from=「src.output.字段」必须命中前驱执行器真实声明的输出键。"""
    from app.services.hermes.planner_service import _fulfillment_graph

    g = _fulfillment_graph("p", "e", {})
    nodes = {n.id: n for n in g.nodes}
    assert len(nodes) == 9  # 7步闭环 + PI前风控 trade_ops.pi_precheck
    for n in g.nodes:
        assert set(n.depends_on or []) <= set(nodes)  # depends_on 引用的节点必须存在
        for target, ref in (n.input_from or {}).items():
            src_id, _, field = ref.partition(".output.")
            src = nodes[src_id]
            declared = _REAL_OUTPUTS.get((src.executor, src.capability), set())
            # 允许少数契约未显式声明 output 的宽松通过，但显式声明的必须对得上
            if declared:
                assert field in declared, f"{n.id}.{target} 引用了 {src.executor} 未声明的输出 {field!r}"


def test_fulfillment_intent_resolves_to_l1_template():
    graph, source = _decompose("履约 生成PI 并跟踪物流", {"order_id": "ORD-1", "order_number": "ORD-2026"})
    assert source == "L1_template"
    assert {n.capability for n in graph.nodes} >= {
        "inquiry.capture", "order.create", "document.generate_pi", "crm.sync_stage", "logistics.track",
    }


def test_fulfillment_graph_only_uses_registered_executors():
    from app.services.hermes.executors import ExecutorRegistry
    from app.services.hermes.planner_service import validate_graph

    graph, source = _decompose("订单物流跟单", {"message": "客户下了一笔订单"})
    assert source == "L1_template"
    allowed = set(ExecutorRegistry.list_executors())
    assert all(n.executor in allowed for n in graph.nodes)
    assert validate_graph(graph) == []  # 三道安全阀全过：无未注册执行器/能力、无环


def test_fulfillment_logistics_waits_for_pi_and_crm():
    graph, source = _decompose("外贸履约：发货并出PI", {"message": "集装箱已备妥"})
    assert source == "L1_template"
    n = {node.id: node for node in graph.nodes}
    assert n["n7"].capability == "logistics.track"
    assert n["n7"].depends_on == ["n6"]  # 物流可查排在 CI/PL 发运单证之后


class TestSocialOutreach:
    """社媒/WhatsApp 全域拓客：trade_ai_agent 进 L1（此前注册未驱动）。"""

    def test_social_intent_resolves_to_l1_and_uses_trade_ai_agent(self):
        graph, source = _decompose("WhatsApp 全域拓客", {"keyword": "building materials"})
        assert source == "L1_template"
        assert {n.executor for n in graph.nodes} == {"trade_ai_agent"}
        assert {n.capability for n in graph.nodes} == {"prospect.scrape", "outreach.whatsapp", "inbox.classify"}

    def test_social_graph_passes_safety_valves(self):
        from app.services.hermes.planner_service import validate_graph

        graph, source = _decompose("社媒找客户并发 WhatsApp", {"message": "门窗供应商"})
        assert source == "L1_template"
        assert validate_graph(graph) == []  # 无未注册执行器/能力、无环

    def test_whatsapp_requires_approval(self):
        graph, source = _decompose("社交媒体私域触达", {"message": "推广落地页"})
        assert source == "L1_template"
        assert "outreach.whatsapp" in graph.policies.approval_required  # 触达类挂起等人审
        n = {node.id: node for node in graph.nodes}
        assert n["n2"].depends_on == ["n1"]  # 先挖潜客，再 WhatsApp 触达


def test_fulfillment_graph_covers_all_7_steps():
    """验证 _fulfillment_graph 完整覆盖外贸 7 步闭环（8 节点：含 CRM 阶段推进）。"""
    from app.services.hermes.planner_service import _fulfillment_graph

    g = _fulfillment_graph("p", "e", {})
    caps = {n.capability for n in g.nodes}
    # ①询盘→②建单→③PI→④定金→⑤CRM→⑥CI/PL→⑦物流→⑧尾款
    assert "inquiry.capture" in caps  # ①询盘捕获
    assert "order.create" in caps  # ②建单
    assert "document.generate_pi" in caps  # ③形式发票 PI
    assert "billing.meter" in caps  # ④定金 + ⑧尾款（同能力，不同 event_type）
    assert "crm.sync_stage" in caps  # ⑤CRM 阶段推进
    assert "document.generate_trade_docs" in caps  # ⑥发运单证 CI/PL
    assert "logistics.track" in caps  # ⑦物流可查
    assert len(g.nodes) == 9  # 8 业务节点 + PI 前风控 trade_ops.pi_precheck


def test_order_status_machine_includes_deposit_and_final_payment():
    """验证订单状态机包含定金/尾款核销节点，且跃迁有向。"""
    from app.models.enums import OrderStatus

    # 新状态存在
    assert OrderStatus.DEPOSIT_RECEIVED.value == "deposit_received"
    assert OrderStatus.FINAL_PAYMENT_RECEIVED.value == "final_payment_received"
    # 合法跃迁
    assert OrderStatus.is_valid_transition("confirmed", "deposit_received")  # ④定金核销
    assert OrderStatus.is_valid_transition("deposit_received", "in_production")  # 定金→生产
    assert OrderStatus.is_valid_transition("shipped", "final_payment_received")  # ⑦尾款核销
    assert OrderStatus.is_valid_transition("final_payment_received", "completed")  # 尾款→完成
    # 兼容旧路径（跳过定金/尾款）
    assert OrderStatus.is_valid_transition("confirmed", "in_production")  # 预付款客户
    assert OrderStatus.is_valid_transition("shipped", "completed")  # 全款预付
    # 非法反向跃迁
    assert not OrderStatus.is_valid_transition("deposit_received", "confirmed")
    assert not OrderStatus.is_valid_transition("inal_payment_received", "shipped")

