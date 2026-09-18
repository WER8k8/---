"""未驱动执行器串联测试：12 个此前未挂 L1 模板的执行器现被 6 个新模板驱动。

覆盖：product / media / seo / engagement / research / wangcai / ai_engine /
      lead / billing / browser / forum / ubrain。
"""
from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

from app.schemas.hermes_orchestration import IntentEvent


def _decompose(intent: str, payload: dict):
    from app.services.hermes.planner_service import decompose

    ev = IntentEvent(event_id="e1", tenant_id="t1", channel="api", intent=intent, payload=payload)
    return asyncio.run(decompose(ev, MagicMock()))


class TestProductLaunch:
    """产品上架 → 媒体素材 → SEO → 社媒触达。"""

    def test_product_intent_resolves_to_l1(self):
        graph, source = _decompose("发布新产品", {"title": "Building Materials", "keyword": "cement"})
        assert source == "L1_template"
        assert {n.executor for n in graph.nodes} == {"product", "media", "seo", "engagement"}

    def test_product_graph_passes_safety_valves(self):
        from app.services.hermes.planner_service import validate_graph

        graph, source = _decompose("产品上架", {"title": "Steel Beams"})
        assert source == "L1_template"
        assert validate_graph(graph) == []

    def test_engagement_requires_approval(self):
        graph, source = _decompose("发布产品并触达客户", {"title": "Windows"})
        assert source == "L1_template"
        assert "engagement.send" in graph.policies.approval_required


class TestResearchAnalysis:
    """市场研析 → 海关数据 → AI 推理。"""

    def test_market_analysis_intent_resolves_to_l1(self):
        graph, source = _decompose("市场分析", {"topic": "Building materials export"})
        assert source == "L1_template"
        assert {n.executor for n in graph.nodes} >= {
            "research",
            "wangcai",
            "ai_engine",
            "module_matrix",
            "commerce_ops",
            "platform_ops",
            "content_deep",
            "outreach_loop",
        }

    def test_research_analysis_passes_safety_valves(self):
        from app.services.hermes.planner_service import validate_graph

        graph, source = _decompose("海关数据查询", {"topic": "Cement export feasibility"})
        assert source == "L1_template"
        assert validate_graph(graph) == []

    def test_ai_reasoning_depends_on_research_and_wangcai(self):
        graph, source = _decompose("出口可行性分析", {"topic": "Steel"})
        assert source == "L1_template"
        n = {node.id: node for node in graph.nodes}
        assert n["n3"].capability == "ai.reason"
        assert set(n["n3"].depends_on) == {"n1", "n2"}


class TestLeadGeneration:
    """Geo 拓客 → 线索评分 → 计费计量。"""

    def test_lead_gen_intent_resolves_to_l1(self):
        graph, source = _decompose("找线索", {"industry": "Construction", "country": "USA"})
        assert source == "L1_template"
        assert {n.executor for n in graph.nodes} == {"lead", "billing"}

    def test_lead_generation_passes_safety_valves(self):
        from app.services.hermes.planner_service import validate_graph

        graph, source = _decompose("线索搜索", {"industry": "Materials"})
        assert source == "L1_template"
        assert validate_graph(graph) == []

    def test_billing_meters_lead_generation(self):
        graph, source = _decompose("拓客搜索", {"industry": "Steel"})
        assert source == "L1_template"
        n = {node.id: node for node in graph.nodes}
        assert n["n3"].capability == "billing.meter"
        assert n["n3"].depends_on == ["n2"]


class TestBrowserEvidence:
    """网页取证 → 论坛发帖。"""

    def test_browser_evidence_intent_resolves_to_l1(self):
        graph, source = _decompose("网页取证", {"url": "https://example.com"})
        assert source == "L1_template"
        assert {n.executor for n in graph.nodes} == {"browser", "forum"}

    def test_browser_evidence_passes_safety_valves(self):
        from app.services.hermes.planner_service import validate_graph

        graph, source = _decompose("抓取网页", {"url": "https://test.com"})
        assert source == "L1_template"
        assert validate_graph(graph) == []

    def test_forum_post_depends_on_browser_scrape(self):
        graph, source = _decompose("爬虫抓取", {"url": "https://research.com"})
        assert source == "L1_template"
        n = {node.id: node for node in graph.nodes}
        assert n["n2"].capability == "forum.post"
        assert n["n2"].depends_on == ["n1"]


class TestUBrainAssistant:
    """UBrain 统一助手：意图检测 → AI 推理。"""

    def test_ubrain_intent_resolves_to_l1(self):
        graph, source = _decompose("智能助手", {"message": "How to export cement?"})
        assert source == "L1_template"
        assert {n.executor for n in graph.nodes} == {"ubrain", "ai_engine"}

    def test_ubrain_passes_safety_valves(self):
        from app.services.hermes.planner_service import validate_graph

        graph, source = _decompose("问答", {"message": "What is HS code?"})
        assert source == "L1_template"
        assert validate_graph(graph) == []

    def test_ai_chat_depends_on_ubrain(self):
        graph, source = _decompose("助手问答", {"message": "Export feasibility"})
        assert source == "L1_template"
        n = {node.id: node for node in graph.nodes}
        assert n["n2"].capability == "ai.chat"
        assert n["n2"].depends_on == ["n1"]


def test_all_registered_executors_now_driven():
    """防回归：所有已注册执行器必须被至少一个 L1 模板驱动（排除测试夹具）。"""
    from app.services.hermes.executors import ExecutorRegistry
    import inspect
    import re
    from app.services.hermes import planner_service as ps

    src = inspect.getsource(ps)
    driven = set(re.findall(r'executor="([a-z_]+)"', src))
    registered = set(ExecutorRegistry.list_executors())
    # 排除测试夹具（fake_p0_executor 是 test_hermes_dag_p0.py 注册的 mock）
    test_fixtures = {"fake_p0_executor"}
    undriven = registered - driven - test_fixtures
    assert not undriven, f"以下执行器已注册但未被 L1 模板驱动: {sorted(undriven)}"
