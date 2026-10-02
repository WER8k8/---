# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""国内轨 · 企微线索自动回流单元测试（Stage A4 验收）。

验证范围：
1. 正常入库：姓名、手机、微信、标签、意向产品完整解析落库；
2. 反欺骗约束：客户端传入伪造的 source_channel 被忽略，服务端硬性锁死 "wecom_ingress"；
3. 触达渠道强校验：phone/wechat/email 全部缺失时拒绝落库并抛出异常；
4. 桥接令牌鉴权：正确令牌放行，错误或空令牌拒绝。
"""
from __future__ import annotations

import json
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.inquiry import Inquiry
from app.services import wecom_lead_ingress_service as svc
from app.services.wecom_lead_ingress_service import WeComIngressError


@pytest.fixture()
def db_session():
    """轻量内存 SQLite 隔离测试会话。"""
    engine = create_engine("sqlite://")
    Inquiry.__table__.create(engine)
    maker = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = maker()
    try:
        yield session
    finally:
        session.close()


class TestWeComLeadIngress:

    def test_successful_ingestion(self, db_session):
        payload = {
            "name": "张经理 (佛山建材总代)",
            "phone": "13800138000",
            "wechat": "wxid_foshanceo123",
            "company": "佛山市优质建材供应链有限公司",
            "interest_product": "600x1200大板瓷砖",
            "message": "在企微咨询大板出口中东报价与箱单明细",
            "tags": ["高意向", "中东买家代理", "佛山工厂"],
            "staff_user_id": "sales_lucy",
            "priority_score": 85,
        }

        inquiry = svc.ingest_wecom_lead(db_session, payload, tenant_id="tenant-888")

        assert inquiry.id is not None
        assert inquiry.name == "张经理 (佛山建材总代)"
        assert inquiry.phone == "13800138000"
        assert inquiry.wechat == "wxid_foshanceo123"
        assert inquiry.product == "600x1200大板瓷砖"
        assert inquiry.source_channel == "wecom_ingress"
        assert inquiry.attribution_channel == "wecom"
        assert inquiry.status == "pending"
        assert inquiry.priority_score == 85
        assert inquiry.tenant_id == "tenant-888"

        attr_data = json.loads(inquiry.attribution_data)
        assert attr_data["channel"] == "wecom"
        assert attr_data["tags"] == ["高意向", "中东买家代理", "佛山工厂"]
        assert attr_data["company"] == "佛山市优质建材供应链有限公司"

    def test_anti_spoofing_forced_source_channel(self, db_session):
        payload = {
            "name": "李总",
            "phone": "13912345678",
            "source_channel": "malicious_spoofed_channel",  # 试图伪造渠道
        }

        inquiry = svc.ingest_wecom_lead(db_session, payload)
        # 服务端硬性覆盖，防止欺骗
        assert inquiry.source_channel == "wecom_ingress"

    def test_missing_contact_info_rejected(self, db_session):
        payload = {
            "name": "无联系方式潜客",
            "company": "测试公司",
            "message": "只留了名字和留言，无任何电话微信邮箱",
        }

        with pytest.raises(WeComIngressError) as exc_info:
            svc.ingest_wecom_lead(db_session, payload)

        assert exc_info.value.reason == "missing_contact_channel"
        assert exc_info.value.status_code == 400

    def test_verify_bridge_token(self, monkeypatch):
        monkeypatch.setenv("WECOM_BRIDGE_TOKEN", "secret-bridge-token-xyz")

        assert svc.verify_bridge_token("secret-bridge-token-xyz") is True
        assert svc.verify_bridge_token("wrong-token") is False
        assert svc.verify_bridge_token("") is False
        assert svc.verify_bridge_token(None) is False

    def test_get_wecom_status_endpoint(self):
        from app.api.v1.routes.wecom_leads import get_wecom_status
        resp = get_wecom_status()
        assert resp.code == 0
        data = resp.data
        assert "sidecar_online" in data
        assert data["source_channel"] == "wecom_ingress"
        assert data["golden_path"] == "GP-C"
        assert "wecom.lead_ingress" in data["supported_capabilities"]
