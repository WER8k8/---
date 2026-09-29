# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""验证租户端关键词热度查询、零搜索量熔断拦截与谷歌排行榜单元测试。"""
from __future__ import annotations

import uuid
import pytest

from app.models.growth_tools import GrowthKeywordEntry
from app.models.tenant import Tenant, TenantPlan, UserTenant
from app.models.user import User
from app.services.keyword_research_service import (
    analyze_keyword_heat,
    check_zero_volume_guard,
    get_google_hot_leaderboard,
    run_wangcai_deerflow_deep_research,
    save_keywords_to_tenant_library,
)


def _create_tenant_and_user(db_session, name: str) -> tuple[Tenant, User]:
    plan = db_session.query(TenantPlan).first()
    if not plan:
        plan = TenantPlan(name="Plan", code=f"p_{uuid.uuid4().hex[:6]}", price_monthly=0, price_yearly=0)
        db_session.add(plan)
        db_session.flush()

    t = Tenant(
        id=str(uuid.uuid4()),
        name=name,
        domain=f"kw-{uuid.uuid4().hex[:6]}.com",
        plan_id=plan.id,
        status="active",
    )
    db_session.add(t)

    u = User(
        id=str(uuid.uuid4()),
        username=f"u_{uuid.uuid4().hex[:8]}",
        email=f"u_{uuid.uuid4().hex[:8]}@test.com",
        hashed_password="pw",
        role="tenant",
        is_active=True,
    )
    db_session.add(u)
    db_session.flush()

    ut = UserTenant(
        id=str(uuid.uuid4()),
        user_id=u.id,
        tenant_id=t.id,
        role="admin",
        is_active=True,
    )
    db_session.add(ut)
    db_session.commit()
    return t, u


def test_zero_volume_guard_blocks_fake_keywords():
    """【硬锁验证】：假设租户做岩棉，随便设一个生造死词，系统必须坚决熔断拦截并推荐真实词！"""
    # 租户随手乱设的堆砌死词
    fake_kw = "rock wool china factory best cheap good supplier"
    guard = check_zero_volume_guard(fake_kw)

    assert guard["is_zero_volume"] is True
    assert guard["is_prohibited"] is True
    assert guard["guard_status"] == "BLOCKED"
    assert len(guard["suggested_alternatives"]) > 0
    # 自动识别出岩棉品类并推荐真实有流量的 Google 核心词
    alt_keywords = [item["keyword"] for item in guard["suggested_alternatives"]]
    assert any("Rock Wool" in kw or "Mineral Wool" in kw for kw in alt_keywords)


def test_google_b2b_leaderboard():
    """测试获取 Google 官方外贸关键词排行榜。"""
    # 获取绝热保温热门榜
    board = get_google_hot_leaderboard(category="insulation")
    assert board["total"] >= 10
    top1 = board["leaderboard"][0]
    assert top1["keyword"] == "Rock Wool Insulation"
    assert top1["search_volume"] >= 30000
    assert "cpc" in top1
    assert "growth" in top1


def test_keyword_heat_analysis_with_guard(db_session):
    """测试正常关键词查询与分析。"""
    res = analyze_keyword_heat(db_session, "Rock Wool Board", market="global")
    assert res["keyword"] == "Rock Wool Board"
    assert res["zero_volume_guard"]["is_prohibited"] is False
    assert res["search_volume"] > 0
    assert len(res["trends"]) == 12
    assert len(res["regional_demand"]) > 0


def test_tenant_library_isolation(db_session):
    """测试将长尾关键词保存到专属词库，并验证租户间严格数据隔离。"""
    t1, u1 = _create_tenant_and_user(db_session, "租户一-岩棉厂")
    t2, u2 = _create_tenant_and_user(db_session, "租户二-密封件厂")

    t1_keywords = [
        {"keyword": "Rock Wool Insulation wholesale", "word_class": "demand", "search_volume": 4200, "competition": 35, "intent": "批发寻源"},
    ]
    res1 = save_keywords_to_tenant_library(db_session, str(t1.id), t1_keywords)
    assert res1["saved_count"] == 1

    t2_keywords = [
        {"keyword": "Spiral Wound Gasket manufacturer", "word_class": "brand", "search_volume": 5800, "competition": 28, "intent": "工厂直采"},
    ]
    res2 = save_keywords_to_tenant_library(db_session, str(t2.id), t2_keywords)
    assert res2["saved_count"] == 1

    t1_entries = db_session.query(GrowthKeywordEntry).filter(GrowthKeywordEntry.tenant_id == str(t1.id)).all()
    t2_entries = db_session.query(GrowthKeywordEntry).filter(GrowthKeywordEntry.tenant_id == str(t2.id)).all()

    assert [e.keyword for e in t1_entries] == ["Rock Wool Insulation wholesale"]
    assert [e.keyword for e in t2_entries] == ["Spiral Wound Gasket manufacturer"]


def test_wangcai_deerflow_autopilot(db_session):
    """验证旺财 × DeerFlow 2.0 深度研究全自动化：客户零调研成本，AI推演询盘转化与自动部署。"""
    t, u = _create_tenant_and_user(db_session, "租户-外贸岩棉集团")

    res = run_wangcai_deerflow_deep_research(
        db_session,
        str(t.id),
        "Rock Wool Insulation Board",
        auto_apply=True,
    )

    assert "旺财" in res["agent_name"]
    assert "DeerFlow 2.0" in res["engine"]
    assert "metrics_projection" in res
    assert "0%" in res["metrics_projection"]["customer_effort_score"]
    assert len(res["golden_clusters"]) >= 5
    assert res["auto_deploy_status"]["tenant_library"]["status"] == "applied"

    # 验证已自动入库到租户专属词库
    entries = db_session.query(GrowthKeywordEntry).filter(GrowthKeywordEntry.tenant_id == str(t.id)).all()
    assert len(entries) >= 5
    assert any("Rock Wool" in e.keyword for e in entries)


def test_chinese_input_automatic_transmutation_to_target_locales():
    """验证中国用户输入中文产品词时，系统全自动置换为对应国家、对应采购商搜索母语词与母语矩阵。"""
    from app.services.keyword_research_service import transmute_chinese_keyword_to_multilingual

    # 1. 中文岩棉板 -> 德国德语置换
    res_de = transmute_chinese_keyword_to_multilingual("岩棉板", target_country="DE")
    assert res_de["is_transmuted"] is True
    assert res_de["target_country"] == "DE"
    assert res_de["target_language"] == "de"
    assert res_de["transmuted_keyword"] == "Steinwolle Dämmplatte"
    assert "Hersteller" in res_de["transmuted_longtail"]

    # 2. 中文岩棉板 -> 美国英语置换
    res_us = transmute_chinese_keyword_to_multilingual("岩棉板", target_country="US")
    assert res_us["is_transmuted"] is True
    assert res_us["transmuted_keyword"] == "Rock Wool Board"

    # 3. 中文岩棉板 -> 沙特阿拉伯语置换
    res_sa = transmute_chinese_keyword_to_multilingual("岩棉板", target_country="SA")
    assert res_sa["is_transmuted"] is True
    assert res_sa["target_language"] == "ar"
    assert "ألواح الصوف الصخري" in res_sa["transmuted_keyword"]

    # 4. 验证生成的全球多国母语矩阵覆盖 7 大出口国
    matrix = res_de["multilingual_matrix"]
    assert len(matrix) >= 7
    codes = [m["country_code"] for m in matrix]
    assert set(["US", "DE", "ES", "SA", "RU", "FR", "VN"]).issubset(set(codes))

    for item in matrix:
        assert item["search_volume"] > 0
        assert item["keyword"] != ""
        assert "已自动置换" in item["deployment_status"]


def test_chinese_keyword_heat_analysis_localized(db_session):
    """验证查询中文关键词时，系统自动置换为对应目标国海外母语词并获取真实搜索量与母语长尾词。"""
    # 模拟中国用户输入「金属缠绕垫」，目标国家选西班牙 (ES)
    res = analyze_keyword_heat(db_session, "金属缠绕垫", target_country="ES")

    assert res["transmutation"]["is_transmuted"] is True
    assert res["target_country"] == "ES"
    assert res["target_language"] == "es"
    assert res["currency_symbol"] == "€"
    assert res["search_term"] == "Junta espirometálica para bridas"
    assert res["search_volume"] > 0

    # 验证长尾拓展词全为西语本土采购词，且包含中文意图说明
    longtails = res["long_tail_keywords"]
    assert len(longtails) > 0
    assert any("fabricante" in lt["keyword"] or "precios" in lt["keyword"] for lt in longtails)
    assert any("工厂" in lt["intent"] or "价格" in lt["intent"] for lt in longtails)


def test_wangcai_autopilot_with_chinese_product(db_session):
    """验证旺财全自动化深研输入中文时，自动置换多国母语矩阵并落库。"""
    t, u = _create_tenant_and_user(db_session, "租户-外贸门窗总厂")

    res = run_wangcai_deerflow_deep_research(
        db_session,
        str(t.id),
        "断桥铝门窗系统",
        auto_apply=True,
        target_country="DE",
    )

    assert "【多国母语全自动置换完成】" in res["executive_summary"]
    assert "multilingual_matrix" in res
    assert len(res["multilingual_matrix"]) >= 7

    # 检查是否成功落库专属词库
    entries = db_session.query(GrowthKeywordEntry).filter(GrowthKeywordEntry.tenant_id == str(t.id)).all()
    assert len(entries) >= 5


