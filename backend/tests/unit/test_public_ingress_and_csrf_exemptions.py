# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""公开入站与 CSRF 豁免、RLS 容灾单元测试 (G-11 ~ G-13 验收)."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.csrf_middleware import _API_EXEMPT_PREFIXES, _PUBLIC_PREFIXES
from app.models.inquiry import Inquiry
from app.schemas.inquiry import InquiryCreate


def test_csrf_exemptions_contain_public_endpoints():
    """验证公开端点（wangcai, system/contact, wecom-leads）在 CSRF 豁免白名单中。"""
    assert "/api/v1/system/contact" in _API_EXEMPT_PREFIXES
    assert "/api/v1/wangcai" in _API_EXEMPT_PREFIXES
    assert "/api/v1/wecom-leads" in _API_EXEMPT_PREFIXES
    assert "/api/v1/public" in _API_EXEMPT_PREFIXES


def test_public_health_prefixes_present():
    """验证健康探活端点在 _PUBLIC_PREFIXES 中。"""
    assert "/health" in _PUBLIC_PREFIXES
    assert "/api/v1/health" in _PUBLIC_PREFIXES
    assert "/api/v1/system/health" in _PUBLIC_PREFIXES


def test_submit_contact_logic():
    """验证 submit_contact 逻辑能够平稳写入，且 RLS 兼容不崩溃。"""
    engine = create_engine("sqlite://")
    Inquiry.__table__.create(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        from app.api.v1.routes.system import submit_contact
        req = InquiryCreate(
            name="公开访客张先生",
            email="zhang@example.com",
            phone="13811112222",
            product="石膏板系统",
            message="咨询石膏板耐火等级及检测报告",
        )
        resp = submit_contact(req=req, db=db, request=None)
        assert resp.status_code == 201
        
        # 验证数据库中真实有行
        inq = db.query(Inquiry).filter(Inquiry.email == "zhang@example.com").first()
        assert inq is not None
        assert inq.name == "公开访客张先生"
        assert inq.product == "石膏板系统"
    finally:
        db.close()
