# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""验证租户端关键词热度查询、零搜索量熔断拦截与谷歌排行榜单元测试。"""
from __future__ import annotations

import json
import uuid
import pytest

from app.models.growth_tools import GrowthKeywordEntry
from app.models.tenant import Tenant, TenantPlan, UserTenant
from app.models.user import User
from app.services.keyword_research_service import (
    analyze_keyword_heat,
    check_zero_volume_guard,
    generate_full_site_seo_blueprint,
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


def test_full_site_blueprint_without_competitor_generates_five_pillars(db_session):
    """验证无同行参考时，启动五维正向推演（场景/替代品/标准/FAQ/母语）并生成扁平化页面拓扑与避坑指南。"""
    t, u = _create_tenant_and_user(db_session, "租户-无同行创新建材")

    res = generate_full_site_seo_blueprint(
        db_session,
        str(t.id),
        "岩棉保温板",
        product_parameters="密度: 120kg/m3, 厚度: 50mm, 耐火: A1级",
        substitute_products="EPS聚苯板, 玻璃棉",
        industry_standards="ASTM C578, EN 13501-1",
        customer_faqs="最高耐温多少度？40HQ装多少方？",
        competitor_urls=[],
        target_country="US",
    )

    assert res["status"] == "success"
    assert res["mode"] == "BLUE_OCEAN_FIVE_PILLARS"
    assert "无成熟同行参考" in res["mode_description"]

    # 1. 验证 4 大避坑诊断全覆盖
    pitfalls = res["pitfall_diagnostics"]
    assert len(pitfalls) == 4
    pitfall_ids = {p["pitfall_id"] for p in pitfalls}
    assert {"PITFALL_01", "PITFALL_02", "PITFALL_03", "PITFALL_04"} == pitfall_ids
    assert all(p["status"] == "GUARDED_PASSED" for p in pitfalls)

    # 2. 验证导航栏（避开直觉命名，强制绑定 Google 高搜量）
    nav = res["navigation_architecture"]
    assert len(nav) >= 4
    assert any(n["google_search_volume"] >= 10000 for n in nav)
    assert any("/solutions" in n["slug"] for n in nav)
    assert any("/vs-traditional" in n["slug"] for n in nav)

    # 3. 验证五维正向推演内容齐全
    five = res["five_pillars"]
    assert len(five["pillar_1_solutions"]) >= 3
    assert len(five["pillar_2_vs_substitutes"]) >= 2
    assert len(five["pillar_3_standards"]) >= 2
    # A2：customer_faqs 入参真消费（按问号/分号/换行切分为逐条问题），不再回落 4 条岩棉模板
    faqs = five["pillar_4_faqs"]
    assert len(faqs) == 2
    assert all(f["faq_source"] == "tenant_input" for f in faqs)
    assert all(f["answer_pending"] is True for f in faqs)
    assert len(five["pillar_5_multilingual_matrix"]) >= 7

    # 4. 验证扁平化拓扑（Max 2-3 层，杜绝深层衰减，且含具体型号落地页）
    matrix = res["page_topology_matrix"]
    assert len(matrix) >= 10
    # 验证 URL 扁平化规约：路径斜杠数量不超过 3（例如 /{lang}/p/slug 为 3 个斜杠）
    for page in matrix:
        assert page["flat_url"].count("/") <= 4, f"URL 层级过深: {page['flat_url']}"
    # 验证包含型号级落地页（A3：主力型号页由租户入参驱动生成）
    model_pages = [p for p in matrix if p["page_type"] == "product_spec"]
    assert len(model_pages) >= 3
    tenant_model_pages = [p for p in model_pages if p.get("model_slug_source") == "tenant_parameters"]
    assert len(tenant_model_pages) == 1
    assert "120kg-50mm" in tenant_model_pages[0]["flat_url"]

    # 5. 验证执行路线图（A6：milestones 只留内容铺设，运维动作拆 advisory_actions）
    roadmap = res["execution_roadmap"]
    assert len(roadmap["milestones"]) == 3
    assert "单日铺设 4~5 个" in roadmap["daily_cadence"]
    milestone_blob = json.dumps(roadmap["milestones"], ensure_ascii=False)
    for banned in ("Sitemap", "hreflang", "GSC", "Search Console"):
        assert banned not in milestone_blob, f"运维动作不应混入 milestones: {banned}"
    advisory = res["advisory_actions"]
    advisory_blob = json.dumps(advisory, ensure_ascii=False)
    for expected in ("Sitemap", "hreflang", "Search Console"):
        assert expected in advisory_blob
    assert all(a["owner_hint"] == "deploy" for a in advisory)


def test_full_site_blueprint_with_competitors(db_session):
    """验证传同行 URL 时诚实降级为通用模板（A4：本版本不抓取，不得伪称已逆向拆解）。"""
    t, u = _create_tenant_and_user(db_session, "租户-有同行对标")

    res = generate_full_site_seo_blueprint(
        db_session,
        str(t.id),
        "Spiral Wound Gasket",
        competitor_urls=["https://competitor-gasket.com", "https://peer-sealing.com"],
        target_country="US",
    )

    assert res["status"] == "success"
    assert res["mode"] == "TEMPLATE_FALLBACK_NO_CRAWL"
    assert res["honesty_note"]
    assert "未做真实抓取" in res["mode_description"]
    assert res["competitor_deconstruction"] is not None
    comp = res["competitor_deconstruction"]
    assert comp["mode"] == "TEMPLATE_FALLBACK_NO_CRAWL"
    assert comp["deconstruction_source"] == "generic_template"
    assert len(comp["analyzed_sites"]) == 2
    assert len(comp["extracted_selling_points"]) >= 3
    assert len(comp["extracted_buyer_demands"]) >= 3
    assert comp["differentiation_edge"] != ""


# =========================================================================
# 模块3 修复（A1–A7）配对反证：负向（默认路径可冻结）+ 正向（传参后字段必变）
# =========================================================================

def test_blueprint_deterministic_for_same_input(db_session):
    """A7 负向基线：同一输入两次调用输出逐字段一致（无随机漂移），可作回归冻结基线。"""
    t, u = _create_tenant_and_user(db_session, "租户-确定性基线")

    first = generate_full_site_seo_blueprint(db_session, str(t.id), "Spiral Wound Gasket", target_country="US")
    second = generate_full_site_seo_blueprint(db_session, str(t.id), "Spiral Wound Gasket", target_country="US")

    for key in (
        "industry_key",
        "template_scope",
        "navigation_architecture",
        "pitfall_diagnostics",
        "five_pillars",
        "page_topology_matrix",
        "execution_roadmap",
        "advisory_actions",
    ):
        assert json.dumps(first[key], ensure_ascii=False, sort_keys=True) == json.dumps(
            second[key], ensure_ascii=False, sort_keys=True
        ), f"字段 {key} 非确定性"


def test_blueprint_nav_volumes_from_data_gateway(db_session):
    """A1 正向：导航搜索量来自数据网关（含来源标注），不手填。"""
    t, u = _create_tenant_and_user(db_session, "租户-导航取数")
    res = generate_full_site_seo_blueprint(db_session, str(t.id), "岩棉保温板", target_country="US")

    nav = res["navigation_architecture"]
    assert len(nav) >= 4
    for item in nav:
        assert item["target_keyword"]
        assert item["data_source"] in ("semrush_live_api", "google_benchmark_db")
        assert item["raw_status"] in ("ok", "matched_exact", "matched_multilingual_exact", "estimated")
        assert isinstance(item["google_search_volume"], int)

    products = next(n for n in nav if n["slug"] == "/products")
    assert products["raw_status"] == "matched_exact"
    assert products["google_search_volume"] > 0
    # 未命中真实词时必须如实标 estimated，不得伪装成 live
    estimated = [n for n in nav if n["raw_status"] == "estimated"]
    assert all(n["data_source"] != "semrush_live_api" for n in estimated)


def test_blueprint_source_has_no_hardcoded_nav_volumes():
    """A1 源码级门禁：不得再出现写死的 google_search_volume 常量。"""
    import inspect
    import re as _re

    from app.services import keyword_research_service as krs

    src = inspect.getsource(krs)
    assert not _re.search(r'"google_search_volume":\s*\d', src)


def test_blueprint_source_has_no_fake_deconstruction_claim():
    """A4 源码级门禁：误导话术「逆向拆解与卖点库萃取」必须 0 命中。"""
    import inspect

    from app.services import keyword_research_service as krs

    assert "逆向拆解与卖点库萃取" not in inspect.getsource(krs)


def test_blueprint_faqs_consumed_from_tenant_input(db_session):
    """A2 正向：customer_faqs 逐条生成问题，答案留空标 answer_pending（不臆造答案）。"""
    t, u = _create_tenant_and_user(db_session, "租户-FAQ真消费")
    res = generate_full_site_seo_blueprint(
        db_session,
        str(t.id),
        "Spiral Wound Gasket",
        customer_faqs="最高耐压是多少？40HQ装多少件？MOQ是多少？",
        target_country="US",
    )

    faqs = res["five_pillars"]["pillar_4_faqs"]
    assert len(faqs) == 3
    assert all(f["faq_source"] == "tenant_input" for f in faqs)
    assert all(f["answer_pending"] is True for f in faqs)
    assert all(f["answer"] == "" for f in faqs)
    assert [f["question"] for f in faqs] == ["最高耐压是多少", "40HQ装多少件", "MOQ是多少"]


def test_blueprint_faqs_fallback_labeled_when_absent(db_session):
    """A2 负向：未传 customer_faqs → 回落模板并标注 template_fallback。"""
    t, u = _create_tenant_and_user(db_session, "租户-FAQ回落")
    res = generate_full_site_seo_blueprint(db_session, str(t.id), "Spiral Wound Gasket", target_country="US")

    faqs = res["five_pillars"]["pillar_4_faqs"]
    assert len(faqs) >= 3
    assert all(f["faq_source"] == "template_fallback" for f in faqs)


def test_blueprint_product_parameters_generates_tenant_model_page(db_session):
    """A3 正向：product_parameters 真消费，生成租户参数驱动的型号长尾页。"""
    t, u = _create_tenant_and_user(db_session, "租户-型号参数")
    res = generate_full_site_seo_blueprint(
        db_session,
        str(t.id),
        "Spiral Wound Gasket",
        product_parameters="压力等级: Class 300, 密度: 120kg/m3, 厚度: 50mm",
        target_country="US",
    )

    pages = [p for p in res["page_topology_matrix"] if p["page_type"] == "product_spec"]
    tenant_pages = [p for p in pages if p.get("model_slug_source") == "tenant_parameters"]
    assert len(tenant_pages) == 1
    assert "120kg-50mm" in tenant_pages[0]["flat_url"]
    assert "120" in " ".join(tenant_pages[0]["long_tail_models"])
    assert "50mm" in " ".join(tenant_pages[0]["long_tail_models"])


def test_blueprint_no_parameters_falls_back_labelled(db_session):
    """A3 负向：未传 product_parameters → 沿用模板页并标注 template_fallback。"""
    t, u = _create_tenant_and_user(db_session, "租户-型号回落")
    res = generate_full_site_seo_blueprint(db_session, str(t.id), "岩棉保温板", target_country="US")

    pages = [p for p in res["page_topology_matrix"] if p["page_type"] == "product_spec"]
    primary = pages[0]
    assert primary["model_slug_source"] == "template_fallback"
    assert "RW-120-50" in primary["long_tail_models"]


def test_blueprint_non_building_material_has_no_rockwool_leak(db_session):
    """A5 正向：非建材行业输出中不得出现任何岩棉 SKU 与岩棉专有数值。"""
    t, u = _create_tenant_and_user(db_session, "租户-非建材密封件")
    res = generate_full_site_seo_blueprint(db_session, str(t.id), "Spiral Wound Gasket", target_country="US")

    assert res["industry_key"] == "sealing"
    assert res["template_scope"] == "generic"

    blob = json.dumps(res, ensure_ascii=False)
    for leaked in (
        "RW-120-50",
        "RW-140-75",
        "RWP-150",
        "RWB-Wire-50",
        "rock-wool-board",
        "rock-wool-pipe",
        "rock-wool-acoustic",
        "650°C",
        "65 to 72 cubic meters",
        "ASTM C578",
    ):
        assert leaked not in blob, f"非建材输出泄漏岩棉内容: {leaked}"


def test_blueprint_rockwool_keeps_building_template(db_session):
    """A5 对照：岩棉系保留建材模板，并标注 template_scope=rock_wool。"""
    t, u = _create_tenant_and_user(db_session, "租户-岩棉保留")
    res = generate_full_site_seo_blueprint(db_session, str(t.id), "岩棉保温板", target_country="US")

    assert res["industry_key"] == "insulation"
    assert res["template_scope"] == "rock_wool"
    assert "RW-120-50" in json.dumps(res, ensure_ascii=False)


def test_blueprint_competitor_urls_downgraded_honestly(db_session):
    """A4：传 competitor_urls 时仅登记来源，mode/话术如实降级，不做假拆解。"""
    t, u = _create_tenant_and_user(db_session, "租户-同行诚实降级")
    res = generate_full_site_seo_blueprint(
        db_session,
        str(t.id),
        "Spiral Wound Gasket",
        competitor_urls=["https://a.com", "https://b.com", "https://c.com"],
        target_country="US",
    )

    assert res["mode"] == "TEMPLATE_FALLBACK_NO_CRAWL"
    assert "未做真实抓取" in res["mode_description"]
    assert "逆向拆解与卖点库萃取" not in res["mode_description"]
    assert res["honesty_note"]
    comp = res["competitor_deconstruction"]
    assert comp["mode"] == "TEMPLATE_FALLBACK_NO_CRAWL"
    assert comp["deconstruction_source"] == "generic_template"
    assert len(comp["analyzed_sites"]) == 3


def test_blueprint_nav_flags_below_benchmark(db_session):
    """A1 补强（复核 P2-1）：低于 10,000 基准的导航词必须显式标 below_benchmark，不得伪称已达标。"""
    t, u = _create_tenant_and_user(db_session, "租户-基准标记")

    # tile → en_base 未命中权威基准库，products 走算法估算且低于基准
    res = generate_full_site_seo_blueprint(db_session, str(t.id), "tile", target_country="US")
    nav = res["navigation_architecture"]
    for item in nav:
        assert item["below_benchmark"] is (item["google_search_volume"] < 10000)

    products = next(n for n in nav if n["slug"] == "/products")
    assert products["raw_status"] == "estimated"
    assert products["below_benchmark"] is True
    assert products["google_search_volume"] < 10000

    # 对照：命中权威基准库的大词不得被误标
    res2 = generate_full_site_seo_blueprint(db_session, str(t.id), "岩棉保温板", target_country="US")
    products2 = next(n for n in res2["navigation_architecture"] if n["slug"] == "/products")
    assert products2["raw_status"] == "matched_exact"
    assert products2["below_benchmark"] is False


def test_blueprint_all_parsed_parameters_are_consumed(db_session):
    """复核 P3-1：规格/耐火等已解析入参必须被消费，不得「解析了却静默丢弃」。"""
    t, u = _create_tenant_and_user(db_session, "租户-参数全消费")
    res = generate_full_site_seo_blueprint(
        db_session,
        str(t.id),
        "Spiral Wound Gasket",
        product_parameters="密度: 120kg/m3, 厚度: 50mm, 规格: DN150 PN40, 耐火: A1级",
        target_country="US",
    )

    page = next(p for p in res["page_topology_matrix"] if p.get("model_slug_source") == "tenant_parameters")
    blob = " ".join(page["long_tail_models"]) + " " + " ".join(page["secondary_keywords"])
    assert "DN150 PN40" in blob, "spec 入参未被消费"
    assert "A1级" in blob, "fire 入参未被消费"


