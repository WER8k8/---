# -*- coding: utf-8 -*-
"""对标阿里国际 Accio Work 复刻能力的回归测试（不连真库、不打真 LLM）。

覆盖 2026-09-14 新增的两条能力链与其接线点：
  1. 技能层：market_insight / supplier_compare 必须注册，且 prompt 占位符
     与 input_schema 完全一致（少一个键就是运行期 KeyError）。
  2. DeerFlow 层：两个 intent 必须走专属处理函数，不许掉进 _exec_generic 兜底。
  3. 诚实纪律：缺必填参数必须 degraded=True 且带真实原因，不得假成功。
  4. 编排层：market_intelligence 模板存在，且 job payload 会合并进子任务参数
     （这条同时修掉旧模板永远拿到空 parameters 的 bug）。
  5. Hermes 层：能力名翻译成 intent，且声明与映射表一致。
"""
from __future__ import annotations

import json
import re
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.deerflow.executor import SubTaskExecutor
from app.services.deerflow.planner import SubTask, TaskPlanner
from app.services.foreign_trade import skill_registry
from app.services.foreign_trade import market_insight_skill, supplier_compare_skill
from app.services.hermes.executors.deerflow_executor import _CAPABILITY_TO_INTENT

NEW_SKILLS = {
    "market_insight": market_insight_skill.MARKET_INSIGHT_META,
    "supplier_compare": supplier_compare_skill.SUPPLIER_COMPARE_META,
}


def _executor() -> SubTaskExecutor:
    """构造一个只用于派发逻辑的执行器（DB/job 全是假的，不触库）。"""
    return SubTaskExecutor(db=MagicMock(), job=MagicMock(id="job-1", tenant_id="t-1"))


def _placeholders(meta) -> set[str]:
    """取出 prompt_template 里 {field} 形式的占位符（忽略 {{ }} 转义）。"""
    return set(re.findall(r"(?<!\{)\{([a-zA-Z_][a-zA-Z0-9_]*)\}(?!\})", meta.prompt_template))


# ── 1. 技能层 ────────────────────────────────────────────────
@pytest.mark.parametrize("name", sorted(NEW_SKILLS))
def test_skill_is_registered(name):
    assert skill_registry.get(name) is not None, f"{name} 未注册进 skill_registry"


@pytest.mark.parametrize("name,meta", sorted(NEW_SKILLS.items(), key=lambda kv: kv[0]))
def test_prompt_placeholders_match_input_schema(name, meta):
    """占位符必须全部在 input_schema 里，否则 format(**params) 直接 KeyError。"""
    assert _placeholders(meta) <= set(meta.input_schema), (
        f"{name} prompt 用了 schema 之外的占位符: {_placeholders(meta) - set(meta.input_schema)}"
    )


@pytest.mark.parametrize("name,meta", sorted(NEW_SKILLS.items(), key=lambda kv: kv[0]))
def test_required_fields_cover_all_placeholders(name, meta):
    """每个占位符都得有默认值或必填，保证调用方只给必填也能 format 成功。"""
    for field in _placeholders(meta):
        spec = meta.input_schema[field]
        assert spec.get("required") or "default" in spec, f"{name}.{field} 既非必填也无默认值"


def test_skills_mark_output_as_needing_verification():
    """诚实纪律：两条能力都必须要求人工核实，不得把模型推断写成事实。"""
    for name, meta in NEW_SKILLS.items():
        assert "confidence" in meta.prompt_template, f"{name} 缺 confidence"
        assert "verification_required" in meta.prompt_template, f"{name} 缺 verification_required"
        assert "disclaimer" in meta.prompt_template, f"{name} 缺 disclaimer"


# ── 2/3. DeerFlow 派发与降级 ─────────────────────────────────
@pytest.mark.parametrize("intent", sorted(NEW_SKILLS))
def test_new_intents_hit_dedicated_handlers(intent):
    fake_self = MagicMock(spec=SubTaskExecutor)
    subtask = SubTask(id="s1", title="t", intent=intent, agent_ref="", parameters={})

    SubTaskExecutor._dispatch_by_intent(fake_self, subtask)

    fake_self._exec_generic.assert_not_called()
    assert getattr(fake_self, f"_exec_{intent}").called, f"{intent} 没走到专属处理函数"


@pytest.mark.parametrize(
    "intent,params",
    [
        ("market_insight", {"category": "岩棉板"}),
        ("market_insight", {}),
        ("supplier_compare", {"category": "岩棉板", "target_market": "沙特"}),
        ("supplier_compare", {"target_market": "沙特", "candidates": "A 公司"}),
    ],
)
def test_missing_required_params_degrade_honestly(intent, params):
    """缺必填必须显式降级并给出真实原因，不能报假成功。"""
    result = _executor()._dispatch_by_intent(
        SubTask(id="s1", title="t", intent=intent, agent_ref="", parameters=params)
    )

    assert result["degraded"] is True
    assert result["status"] == "completed", "单子任务降级不应连坐整条计划"
    assert "缺少必填参数" in result["reason"]


def test_market_insight_returns_skill_payload():
    from app.services.foreign_trade.skill_registry import SkillResult

    fake = SkillResult(success=True, data={"confidence": "中"}, skill_name="market_insight",
                       model_used="deepseek-chat", tokens_used=123)
    with patch.object(skill_registry, "execute", new=AsyncMock(return_value=fake)):
        result = _executor()._exec_market_insight(
            {"category": "岩棉板", "target_market": "沙特"}
        )

    assert result["degraded"] is False
    assert result["insight"] == {"confidence": "中"}
    assert result["tokens_used"] == 123
    # 模型推断必须带待核实标记透出，不许当既成事实
    assert result["human_verify_required"] is True


def test_supplier_compare_accepts_candidate_list():
    from app.services.foreign_trade.skill_registry import SkillResult

    captured: dict = {}

    async def _capture(name, params):
        captured["name"] = name
        captured["params"] = params
        return SkillResult(success=True, data={"ranking": []}, skill_name=name)

    with patch.object(skill_registry, "execute", new=_capture):
        result = _executor()._exec_supplier_compare({
            "category": "岩棉板",
            "target_market": "沙特",
            "candidates": ["A 公司：报价低、无 EN 认证", {"name": "B 公司", "moq": "未披露"}],
        })

    assert captured["name"] == "supplier_compare"
    assert result["candidate_count"] == 2
    # 列表要拍平成多行文本，且非字符串项要能序列化而不是报错
    assert "A 公司" in captured["params"]["candidates"]
    assert "未披露" in captured["params"]["candidates"]


def test_skill_failure_degrades_with_real_reason():
    from app.services.foreign_trade.skill_registry import SkillResult

    fake = SkillResult(success=False, error="AI 服务未配置")
    with patch.object(skill_registry, "execute", new=AsyncMock(return_value=fake)):
        result = _executor()._exec_market_insight({"category": "岩棉板", "target_market": "沙特"})

    assert result["degraded"] is True
    assert "AI 服务未配置" in result["reason"]


# ── 4. 编排层 ────────────────────────────────────────────────
def test_market_intelligence_template_shape():
    template = TaskPlanner._TEMPLATES.get("market_intelligence")
    assert template, "缺 market_intelligence 编排模板"
    intents = [d["intent"] for d in template]
    assert intents == ["market_insight", "supplier_compare", "keyword_research"]


def test_template_subtasks_inherit_job_payload():
    """回归护栏：模板子任务必须继承 job payload，否则必填参数永远拿不到。"""
    job = MagicMock(
        id="job-1",
        intent="market_intelligence",
        payload_json=json.dumps({"category": "岩棉板", "target_market": "沙特", "context": {"x": 1}}),
    )

    plan = TaskPlanner(db=MagicMock()).create_plan(job)

    first = plan.subtasks[0]
    assert first.parameters["category"] == "岩棉板"
    assert first.parameters["target_market"] == "沙特"
    assert "context" not in first.parameters, "内部上下文字典不该渗进技能参数"


def test_bad_payload_does_not_break_planning():
    job = MagicMock(id="job-2", intent="market_intelligence", payload_json="{not json")

    plan = TaskPlanner(db=MagicMock()).create_plan(job)

    assert len(plan.subtasks) == 3


# ── 5. Hermes 层 ─────────────────────────────────────────────
@pytest.mark.parametrize(
    "capability,intent",
    [("research.market_insight", "market_insight"), ("research.supplier_compare", "supplier_compare")],
)
def test_hermes_capability_translates_to_intent(capability, intent):
    assert _CAPABILITY_TO_INTENT.get(capability) == intent


def test_declared_capabilities_stay_inside_mapping():
    """与既有契约测试同口径：声明的能力必须都在映射表里，planner 才不会漏。"""
    from app.services.hermes.executors.deerflow_executor import DeerflowExecutor

    declared = set(DeerflowExecutor.get_capabilities().keys())
    assert declared <= set(_CAPABILITY_TO_INTENT)


# ── 6. UBrain 副驾自然语言入口 ───────────────────────────────
from app.services.ubrain.orchestrator import (  # noqa: E402
    UBrainOrchestrator,
    _extract_insight_subject,
)


@pytest.mark.parametrize(
    "message,expected",
    [
        ("岩棉板出口沙特，做个市场洞察", "market_insight"),
        ("帮我对比 A 公司、B 公司这两家供应商", "supplier_compare"),
        ("compare suppliers for rock wool in Saudi", "supplier_compare"),
        # 回归护栏：老说法必须留在原路由，不能被新能力抢走
        ("做一份市场研究", "market_research"),
        ("岩棉板能出口越南吗", "export_feasibility"),
    ],
)
def test_intent_routing(message, expected):
    assert UBrainOrchestrator().detect_intent(message) == expected


def test_subject_extraction_does_not_invent():
    """抽不到就不编：品类/市场/候选缺失时返回空，交给调用方追问。"""
    subject = _extract_insight_subject("随便看看")
    assert subject["target_market"] == ""
    assert subject["candidates"] == ""

    listed = _extract_insight_subject("对比 沙特 的 华美公司、洛克wool集团、ABX Ltd 做岩棉板供应商")
    assert listed["target_market"] == "沙特"
    assert len(listed["candidates"].splitlines()) == 3


@pytest.mark.parametrize(
    "message,expected_market",
    [
        ("岩棉板 印度尼西亚 市场洞察", "印度尼西亚"),
        ("岩棉板 沙特阿拉伯 市场洞察", "沙特阿拉伯"),
        ("岩棉板 马来西亚 市场洞察", "马来西亚"),
        ("岩棉板 出口印度 市场洞察", "印度"),
    ],
)
def test_longest_market_alias_wins(message, expected_market):
    """长地名必须优先于其短前缀命中，不能被切成半截名字。"""
    assert _extract_insight_subject(message)["target_market"] == expected_market


def test_missing_subject_asks_instead_of_enqueueing():
    """缺参数时不得入队烧 token，必须回一句要什么。"""
    orch = UBrainOrchestrator()
    with patch("app.services.ubrain.orchestrator.enqueue_job") as enq:
        reply, result = orch._handle_accio_replica_intent(
            "market_insight", "做个市场洞察", {}, MagicMock(), "tenant-1"
        )

    enq.assert_not_called()
    assert result["available"] is False
    assert set(result["missing_params"]) == {"品类", "目标市场"}
    assert "品类" in reply


def test_no_tenant_short_circuits():
    orch = UBrainOrchestrator()
    with patch("app.services.ubrain.orchestrator.enqueue_job") as enq:
        reply, result = orch._handle_accio_replica_intent(
            "market_insight", "岩棉板 沙特 市场洞察", {}, MagicMock(), None
        )

    enq.assert_not_called()
    assert result["available"] is False
    assert "租户" in reply


def test_degraded_result_is_reported_as_unfinished():
    """执行器降级时必须回「未完成 + 原因」，不许把降级粉饰成成功。"""
    orch = UBrainOrchestrator()
    job = MagicMock(id="job-abcdef12345")
    ran = {"status": "success", "result": {"degraded": True, "reason": "AI 服务未配置"}}
    with patch("app.services.ubrain.orchestrator.enqueue_job", return_value=job), patch(
        "app.services.ubrain.orchestrator.run_job", return_value=ran
    ):
        reply, result = orch._handle_accio_replica_intent(
            "market_insight", "岩棉板 沙特 市场洞察", {"sync": True}, MagicMock(), "tenant-1"
        )

    assert "未完成" in reply
    assert "AI 服务未配置" in reply
    assert result["job_status"] == "success"


def test_successful_insight_surfaces_confidence_and_verification():
    orch = UBrainOrchestrator()
    job = MagicMock(id="job-abcdef12345")
    ran = {
        "status": "success",
        "result": {
            "degraded": False,
            "insight": {"confidence": "中", "verification_required": ["核实 SASO 版本", "核实价格带"]},
        },
    }
    with patch("app.services.ubrain.orchestrator.enqueue_job", return_value=job), patch(
        "app.services.ubrain.orchestrator.run_job", return_value=ran
    ):
        reply, result = orch._handle_accio_replica_intent(
            "market_insight", "岩棉板 沙特 市场洞察", {"sync": True}, MagicMock(), "tenant-1"
        )

    assert "置信度 中" in reply
    assert "待人工核实 2 项" in reply
    assert result["job_id"] == "job-abcdef12345"
