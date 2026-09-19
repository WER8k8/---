# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""B2B Outreach and Lead Gen Scenario Template.

【已弃用 / DEPRECATED】planner 不消费本模板；保留仅供历史对照。
权威 L1 模板见 `app.services.hermes.planner_service`（勿在此扩展执行器）。
"""
from typing import Dict, Any
from app.schemas.hermes_orchestration import TaskGraph, TaskNode, GraphPolicies

def build_outreach_graph(plan_id: str, event_id: str, target_profile: Dict[str, Any]) -> TaskGraph:
    """
    Constructs the deterministic TaskGraph for Deep Research and B2B Outreach.
    Deprecated: not consumed by planner_service; temporal_workflow executor does not exist.
    """
    return TaskGraph(
        plan_id=plan_id,
        event_id=event_id,
        strategy="deep",
        policies=GraphPolicies(max_parallel=3),
        nodes=[
            TaskNode(
                id="deep_research_leads",
                executor="deerflow",
                capability="buyer.research",
                depends_on=[],
                input={"target_profile": target_profile, "max_leads": 10},
                sop_ref="sales-prospector.deep_search_v1" # ECC
            ),
            TaskNode(
                id="generate_trade_documents",
                executor="goodjob_crm",
                capability="document.generate.quotation",
                depends_on=["deep_research_leads"],
                input={"product_category": target_profile.get("product_category")},
                input_from={"company_contexts": "deep_research_leads.output.leads"}
            ),
            TaskNode(
                id="write_personalized_emails",
                executor="accio",
                capability="outreach.write",
                depends_on=["generate_trade_documents"],
                input_from={
                    "leads": "deep_research_leads.output.leads",
                    "quotations": "generate_trade_documents.output.docs"
                },
                sop_ref="copywriter.b2b_cold_email" # ECC
            ),
            TaskNode(
                id="temporal_email_sequence",
                executor="temporal_workflow",
                capability="email.sequence.track",
                depends_on=["write_personalized_emails"],
                input={"wait_days": 3, "follow_up": True},
                input_from={"email_payloads": "write_personalized_emails.output.emails"}
            )
        ]
    )
