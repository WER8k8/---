"""ECommerceCrawlers 智能层 — 大白话状态、自动补全合规字段、一键探测。"""

from __future__ import annotations

from typing import Any

from app.services.crawlers.ecommerce_crawlers_registry import (
    SPIDER_RECIPES,
    recipe_by_id,
)
from app.services.crawlers.ecommerce_crawlers_sidecar import (
    ecommerce_crawlers_sidecar_status,
    run_spider,
)
from app.services.geo.headless_rank_probe_service import headless_probe_sidecar_status
from app.services.ubrain.ai_find_customer_sidecar import ai_find_customer_sidecar_status
from app.services.ubrain.domain_email_extractor_sidecar import domain_email_extractor_sidecar_status
from app.services.crawlers.media_crawler_sidecar import media_crawler_sidecar_status
from app.services.ubrain.linkedin_decision_maker_sidecar import linkedin_decision_maker_sidecar_status
from app.services.foreign_trade.customs_data_spider_sidecar import customs_data_spider_sidecar_status

# 用户可见：错误码 → 中文说明 + 下一步
ERROR_HINTS_ZH: dict[str, str] = {
    "SPIDER_UNKNOWN": "未识别的采集类型，请从列表中选择",
    "SPIDER_PLATFORM_BLOCKED": "该能力属于黑帽 SEO，平台永久关闭",
    "SPIDER_PURPOSE_REQUIRED": "请填写用途说明（例如：SEO 收录监测）",
    "SPIDER_PLATFORM_NOT_ENABLED": "平台尚未开通此采集项，请联系运维在服务器配置开关",
    "SPIDER_TENANT_CONSENT_REQUIRED": "须勾选「租户已授权」后再试",
    "SPIDER_COMPLIANCE_ACK_REQUIRED": "须勾选「已阅读合规承诺」后再试",
    "SOCIAL_SPIDERS_NOT_ENABLED": "微信/微博/知乎等社媒采集须运维单独开通",
    "SPIDER_BULK_OUTREACH_FORBIDDEN": "禁止批量触达，本系统仅支持公开信息研究",
    "SPIDER_ROLE_DENIED": "当前账号无权触发，请用租户管理员或平台运维账号",
    "ECOMMERCE_CRAWLERS_NOT_CONFIGURED": "采集服务未部署：运维需配置 ECOMMERCE_CRAWLERS_URL",
    "ECOMMERCE_CRAWLERS_SIDECAR_ERROR": "采集服务无响应，请检查 Sidecar 是否在线",
    "SPIDER_NO_EVIDENCE": "采集完成但未返回可核对链接，结果不会写入系统",
}

COMPLIANCE_LABEL_ZH: dict[str, str] = {
    "allowed_sidecar": "可直接使用",
    "human_review": "可用 · 须人工核实",
    "restricted": "敏感 · 须授权",
    "social_restricted": "社媒 · 须单独开通",
    "platform_blocked": "永久禁用",
}

LANE_LABEL_ZH: dict[str, str] = {
    "seo_matrix": "SEO 收录",
    "osint": "企业背调",
    "competitor_intel": "竞品价盘",
    "growth_tools": "内容与舆情",
    "market_intel": "市场信号",
    "reference_only": "参考数据",
    "international_inquiry": "海外询盘",
}

# 一键入口别名（前端不必记 spider_id）
QUICK_PRESETS: dict[str, str] = {
    "baidu": "baidu_keyword",
    "seo": "baidu_keyword",
    "qichacha": "qichacha",
    "osint": "qichacha",
    "zhaopin": "zhaopin",
    "wechat": "wechat",
    "weibo": "weibo",
    "zhihu": "zhihu",
}


def _sidecar_label(st: dict[str, Any]) -> tuple[str, str]:
    """实现 sidecarlabel 的功能。
    
    :param st: 参数 st（类型: dict[str, Any]）
    :return: 返回 tuple[str, str] 结果
    """
    if not st.get("configured"):
        return "未接入", "运维尚未配置采集服务地址"
    if st.get("healthy"):
        return "已就绪", "采集服务在线，可发起检测"
    return "不可达", st.get("detail") or "地址已配置但服务未响应，请检查 Sidecar 进程"


def _recipe_ui(recipe) -> dict[str, Any]:
    """实现 recipeui 的功能。
    
    :param recipe: 参数 recipe 的说明
    :return: 返回 dict[str, Any] 结果
    """
    tier = recipe.compliance
    return {
        "id": recipe.id,
        "name": recipe.name,
        "lane_label": LANE_LABEL_ZH.get(recipe.lane, recipe.lane),
        "compliance_label": COMPLIANCE_LABEL_ZH.get(tier, tier),
        "callable": tier != "platform_blocked",
        "summary": recipe.summary,
        "needs_consent": tier in ("restricted", "social_restricted"),
        "needs_social_enable": tier == "social_restricted",
    }


def _collect_panel_status():
    """采集各旁路 spider / 分析模块的在线状态。"""
    ec = ecommerce_crawlers_sidecar_status()
    hl = headless_probe_sidecar_status()
    fc = ai_find_customer_sidecar_status()
    em = domain_email_extractor_sidecar_status()
    mc = media_crawler_sidecar_status()
    li = linkedin_decision_maker_sidecar_status()
    cu = customs_data_spider_sidecar_status()
    return ec, hl, fc, em, mc, li, cu


def _build_panel_modules(ec, hl, fc, em, mc, li, cu, ua_slice):
    """根据各旁路状态构造管理端面板模块列表。"""
    ec_label, ec_hint = _sidecar_label(ec)
    hl_label, hl_hint = _sidecar_label(hl)
    fc_label, fc_hint = _sidecar_label(fc)
    em_label, em_hint = _sidecar_label(em)
    mc_label, mc_hint = _sidecar_label(mc)
    li_label, li_hint = _sidecar_label(li)
    cu_label, cu_hint = _sidecar_label(cu)
    featured = [
        _recipe_ui(r)
        for r in SPIDER_RECIPES
        if r.id in ("baidu_keyword", "qichacha", "zhaopin", "wechat", "taobao")
    ]
    return [
        {
            "id": "domestic_crawl",
            "name": "国内电商/资讯采集",
            "status": ec_label,
            "hint": ec_hint,
            "registry_count": ec.get("registry_count"),
            "featured_spiders": featured,
        },
        {
            "id": "user_action_analytics",
            "name": ua_slice["name"],
            "status": ua_slice["status"],
            "hint": ua_slice["hint"],
            "featured_modules": ua_slice.get("featured_modules"),
        },
        {
            "id": "headless_probe",
            "name": "Headless 排名探针",
            "status": hl_label,
            "hint": hl_hint,
        },
        {
            "id": "find_customer",
            "name": "AI 找客旁路",
            "status": fc_label,
            "hint": fc_hint,
        },
        {
            "id": "domain_email_extractor",
            "name": "官网邮箱 enrichment",
            "status": em_label,
            "hint": em_hint,
        },
        {
            "id": "media_crawler",
            "name": "MediaCrawler 社媒/黄页",
            "status": mc_label,
            "hint": mc_hint,
        },
        {
            "id": "linkedin_decision_maker",
            "name": "LinkedIn 决策人（受限）",
            "status": li_label,
            "hint": li_hint,
        },
        {
            "id": "customs_data_spider",
            "name": "海关买家反查（受限）",
            "status": cu_label,
            "hint": cu_hint,
        },
    ]


def _build_panel_extracted():
    """提取出的子流程，封装原函数的局部计算逻辑。

    :return: 返回 overall, overall_hint, modules 等计算结果
    """
    """管理端一页看懂：旁路状态 + 常用采集项。"""
    from app.services.analytics.user_action_analytics_smart import build_panel_slice
    ec, hl, fc, em, mc, li, cu = _collect_panel_status()
    ua_slice = build_panel_slice()
    modules = _build_panel_modules(ec, hl, fc, em, mc, li, cu, ua_slice)
    ready_count = sum(
        1 for x in (ec, hl, fc, em, mc, li, cu) if x.get("healthy")
    )
    if ua_slice.get("healthy") or (ua_slice.get("status") == "已就绪"):
        ready_count += 1

    if ready_count >= 2:
        overall = "部分就绪"
        overall_hint = f"多个旁路在线，可按需在增长工具中发起检测/分析"
    elif ready_count == 1:
        overall = "部分就绪"
        overall_hint = "仅部分旁路在线，未接入的功能会提示「未配置」而非假数据"
    else:
        overall = "未接入"
        overall_hint = "旁路未部署时系统不会伪造采集/分析结果"
    return overall, overall_hint, modules

def build_panel() -> dict[str, Any]:
    """build_panel。
    :return: 返回处理结果。
    """
    overall, overall_hint, modules = _build_panel_extracted()
    return {
        "headline": "数据采集旁路",
        "overall_status": overall,
        "overall_hint": overall_hint,
        "modules": modules,
        "usage_tips": [
            "百度收录：增长工具 → 引流监测 → 测百度收录",
            "页面转化：增长工具 → 引流监测 → 查页面转化",
            "AI 找客：销售 → 客户开发（Sidecar 在线时带 evidence_url）",
            "邮箱补全：找客后自动尝试 DOMAIN_EMAIL_EXTRACTOR_URL",
            "LinkedIn 决策人：须租户授权 + 合规勾选，禁止自动群发",
            "海关买家 brief：GET /foreign-trade/trade-intel/customs-buyer-brief",
            "海关买家反查：POST /foreign-trade/integrations/customs/buyer-research（须授权）",
        ],
    }


def resolve_spider_id(preset_or_id: str) -> str | None:
    """实现 解析spiderID 的功能。
    
    :param preset_or_id: 参数 preset_or_id（类型: str）
    :return: 返回 str | None 结果
    """
    key = (preset_or_id or "").strip().lower()
    if not key:
        return None
    if recipe_by_id(key):
        return key
    return QUICK_PRESETS.get(key)


def _default_purpose(spider_id: str, keyword: str | None) -> str:
    """实现 defaultpurpose 的功能。
    
    :param spider_id: 参数 spider_id（类型: str）
    :param keyword: 参数 keyword（类型: str | None）
    :return: 返回 str 结果
    """
    recipe = recipe_by_id(spider_id)
    kw = (keyword or "").strip()
    lane = recipe.lane if recipe else "general"
    if spider_id == "baidu_keyword":
        return f"SEO 百度收录监测{'：' + kw if kw else ''}"
    if spider_id == "qichacha":
        return f"企业背调 enrichment{'：' + kw if kw else ''}"
    if lane == "competitor_intel":
        return f"竞品/市场信号监测{'：' + kw if kw else ''}"
    if recipe and recipe.compliance == "social_restricted":
        return f"公开社媒内容行业研究{'：' + kw if kw else ''}"
    return f"数据采集{'：' + kw if kw else ''}"


def apply_run_defaults(
    *,
    spider_id: str,
    operator_role: str | None,
    purpose: str | None,
    tenant_consent: bool,
    compliance_acknowledged: bool,
) -> tuple[str, bool, bool]:
    """平台运维触发时自动补全合规字段，减少手工勾选。"""
    role = (operator_role or "").lower()
    purpose_out = (purpose or "").strip() or _default_purpose(spider_id, None)
    consent = tenant_consent
    ack = compliance_acknowledged
    if role in ("super_admin", "admin"):
        consent = True
        ack = True
    return purpose_out, consent, ack


def quick_run(
    preset_or_id: str,
    *,
    keyword: str | None = None,
    site: str | None = None,
    tenant_id: str | None = None,
    operator_role: str | None = None,
    tenant_consent: bool = False,
    compliance_acknowledged: bool = False,
    purpose: str | None = None,
) -> dict[str, Any]:
    """一键探测：只需 preset + 关键词，其余自动处理。"""
    spider_id = resolve_spider_id(preset_or_id)
    if not spider_id:
        return {
            "ok": False,
            "error_code": "SPIDER_UNKNOWN",
            "message_zh": ERROR_HINTS_ZH["SPIDER_UNKNOWN"],
        }

    purpose_final, consent, ack = apply_run_defaults(
        spider_id=spider_id,
        operator_role=operator_role,
        purpose=purpose or _default_purpose(spider_id, keyword),
        tenant_consent=tenant_consent,
        compliance_acknowledged=compliance_acknowledged,
    )
    params: dict[str, Any] = {}
    if keyword:
        params["keyword"] = keyword.strip()
    if site:
        params["site"] = site.strip()

    out = run_spider(
        spider_id,
        params=params,
        tenant_id=tenant_id,
        operator_role=operator_role,
        purpose=purpose_final,
        tenant_consent=consent,
        compliance_acknowledged=ack,
    )
    return enrich_result_zh(out)


def enrich_result_zh(result: dict[str, Any]) -> dict[str, Any]:
    """给 API 响应加中文说明，前端直接展示。"""
    code = result.get("error_code")
    if not result.get("ok") and code:
        result = dict(result)
        result["message_zh"] = ERROR_HINTS_ZH.get(code, result.get("note") or "操作未成功")
        return result
    if result.get("ok"):
        result = dict(result)
        if result.get("human_review_required"):
            result["message_zh"] = "采集完成，结果须人工核实后再用于业务决策"
        else:
            result["message_zh"] = "采集完成，可点开 evidence 链接核对"
    return result


def domestic_crawl_summary_for_traffic() -> dict[str, Any]:
    """增长工具引流 Tab 用的精简块。"""
    ec = ecommerce_crawlers_sidecar_status()
    label, hint = _sidecar_label(ec)
    return {
        "title": "百度收录探针",
        "status": label,
        "hint": hint,
        "configured": ec.get("configured"),
        "healthy": ec.get("healthy"),
        "quick_action": "baidu",
        "placeholder_keyword": "输入关键词，例如：保温建材",
    }
