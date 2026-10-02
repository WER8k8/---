# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""爱马仕 (Hermes) 直接驱动国内轨企微执行器单元测试。

验证范围：
1. 注册表契约：ExecutorRegistry 包含 "wecom_scrm"，能力声明完备；
2. 能力自述：各 Capability 声明入参/出参与群发人审闸门 (needs_approval)；
3. 原生直驱执行：调度 wecom.lead_ingress 成功落库 UJ inquiries；
4. 负向防御：不支持的能力返回 skipped 并自述支持清单。
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.inquiry import Inquiry
from app.schemas.hermes_orchestration import TaskNode
from app.services.hermes.executors.base import ExecutorContext, ExecutorRegistry
from app.services.hermes.executors.wecom_scrm_executor import WecomScrmExecutor


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite://")
    Inquiry.__table__.create(engine)
    maker = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = maker()
    try:
        yield session
    finally:
        session.close()


class TestWecomScrmExecutor:

    def test_executor_registered(self):
        assert ExecutorRegistry.has("wecom_scrm") is True
        executor = ExecutorRegistry.get("wecom_scrm")
        assert isinstance(executor, WecomScrmExecutor)
        assert executor.get_executor_name() == "wecom_scrm"

    def test_capabilities_declaration(self):
        caps = WecomScrmExecutor.get_capabilities()
        assert "wecom.lead_ingress" in caps
        assert "wecom.customer_seas" in caps
        assert "wecom.create_live_code" in caps
        assert "wecom.chat_audit" in caps
        assert "wecom.send_group_msg" in caps

        # 企微群发营销必须声明需要人审审批
        assert caps["wecom.send_group_msg"]["needs_approval"] is True
        assert caps["wecom.lead_ingress"]["needs_approval"] is False

    @pytest.mark.asyncio
    async def test_native_direct_drive_lead_ingress(self, db_session):
        executor = WecomScrmExecutor()
        node = TaskNode(
            id="node-wecom-01",
            name="国内企微新客入库履约",
            executor="wecom_scrm",
            capability="wecom.lead_ingress",
            input={
                "name": "李总 (深圳门窗工程)",
                "phone": "13699998888",
                "wechat": "wxid_shenzhen_door",
                "company": "深圳宏达建材工程有限公司",
                "message": "在企微咨询大宗断桥铝型材出口报关",
                "tags": ["高意向", "工程大宗", "深圳总包"],
            },
        )
        context = ExecutorContext(db=db_session, tenant_id="tenant-sz-001", plan_id="plan-999")

        result = await executor.run(node, context)

        assert result.status == "succeeded"
        assert result.output["source_channel"] == "wecom_ingress"
        assert result.output["executor"] == "wecom_scrm"
        assert result.output["name"] == "李总 (深圳门窗工程)"

        # 数据库查验实证
        saved = db_session.query(Inquiry).filter(Inquiry.id == result.output["inquiry_id"]).first()
        assert saved is not None
        assert saved.phone == "13699998888"
        assert saved.tenant_id == "tenant-sz-001"
        assert saved.status == "pending"

    @pytest.mark.asyncio
    async def test_unsupported_capability_skipped(self, db_session):
        executor = WecomScrmExecutor()
        node = TaskNode(
            id="node-unsupported",
            name="未定义动作",
            executor="wecom_scrm",
            capability="wecom.unsupported_action",
            input={},
        )
        context = ExecutorContext(db=db_session, tenant_id="t-1", plan_id="p-1")

        result = await executor.run(node, context)
        assert result.status == "skipped"
        assert "wecom_scrm 不支持" in result.error
