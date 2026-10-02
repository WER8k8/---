# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Hermes L1 模板规划验证：企微私域 / 国内获客（GP-C）。"""
import uuid
import pytest

from app.schemas.hermes_orchestration import IntentEvent
from app.services.hermes import planner_service
from app.services.hermes.annex_work_mode import golden_path_for_executors


@pytest.mark.asyncio
async def test_wecom_scrm_resolves_l1_template():
    """验证 Hermes 自然语言命中企微私域 L1 模板，生成合法 DAG。"""
    event = IntentEvent(
        event_id=str(uuid.uuid4()),
        tenant_id="t-wecom-test",
        channel="web",
        intent="企微获客",
        payload={
            "message": "创建企微活码并同步客户公海",
            "channel_name": "建材展会活码",
            "scene": "canton_fair_2026",
        },
    )

    graph, source = await planner_service.decompose(event, db=None)
    assert source == "L1_template"

    # 拓扑三道安全阀校验
    problems = planner_service.validate_graph(graph)
    assert problems == [], f"DAG 拓扑校验失败: {problems}"

    # 验证节点执行器与能力
    node_map = {n.id: n for n in graph.nodes}
    assert "n1" in node_map
    assert node_map["n1"].executor == "wecom_scrm"
    assert node_map["n1"].capability == "wecom.create_live_code"
    assert node_map["n1"].input["name"] == "建材展会活码"

    assert "n2" in node_map
    assert node_map["n2"].executor == "wecom_scrm"
    assert node_map["n2"].capability == "wecom.lead_ingress"
    assert "n1" in node_map["n2"].depends_on

    assert "n3" in node_map
    assert node_map["n3"].executor == "wecom_scrm"
    assert node_map["n3"].capability == "wecom.customer_seas"

    # 验证策略安全
    assert "wecom.send_group_msg" in graph.policies.approval_required

    # 验证黄金路径 GP-C 识别
    executors = {n.executor for n in graph.nodes}
    gp = golden_path_for_executors(executors)
    assert gp is not None
    assert gp["id"] == "GP-C"
    assert gp["name"] == "企微私域与线索回流（国内轨 SCRM）"
