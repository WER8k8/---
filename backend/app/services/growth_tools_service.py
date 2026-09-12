"""三大增长内置工具 — 热门词库 / 内容质检 / AI 引流监测。"""

from __future__ import annotations

import re
import uuid
from collections import defaultdict
from typing import Any

from sqlalchemy.orm import Session

from app.models.content import InclusionStatus
from app.models.growth_tools import WORD_CLASSES, GrowthKeywordEntry
from app.models.region import GeneratedKeyword, IndustryKeyword
from app.models.seo import KeywordRanking
from app.services.compliance_scanner import ComplianceScanner
from app.services.content_scorer import score_content
from app.services.geo.geo_writing_policy import content_quality_to_dict, score_content_quality
from app.services.geo.multi_engine_rank_registry import all_traffic_engines, engine_stat_keys

_KEYWORD_TYPE_TO_CLASS = {
    "product": "industry",
    "supply": "industry",
    "local": "industry",
    "project": "demand",
    "price": "demand",
    "manufacturer": "brand",
}

_CLASS_LABELS = {
    "industry": "行业词",
    "brand": "品牌词",
    "competitor": "竞品词",
    "demand": "需求词",
}

_AI_ENGINE_IDS = frozenset(
    e.id for e in all_traffic_engines() if e.family in ("ai_search", "ai_browser", "llm_chat")
)


def _infer_word_class(keyword: str, keyword_type: str | None = None) -> str:
    """_infer_word_class。

    参数说明：
    :param keyword: 参数 keyword
    :param keyword_type: 参数 keyword_type
    :return: 返回处理结果。
    """
    if keyword_type and keyword_type in _KEYWORD_TYPE_TO_CLASS:
        return _KEYWORD_TYPE_TO_CLASS[keyword_type]
    text = (keyword or "").lower()
    if any(x in text for x in ("竞品", "对比", "vs", "代替", "替代")):
        return "competitor"
    if any(x in text for x in ("品牌", "厂家", "官方", "直营")):
        return "brand"
    if any(x in text for x in ("价格", "多少钱", "报价", "采购", "批发", "需求", "怎么选")):
        return "demand"
    return "industry"


def _serialize_entry(row: GrowthKeywordEntry) -> dict[str, Any]:
    """_serialize_entry。

    参数说明：
    :param row: 参数 row
    :return: 返回处理结果。
    """
    return {
        "id": str(row.id),
        "tenant_id": row.tenant_id,
        "keyword": row.keyword,
        "word_class": row.word_class,
        "word_class_label": _CLASS_LABELS.get(row.word_class, row.word_class),
        "search_volume": row.search_volume or 0,
        "competition": row.competition or 0,
        "source": row.source or "manual",
        "notes": row.notes,
        "is_active": bool(row.is_active),
    }


def hot_keywords_overview(db: Session, *, tenant_id: str | None = None) -> dict[str, Any]:
    """聚合平台词库 + 行业词 + 生成词，按四类呈现。"""
    buckets: dict[str, list[dict[str, Any]]] = {k: [] for k in WORD_CLASSES}
    seen: set[str] = set()
    def _push(word_class: str, keyword: str, **extra: Any) -> None:
        """_push。

        参数说明：
        :param word_class: 参数 word_class
        :param keyword: 参数 keyword
        :param **extra: 参数 **extra
        :return: 返回处理结果。
        """
        key = f"{word_class}:{keyword.strip().lower()}"
        if not keyword.strip() or key in seen:
            return
        seen.add(key)
        buckets[word_class].append(
            {
                "keyword": keyword.strip(),
                "word_class": word_class,
                "word_class_label": _CLASS_LABELS[word_class],
                **extra,
            }
        )

    q = db.query(GrowthKeywordEntry).filter(GrowthKeywordEntry.is_active.is_(True))
    if tenant_id:
        q = q.filter(
            (GrowthKeywordEntry.tenant_id == tenant_id)
            | (GrowthKeywordEntry.tenant_id.is_(None))
        )
    for row in q.order_by(GrowthKeywordEntry.search_volume.desc()).limit(200).all():
        wc = row.word_class if row.word_class in WORD_CLASSES else "industry"
        _push(
            wc,
            row.keyword,
            id=str(row.id),
            search_volume=row.search_volume or 0,
            source=row.source or "library",
        )

    for ik in (
        db.query(IndustryKeyword)
        .filter(IndustryKeyword.is_active.is_(True))
        .order_by(IndustryKeyword.search_volume.desc())
        .limit(120)
        .all()
    ):
        wc = _infer_word_class(ik.keyword, ik.keyword_type)
        _push(
            wc,
            ik.keyword,
            search_volume=ik.search_volume or 0,
            source="industry_pool",
        )

    for gk in (
        db.query(GeneratedKeyword)
        .filter(GeneratedKeyword.is_valid.is_(True))
        .order_by(GeneratedKeyword.search_volume.desc())
        .limit(80)
        .all()
    ):
        _push(
            "industry",
            gk.keyword,
            search_volume=gk.search_volume or 0,
            source="region_combo",
        )

    for wc in WORD_CLASSES:
        buckets[wc].sort(key=lambda x: x.get("search_volume", 0), reverse=True)
        buckets[wc] = buckets[wc][:30]

    totals = {wc: len(buckets[wc]) for wc in WORD_CLASSES}
    return {
        "classes": WORD_CLASSES,
        "class_labels": _CLASS_LABELS,
        "totals": totals,
        "total": sum(totals.values()),
        "buckets": buckets,
    }


def list_keyword_library(
    db: Session,
    *,
    tenant_id: str | None = None,
    word_class: str | None = None,
) -> list[dict[str, Any]]:
    """list_keyword_library。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param word_class: 参数 word_class
    :return: 返回处理结果。
    """
    q = db.query(GrowthKeywordEntry).filter(GrowthKeywordEntry.is_active.is_(True))
    if tenant_id:
        q = q.filter(
            (GrowthKeywordEntry.tenant_id == tenant_id)
            | (GrowthKeywordEntry.tenant_id.is_(None))
        )
    if word_class and word_class in WORD_CLASSES:
        q = q.filter(GrowthKeywordEntry.word_class == word_class)
    rows = q.order_by(
        GrowthKeywordEntry.word_class.asc(),
        GrowthKeywordEntry.search_volume.desc(),
    ).all()
    return [_serialize_entry(r) for r in rows]


def create_keyword_entry(
    db: Session,
    *,
    keyword: str,
    word_class: str,
    tenant_id: str | None = None,
    search_volume: int = 0,
    competition: int = 0,
    source: str = "manual",
    notes: str | None = None,
) -> dict[str, Any]:
    """create_keyword_entry。

    参数说明：
    :param db: 参数 db
    :param keyword: 参数 keyword
    :param word_class: 参数 word_class
    :param tenant_id: 参数 tenant_id
    :param search_volume: 参数 search_volume
    :param competition: 参数 competition
    :param source: 参数 source
    :param notes: 参数 notes
    :return: 返回处理结果。
    """
    wc = word_class if word_class in WORD_CLASSES else _infer_word_class(keyword)
    text = (keyword or "").strip()
    if not text:
        raise ValueError("关键词不能为空")
    exists = (
        db.query(GrowthKeywordEntry)
        .filter(
            GrowthKeywordEntry.keyword == text,
            GrowthKeywordEntry.word_class == wc,
            GrowthKeywordEntry.tenant_id == tenant_id,
        )
        .first()
    )
    if exists:
        raise ValueError("该分类下关键词已存在")
    row = GrowthKeywordEntry(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        keyword=text,
        word_class=wc,
        search_volume=max(0, int(search_volume or 0)),
        competition=max(0, min(100, int(competition or 0))),
        source=source or "manual",
        notes=notes,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _serialize_entry(row)


def delete_keyword_entry(db: Session, entry_id: str) -> None:
    """delete_keyword_entry。

    参数说明：
    :param db: 参数 db
    :param entry_id: 参数 entry_id
    :return: 返回处理结果。
    """
    row = db.query(GrowthKeywordEntry).filter(GrowthKeywordEntry.id == entry_id).first()
    if not row:
        raise ValueError("关键词不存在")
    row.is_active = False
    db.commit()


def _score_logic_completeness(title: str, body: str) -> dict[str, Any]:
    """_score_logic_completeness。

    参数说明：
    :param title: 参数 title
    :param body: 参数 body
    :return: 返回处理结果。
    """
    text = (body or "").strip()
    paragraphs = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    has_title = bool((title or "").strip())
    has_intro = len(paragraphs) >= 1 and len(paragraphs[0]) >= 40
    has_body = len(paragraphs) >= 2
    has_cta = bool(re.search(r"(联系|咨询|报价|下单|了解更多|立即|电话|微信)", text))
    has_list_or_table = bool(re.search(r"^[\-\*•]\s|^\d+\.\s|\|", text, re.M))
    checks = {
        "has_title": has_title,
        "has_intro": has_intro,
        "has_body": has_body,
        "has_cta": has_cta,
        "has_structure": has_list_or_table or len(paragraphs) >= 3,
    }
    score = sum(1 for v in checks.values() if v) / max(len(checks), 1)
    issues = []
    if not has_intro:
        issues.append("缺少清晰开篇段落")
    if not has_body:
        issues.append("正文段落过少，逻辑展开不足")
    if not has_cta:
        issues.append("缺少行动号召（联系/咨询/报价等）")
    if not checks["has_structure"]:
        issues.append("建议增加列表或分段结构，提升可读性")
    return {"score": round(score, 3), "checks": checks, "issues": issues}


def inspect_content_quality(
    db: Session,
    *,
    title: str,
    body: str,
    keywords: list[str] | None = None,
) -> dict[str, Any]:
    """统一内容质检：合规 + SEO 结构 + GEO/AI 适配 + 逻辑完整度。"""
    full_text = f"{title or ''}\n{body or ''}".strip()
    compliance = ComplianceScanner(db).scan_text(full_text)
    seo = score_content(title or "", body or "", keywords or [])
    geo = content_quality_to_dict(score_content_quality(body or "", intent="b2b"))
    logic = _score_logic_completeness(title or "", body or "")
    high_risk = int(compliance.get("high_severity_count") or 0)
    seo_total = int(seo.get("total_score") or 0)
    geo_pass = bool(geo.get("passed"))
    logic_ok = logic["score"] >= 0.6
    blockers: list[str] = []
    if high_risk > 0:
        blockers.append(f"广告法高风险违禁词 {high_risk} 处")
    if not geo_pass:
        blockers.extend(geo.get("reasons") or ["GEO/AI 适配未达标"])
    if seo_total < 55:
        blockers.append(f"SEO 结构分偏低（{seo_total}/100）")
    if not logic_ok:
        blockers.extend(logic.get("issues") or ["逻辑完整度不足"])

    passed = len(blockers) == 0
    grade = "A" if passed and seo_total >= 75 else "B" if passed else "C" if seo_total >= 45 else "D"
    return {
        "passed": passed,
        "grade": grade,
        "blockers": blockers,
        "compliance": {
            "total_issues": compliance.get("total_issues", 0),
            "high_severity_count": high_risk,
            "violations": (compliance.get("violations") or [])[:20],
            "suggestions": (compliance.get("suggestions") or [])[:10],
        },
        "seo": seo,
        "geo_ai": geo,
        "logic": logic,
        "summary": "可发布" if passed else "需修改后再发",
    }


def ai_traffic_overview(db: Session) -> dict[str, Any]:
    """AI/搜索平台引流与收录监测汇总（收录 + 排名 + 平台能力）。"""
    engines = all_traffic_engines()
    inclusion_rows = db.query(InclusionStatus).all()
    by_engine: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "included": 0})
    for row in inclusion_rows:
        eng = (row.search_engine or "unknown").lower()
        by_engine[eng]["total"] += 1
        if row.is_included:
            by_engine[eng]["included"] += 1

    ai_cards, behavior_analytics, classic_cards, domestic_crawl, domestic_search, global_search, headless_snap, overall_rate, platform_cards, probe_ready_count, total_included, total_tracked = _build_traffic_platform_cards(db, engines, by_engine)
    return {
        "summary": {
            "platforms": len(platform_cards),
            "ai_platforms": len(ai_cards),
            "search_platforms": len(classic_cards),
            "probe_ready": probe_ready_count,
            "tracked_urls": total_tracked,
            "indexed_urls": total_included,
            "overall_inclusion_rate": overall_rate,
            "headless_probe_saved_at": (headless_snap or {}).get("saved_at"),
            "domestic_crawl_status": domestic_crawl.get("status"),
            "behavior_analytics_status": behavior_analytics.get("status"),
        },
        "domestic_crawl": domestic_crawl,
        "behavior_analytics": behavior_analytics,
        "ai_platforms": ai_cards,
        "search_platforms": classic_cards,
        "search_platforms_domestic": domestic_search,
        "search_platforms_global": global_search,
        "note": (
            f"共 {len(platform_cards)} 个监测通道，{probe_ready_count} 个已接 API/收录探针；"
            "其余显示为探索中/待接入，收录数为 0 表示尚未配置探针或未产生检测任务。"
            "收入/引流 ROI 需结合站点 UTM 与询盘归因。"
        ),
    }


def _engine_stats(by_engine, engine_id: str) -> dict[str, int]:
    """聚合单引擎的收录总数与已收录数。"""
    total = 0
    included = 0
    for key in engine_stat_keys(engine_id):
        stats = by_engine.get(key, {"total": 0, "included": 0})
        total += stats["total"]
        included += stats["included"]
    return {"total": total, "included": included}


def _load_ranking_by_engine(db) -> dict[str, list[dict[str, Any]]]:
    """加载最近 500 条关键词排名，按搜索引擎分组。"""
    ranking_rows = (
        db.query(KeywordRanking)
        .order_by(KeywordRanking.updated_at.desc())
        .limit(500)
        .all()
    )
    ranking_by_engine: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in ranking_rows:
        eng = (r.search_engine or "unknown").lower()
        ranking_by_engine[eng].append(
            {
                "keyword": r.keyword,
                "rank": r.current_position,
                "url": r.target_url,
            }
        )
    return ranking_by_engine


def _load_traffic_auxiliary_data(db):
    """加载无头探针快照、国内电商爬虫与行为分析摘要。"""
    from app.services.geo.headless_rank_probe_service import (
        load_headless_probe_snapshot,
        merge_snapshot_into_traffic_cards,
    )
    from app.services.crawlers.ecommerce_crawlers_smart import domestic_crawl_summary_for_traffic
    from app.services.analytics.user_action_analytics_smart import conversion_summary_for_growth
    headless_snap = load_headless_probe_snapshot(db)
    domestic_crawl = domestic_crawl_summary_for_traffic()
    behavior_analytics = conversion_summary_for_growth()
    return headless_snap, domestic_crawl, behavior_analytics


def _build_traffic_platform_cards(db, engines, by_engine=None):
    """构建各搜索引擎平台卡：收录率、排名快照与流量信号。"""
    if by_engine is None:
        by_engine = {}
    ranking_by_engine = _load_ranking_by_engine(db)
    platform_cards: list[dict[str, Any]] = []
    total_included = 0
    total_tracked = 0
    probe_ready_count = 0
    for eng in engines:
        stats = _engine_stats(by_engine, eng.id)
        total = stats["total"]
        included = stats["included"]
        total_tracked += total
        total_included += included
        if eng.probe_ready:
            probe_ready_count += 1
        rate = round(included / total * 100, 1) if total else 0.0
        ranks = []
        for key in engine_stat_keys(eng.id):
            ranks.extend(ranking_by_engine.get(key, []))
        ranks = ranks[:5]
        platform_cards.append(
            {
                "engine_id": eng.id,
                "name": eng.display_name,
                "family": eng.family,
                "market": eng.market,
                "probe_ready": eng.probe_ready,
                "probe_status_label": eng.probe_status_label,
                "distillation_risk": eng.distillation_risk,
                "inclusion_total": total,
                "inclusion_included": included,
                "inclusion_rate": rate,
                "top_rankings": ranks,
                "traffic_signal": "indexed" if included else ("tracking" if total else "idle"),
            }
        )

    overall_rate = round(total_included / total_tracked * 100, 1) if total_tracked else 0.0
    headless_snap, domestic_crawl, behavior_analytics = _load_traffic_auxiliary_data(db)
    platform_cards = merge_snapshot_into_traffic_cards(platform_cards, headless_snap)
    ai_cards = [c for c in platform_cards if c["engine_id"] in _AI_ENGINE_IDS]
    classic_cards = [c for c in platform_cards if c["engine_id"] not in _AI_ENGINE_IDS]
    domestic_search = [c for c in classic_cards if c["market"] == "domestic"]
    global_search = [c for c in classic_cards if c["market"] == "global"]
    return (ai_cards, behavior_analytics, classic_cards, domestic_crawl, domestic_search, global_search, headless_snap, overall_rate, platform_cards, probe_ready_count, total_included, total_tracked)


def growth_dashboard(db: Session, *, tenant_id: str | None = None) -> dict[str, Any]:
    """增长工具总览 — 供首页 Tab 一次拉取。"""
    from app.services.agent_loop.run_repository import latest_run_summary
    from app.services.agent_loop.workflow_presets import list_presets
    hot = hot_keywords_overview(db, tenant_id=tenant_id)
    library = list_keyword_library(db, tenant_id=tenant_id)
    traffic = ai_traffic_overview(db)
    last_run = latest_run_summary(db, tenant_id=tenant_id)
    idle_probe_count = sum(
        1
        for c in (traffic.get("ai_platforms") or []) + (traffic.get("search_platforms") or [])
        if c.get("traffic_signal") == "idle"
    )
    return {
        "keywords": {
            "total": hot.get("total", 0),
            "totals": hot.get("totals", {}),
            "library_count": len(library),
        },
        "traffic": traffic.get("summary") or {},
        "traffic_idle_count": idle_probe_count,
        "last_agent_run": last_run,
        "presets": list_presets(),
        "quick_actions": [
            {"id": "full_diagnosis", "label": "全链路诊断", "tab": "autopilot"},
            {"id": "traffic_audit", "label": "引流审计", "tab": "traffic"},
            {"id": "quality", "label": "内容质检", "tab": "quality"},
        ],
    }
