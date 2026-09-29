# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Hermes 执行器测试 —— trade_ai_agent / goodjob_crm（native + 技能批双路径）。

2026-09-27 重写：旧文件按已废弃的外桥 HTTP 契约（base_url + requests.post +
deal.create / pi.send_whatsapp）编写，native 化后构造签名失效 —— 5 个用例自
native 化起即无法运行。现按当前真实契约重写：
  · trade_ai_agent：技能批适配器（services/adapters/tradeai）优先 + 原生单发兜底
  · goodjob_crm：原生能力集（trade.docs / document.generate_* / crm.*）
run() 行为验证 = patch 目标服务 + asyncio.run，不依赖 pytest-asyncio 插件。
"""
import asyncio
from unittest.mock import Mock, patch
import pytest
from sqlalchemy.orm import Session

from app.services.hermes.executors.trade_ai_agent_executor import TradeAiAgentExecutor
from app.services.hermes.executors.goodjob_crm_executor import GoodJobCrmExecutor
from app.services.hermes.executors.base import ExecutorContext, ExecutorRegistry
from app.schemas.hermes_orchestration import TaskNode


def _node(capability: str, payload: dict | None = None, executor: str = "trade_ai_agent") -> TaskNode:
    return TaskNode(
        id="node_1",
        executor=executor,
        capability=capability,
        input=payload or {},
        sop_ref="",
        depends_on=[],
    )


def _context() -> ExecutorContext:
    return ExecutorContext(db=Mock(spec=Session), tenant_id="test_tenant", plan_id="test_plan")


class TestTradeAiAgentExecutor:
    """TradeAI 原生拓客执行器（检索 / 触达 / 分类；无 Key 诚实 failed）"""

    def test_executor_name(self):
        assert TradeAiAgentExecutor().get_executor_name() == "trade_ai_agent"

    def test_capability_completeness(self):
        caps = TradeAiAgentExecutor().get_capabilities()
        assert set(caps) == {"prospect.scrape", "outreach.whatsapp", "outreach.email", "inbox.classify"}
        for name, spec in caps.items():
            assert {"desc", "input", "output", "cost", "needs_approval"} <= set(spec), name
            assert {"tokens", "seconds"} <= set(spec["cost"]), name

    def test_approval_flags(self):
        caps = TradeAiAgentExecutor().get_capabilities()
        # 外联需人审；检索/分类不需
        assert caps["outreach.whatsapp"]["needs_approval"] is True
        assert caps["outreach.email"]["needs_approval"] is True
        assert caps["prospect.scrape"]["needs_approval"] is False
        assert caps["inbox.classify"]["needs_approval"] is False

    def test_unknown_capability_skipped_not_failed(self):
        result = asyncio.run(TradeAiAgentExecutor().run(_node("unknown.capability"), _context()))
        assert result.status == "skipped"

    def test_prospect_scrape_passes_through_native_result(self):
        with patch(
            "app.services.tradeai.native_acquisition.prospect_scrape",
            return_value={"success": True, "prospects": [{"id": "p1"}], "hit_count": 1},
        ) as mock_scrape:
            result = asyncio.run(
                TradeAiAgentExecutor().run(
                    _node("prospect.scrape", {"keyword": "tile", "country": "UAE"}),
                    _context(),
                )
            )
        assert result.status == "succeeded"
        assert result.output["hit_count"] == 1
        assert result.output["executor"] == "trade_ai_agent"
        mock_scrape.assert_called_once()

    def test_whatsapp_unconfigured_is_honest_failed(self):
        with patch(
            "app.services.tradeai.native_acquisition.outreach_whatsapp",
            return_value={"success": False, "error": "whatsapp_not_configured"},
        ):
            result = asyncio.run(
                TradeAiAgentExecutor().run(
                    _node("outreach.whatsapp", {"whatsapp": "+1000000000", "message": "hi"}),
                    _context(),
                )
            )
        assert result.status == "failed"
        assert "whatsapp_not_configured" in result.error

    def test_inbox_classify_success(self):
        with patch(
            "app.services.tradeai.native_acquisition.classify_inbox",
            return_value={"success": True, "detected_intent": "RFQ"},
        ):
            result = asyncio.run(
                TradeAiAgentExecutor().run(
                    _node("inbox.classify", {"message": "please quote 100 sqm tiles"}),
                    _context(),
                )
            )
        assert result.status == "succeeded"
        assert result.output["detected_intent"] == "RFQ"


class TestGoodJobCrmExecutor:
    """GoodJob CRM 原生履约执行器（7 步状态机 / PI / 单证；写优丁 PG）"""

    # 原生能力集（目录桥能力 goodjob_crm.<family> 由共享目录派生，不在本测试断言范围）
    _NATIVE_CAPS = (
        "trade.docs",
        "document.generate_pi",
        "document.generate_trade_docs",
        "crm.sync_stage",
        "crm.sync_lead",
        "crm.update_opportunity",
    )

    def test_executor_name(self):
        assert GoodJobCrmExecutor().get_executor_name() == "goodjob_crm"

    def test_native_capability_completeness(self):
        caps = GoodJobCrmExecutor().get_capabilities()
        for name in self._NATIVE_CAPS:
            assert name in caps, name
        for name in self._NATIVE_CAPS:
            spec = caps[name]
            assert {"desc", "input", "output", "cost", "needs_approval"} <= set(spec), name
            assert {"tokens", "seconds"} <= set(spec["cost"]), name

    def test_document_capabilities_require_approval(self):
        caps = GoodJobCrmExecutor().get_capabilities()
        # 单证/财务类需人审；阶段/建档同步不需
        assert caps["trade.docs"]["needs_approval"] is True
        assert caps["document.generate_pi"]["needs_approval"] is True
        assert caps["document.generate_trade_docs"]["needs_approval"] is True
        assert caps["crm.sync_stage"]["needs_approval"] is False
        assert caps["crm.sync_lead"]["needs_approval"] is False


class TestExecutorRegistryIntegration:
    """执行器注册表集成测试"""

    def test_native_registration(self):
        assert ExecutorRegistry.has("trade_ai_agent")
        assert isinstance(ExecutorRegistry.get("trade_ai_agent"), TradeAiAgentExecutor)
        assert ExecutorRegistry.has("goodjob_crm")
        assert isinstance(ExecutorRegistry.get("goodjob_crm"), GoodJobCrmExecutor)

    def test_capabilities_aggregation(self):
        all_caps = ExecutorRegistry.all_capabilities()
        assert "prospect.scrape" in all_caps
        assert all_caps["prospect.scrape"]["executor"] == "trade_ai_agent"
        assert "document.generate_pi" in all_caps
        assert all_caps["document.generate_pi"]["executor"] == "goodjob_crm"

    def test_executor_list(self):
        executors = ExecutorRegistry.list_executors()
        assert "trade_ai_agent" in executors
        assert "goodjob_crm" in executors
        assert "accio" in executors
        assert "deerflow" in executors

    def test_skill_batch_adapter_available(self):
        """修正设计稿模块7.3前提订正：services/adapters/tradeai 是在用技能批适配器（非死链），可导入"""
        from app.services.adapters import tradeai  # noqa: F401

        assert hasattr(tradeai, "is_available")
        assert hasattr(tradeai, "tenant_orchestrator")


class TestCapabilityValidation:
    """能力契约校验"""

    def test_trade_ai_agent_capability_contract(self):
        executor = TradeAiAgentExecutor()
        caps = executor.get_capabilities()
        for cap_name, cap_spec in caps.items():
            assert "desc" in cap_spec, f"{cap_name} missing desc"
            assert "input" in cap_spec, f"{cap_name} missing input"
            assert "output" in cap_spec, f"{cap_name} missing output"
            assert "cost" in cap_spec, f"{cap_name} missing cost"
            assert "needs_approval" in cap_spec, f"{cap_name} missing needs_approval"
            assert "tokens" in cap_spec["cost"], f"{cap_name} cost missing tokens"
            assert "seconds" in cap_spec["cost"], f"{cap_name} cost missing seconds"


# 运行测试的便捷函数
def run_adapter_tests():
    """运行适配器集成测试"""
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_adapter_tests()
