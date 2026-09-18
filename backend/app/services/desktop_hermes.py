# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Desktop Hermes 外层（DSH）—— 蓝图落地：意图解构 + Skill 插座 + 组装调度。

公式（总案）：
    外层 DSH（意图+技能）→ 内层 Hermes（DAG）→ 可变编排路线 → 业务执行器
    × 获客莫比乌斯（经验反哺）× 商业正循环 × AEOS 八大子系统
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from app.services.aeos_registry import aeos_invoke_map, aeos_registry_report


# 四航道场景库（蓝图阶段 4：A 研报 / B 拓客 / C 履约 / D 复合）
SCENE_REGISTRY: Dict[str, Dict[str, Any]] = {
    "lane_a_research": {
        "name": "航道A 研报与SEO",
        "intents": ["deep_research", "市场分析", "research_analysis"],
        "plain": "产品/市场深研 → 内容/SEO",
        "executors": ["deerflow", "research", "wangcai", "ai_engine", "content_deep"],
    },
    "lane_b_outreach": {
        "name": "航道B 社媒拓客",
        "intents": ["find_leads", "whatsapp", "社媒拓客", "outreach"],
        "plain": "找客 → 背调 → 人审触达 → 意图分类",
        "executors": ["lead", "accio", "trade_ai_agent", "outreach_loop", "commerce_ops"],
    },
    "lane_c_fulfillment": {
        "name": "航道C 履约单证",
        "intents": ["fulfillment", "形式发票", "order_fulfill", "generate_pi"],
        "plain": "询盘→订单→PI→定金→CRM→单证→物流→尾款",
        "executors": ["inquiry", "order", "trade_ops", "goodjob_crm", "billing", "logistics"],
    },
    "lane_d_composite": {
        "name": "航道D 复合超导",
        "intents": ["composite", "复合超导", "全链路", "super_flow"],
        "plain": "调研+拓客+报价风险闸+计量 一条图跑通",
        "executors": ["deerflow", "lead", "accio", "trade_ops", "billing", "desktop_hermes"],
    },
    "lane_aeos": {
        "name": "AEOS 全域体检",
        "intents": ["aeos_readiness", "aeos", "系统体检", "八大子系统"],
        "plain": "八大子系统代码面 + 业务调用路径体检",
        "executors": ["desktop_hermes", "biz_bot", "platform_ops"],
    },
    "lane_module_robots": {
        "name": "全模块业务机器人",
        "intents": ["module_robot", "业务机器人", "module_batch"],
        "plain": "批量把路由模块升成业务机器人",
        "executors": ["biz_bot", "module_matrix"],
    },
}


class DesktopHermes:
    """外层 Desktop Hermes：万能皆可插的意图/技能中枢。"""

    def __init__(self) -> None:
        self.skills: Dict[str, Dict[str, Any]] = {}
        self._load_default_skills()

    def _load_default_skills(self) -> None:
        for sid, spec in {
            "skill.acquisition_mobius": {
                "name": "获客莫比乌斯链",
                "intents": ["find_leads", "fulfillment", "whatsapp", "inquiry_reply"],
                "plain": "线索→背调→人审触达→询盘→跟单→经验环",
            },
            "skill.tender_dealer": {
                "name": "经销商/招投标",
                "intents": ["dealer_tender", "tender"],
                "plain": "资质包→风险闸→投标→评标",
            },
            "skill.compliance_gate": {
                "name": "合规闸门",
                "intents": ["risk_scan", "compliance", "risk_compliance"],
                "plain": "制裁筛查/退订/付款风险",
            },
            "skill.content_seo": {
                "name": "内容与SEO",
                "intents": ["content_acquisition", "generate_site", "deep_research"],
                "plain": "建站内容→分发→归因",
            },
            "skill.billing_ops": {
                "name": "计费与钱包",
                "intents": ["billing_ops", "billing", "token"],
                "plain": "三轨账单大白话 + Token 真账本",
            },
            "skill.composite_super": {
                "name": "复合超导航道D",
                "intents": ["composite", "super_flow", "复合超导"],
                "plain": "调研+拓客+风险闸+计量一条图",
            },
            "skill.aeos_readiness": {
                "name": "AEOS 八大子系统",
                "intents": ["aeos_readiness", "aeos", "八大子系统"],
                "plain": "SYSTEM-LOCK-02 体检与业务调用",
            },
            "skill.module_robot": {
                "name": "全模块业务机器人",
                "intents": ["module_robot", "业务机器人", "module_batch"],
                "plain": "157 路由模块业务动作全覆盖",
            },
        }.items():
            self.skills[sid] = spec
        # 挂接场景库元数据
        self.scenes = dict(SCENE_REGISTRY)

    def register_skill(self, skill_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        if not skill_id:
            return {"ok": False, "message": "skill_id required"}
        self.skills[skill_id] = spec
        return {"ok": True, "skill_id": skill_id, "count": len(self.skills)}

    def list_skills(self) -> List[Dict[str, Any]]:
        return [{"id": k, **v} for k, v in self.skills.items()]

    def list_scenes(self) -> List[Dict[str, Any]]:
        return [{"id": k, **v} for k, v in SCENE_REGISTRY.items()]

    def recall_skills(self, intent: str) -> List[Dict[str, Any]]:
        out = []
        intent_l = (intent or "").lower()
        for sid, spec in self.skills.items():
            intents = [str(x).lower() for x in spec.get("intents") or []]
            if not intent_l or intent_l in intents or any(intent_l in i for i in intents):
                out.append({"id": sid, **spec})
        # 场景也进召回（万能皆可插）
        for sid, spec in SCENE_REGISTRY.items():
            intents = [str(x).lower() for x in spec.get("intents") or []]
            if intent_l and (intent_l in intents or any(intent_l in i for i in intents)):
                out.append({"id": sid, "kind": "scene", **spec})
        return out

    def decompose_intent(self, intent: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """DSH 意图解构：技能召回 + 场景匹配 + 交给内层 Hermes planner。"""
        payload = dict(payload or {})
        recalled = self.recall_skills(intent)
        scenes = [s for s in recalled if s.get("kind") == "scene"]
        return {
            "intent": intent,
            "skill_refs": recalled,
            "scene_refs": scenes,
            "payload_keys": list(payload.keys()),
            "outer_layer": "DSH/DesktopHermes",
            "next": "hermes.decompose",
            "formula": "DSH外层(意图+技能) → 爱马仕内层DAG → 可变编排插件",
        }

    async def assemble_plan(
        self,
        intent: str,
        payload: Optional[Dict[str, Any]] = None,
        db: Any = None,
        tenant_id: str = "demo",
    ) -> Dict[str, Any]:
        """外层组装 → 内层 Hermes 出任务图（真 planner）。"""
        payload = dict(payload or {})
        outer = self.decompose_intent(intent, payload)
        try:
            from app.schemas.hermes_orchestration import IntentEvent
            from app.services.hermes import planner_service as ps

            ev = IntentEvent(
                event_id=f"dsh-{uuid.uuid4().hex[:10]}",
                tenant_id=tenant_id,
                channel="desktop_hermes",
                intent=intent,
                payload={**payload, "_skill_refs": outer["skill_refs"]},
            )
            graph, source = await ps.decompose(ev, db)
            return {
                **outer,
                "plan_id": graph.plan_id,
                "source": source,
                "nodes": [
                    {"id": n.id, "executor": n.executor, "capability": n.capability}
                    for n in graph.nodes
                ],
                "approval_required": list(graph.policies.approval_required or []),
                "l1_template_count": len(getattr(ps, "_TEMPLATES", [])),
                "aeos": aeos_registry_report(),
                "ok": True,
            }
        except Exception as exc:  # noqa: BLE001
            return {**outer, "ok": False, "error": str(exc)[:200]}

    def mobius_feedback(self, *, intent: str, success: bool, note: str = "") -> Dict[str, Any]:
        """莫比乌斯经验环：外层收到结果后标记（真源仍走 Evolution PG）。"""
        for sid, spec in self.skills.items():
            if intent in [str(x).lower() for x in spec.get("intents") or []]:
                spec["last_result"] = {"intent": intent, "success": success, "note": note}
                spec["weight"] = float(spec.get("weight") or 1.0) + (0.05 if success else -0.05)
        return {
            "ok": True,
            "intent": intent,
            "success": success,
            "hint": "外层权重仅作提示；正式经验以 Evolution PG 为真源",
            "skills": self.recall_skills(intent),
        }

    def aeos_invoke_map(self) -> Dict[str, Any]:
        return aeos_invoke_map()

    def status(self) -> Dict[str, Any]:
        report = aeos_registry_report()
        try:
            from app.services.hermes.executors import ExecutorRegistry
            from app.services.hermes import planner_service as ps

            executors = sorted(ExecutorRegistry.list_executors())
            templates = len(getattr(ps, "_TEMPLATES", []))
        except Exception:
            executors, templates = [], 0
        return {
            "name": "DesktopHermes",
            "slogan": "万能皆可插",
            "skills": len(self.skills),
            "scenes": len(SCENE_REGISTRY),
            "l1_templates": templates,
            "executors": len(executors),
            "aeos_ready": report.get("ready_count"),
            "layers": ["DSH外层", "Hermes内层DAG", "执行器矩阵", "经验环", "AEOS八大子系统"],
            "milestones": {
                "M1_零件齐套": bool(executors) and report.get("ready_count", 0) >= 8,
                "M2_模板航道": templates >= 8,
                "M3_动态拆解_Skill注入": True,
                "M4_场景库": len(SCENE_REGISTRY) >= 4,
            },
        }


desktop_hermes = DesktopHermes()
