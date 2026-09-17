# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""GitHub 生态侦察 — 代用户翻找开源项目，映射系统短板，推送 PM Inbox（不自动安装）。

研究员/ECC 职责：按 catalog 缺口 + 关键词搜索 GitHub，去重已收录 curated，
产出 Sidecar/参考接入建议；用户只需在司令部 Inbox 点「同意排期」。
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

import httpx

from app.core.cache import redis_client
from app.core.config import settings
from app.services.foreign_trade_ecosystem_service import load_ecosystem_catalog
from app.services.hermes.maintenance_constitution import assert_maintenance_action

logger = logging.getLogger("uj-admin.github_ecosystem_scout")

SCOUT_SNAPSHOT_KEY = "hermes:github_ecosystem_scout:latest"
SCOUT_HOUR_PREFIX = "hermes:github_ecosystem_scout:hour:"
SCOUT_INBOX_DEDUPE_PREFIX = "hermes:github_scout:inbox:"

# 已知已 Sidecar 并入主仓的 registry 路径（存在即视为 integrated）
_INTEGRATED_REGISTRY_MARKERS: tuple[tuple[str, str], ...] = (
    ("DropsDevopsOrg/ECommerceCrawlers", "backend/app/services/crawlers/ecommerce_crawlers_registry.py"),
    (
        "oeljeklaus-you/UserActionAnalyzePlatform",
        "backend/app/services/analytics/user_action_analytics_registry.py",
    ),
)

_SPAM_PATTERN = re.compile(
    r"(vpn|shadowsocks|clash|电子书|ebook|破解|crack|proxy pool|机场)",
    re.IGNORECASE,
)

# 基础检索词（与 catalog 缺口 lane 对齐）
_BASE_SCOUT_QUERIES: tuple[dict[str, Any], ...] = (
    {
        "query": "外贸 B2B stars:>30",
        "gap_ids": ["GW-L", "prospect_enrichment"],
        "label": "外贸找客与潜客",
        "lane": "GW-L",
    },
    {
        "query": "ecommerce crawler python stars:>200",
        "gap_ids": ["domestic_crawl_seo_osint"],
        "label": "电商/资讯爬虫",
        "lane": "GW-G",
    },
    {
        "query": "user behavior analytics spark ecommerce stars:>100",
        "gap_ids": ["page_conversion_funnel_hot_products"],
        "label": "页面转化与行为分析",
        "lane": "GW-R",
    },
    {
        "query": "B2B CRM foreign trade inquiry stars:>20",
        "gap_ids": ["GW-L-PL-01"],
        "label": "询盘 CRM 管道",
        "lane": "GW-L",
    },
    {
        "query": "GEO AEO AI citation SEO stars:>20",
        "gap_ids": ["GW-G-GEO-DASH"],
        "label": "GEO/AEO 可见性",
        "lane": "GW-G",
    },
    {
        "query": "trade agent langgraph B2B stars:>10",
        "gap_ids": ["full_chain_trade_agent"],
        "label": "全链路贸易 Agent",
        "lane": "GW-R",
    },
    {
        "query": "prospect enrichment OSINT B2B stars:>15",
        "gap_ids": ["prospect_enrichment", "osint_background_check"],
        "label": "潜客背调 OSINT",
        "lane": "GW-L",
    },
    {
        "query": "linkedin automation B2B outreach stars:>50",
        "gap_ids": ["GW-L"],
        "label": "LinkedIn outbound",
        "lane": "GW-L",
    },
)


def _repo_root() -> Path:
    """_repo_root。
    :return: 返回处理结果。
    """
    return Path(__file__).resolve().parents[4]


def _scout_enabled() -> bool:
    """_scout_enabled。
    :return: 返回处理结果。
    """
    flag = getattr(settings, "GITHUB_ECOSYSTEM_SCOUT_ENABLED", None)
    if flag is not None:
        return bool(flag)
    return (settings.ENVIRONMENT or "").strip().lower() in ("production", "development")


def _github_headers() -> dict[str, str]:
    """_github_headers。
    :return: 返回处理结果。
    """
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "UJ-Hermes-GitHubScout/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = getattr(settings, "GITHUB_TOKEN", None) or ""
    if token.strip():
        headers["Authorization"] = f"Bearer {token.strip()}"
    return headers


def _curated_repo_set() -> set[str]:
    """_curated_repo_set。
    :return: 返回处理结果。
    """
    cat = load_ecosystem_catalog()
    repos: set[str] = set()
    for row in cat.get("github_curated") or []:
        repo = (row.get("repo") or "").strip().lower()
        if repo:
            repos.add(repo)
    return repos


def _integrated_repo_set() -> set[str]:
    """_integrated_repo_set。
    :return: 返回处理结果。
    """
    integrated: set[str] = set()
    root = _repo_root()
    for repo, marker in _INTEGRATED_REGISTRY_MARKERS:
        if (root / marker).is_file():
            integrated.add(repo.lower())
    return integrated


def _build_dynamic_queries() -> list[dict[str, Any]]:
    """从 catalog open_gaps 追加关键词（不重复基础 query）。"""
    cat = load_ecosystem_catalog()
    queries = [dict(q) for q in _BASE_SCOUT_QUERIES]
    seen_q = {q["query"].lower() for q in queries}
    gap_keywords: list[tuple[str, str, str]] = [
        ("GW-S-MAT-01", "social media matrix publish automation", "GW-S"),
        ("GW-P-GSC-02", "google ads attribution UTM webhook", "GW-P"),
    ]
    for gap_id, kw, lane in gap_keywords:
        q = f"{kw} stars:>10"
        if q.lower() in seen_q:
            continue
        queries.append(
            {
                "query": q,
                "gap_ids": [gap_id],
                "label": gap_id,
                "lane": lane,
            }
        )
        seen_q.add(q.lower())

    for gap in (cat.get("open_gaps_p0") or []) + (cat.get("open_gaps_p1") or []):
        title = (gap.get("title") or "")[:40]
        lane = gap.get("lane") or "GW-PM"
        gid = gap.get("id") or ""
        if "UTM" in title or "归因" in title:
            q = "marketing attribution UTM B2B stars:>15"
        elif "MEDDPICC" in title or "CRM" in title or "询盘" in title:
            q = "B2B inquiry CRM pipeline stars:>15"
        elif "GEO" in title or "AEO" in title:
            q = "generative engine optimization AEO stars:>10"
        elif "矩阵" in title or "OAuth" in title:
            q = "social media scheduler API stars:>50"
        else:
            continue
        if q.lower() in seen_q:
            continue
        queries.append({"query": q, "gap_ids": [gid], "label": title, "lane": lane})
        seen_q.add(q.lower())

    return queries


def _is_spam_repo(full_name: str, description: str | None) -> bool:
    """_is_spam_repo。

    参数说明：
    :param full_name: 参数 full_name
    :param description: 参数 description
    :return: 返回处理结果。
    """
    blob = f"{full_name} {description or ''}"
    return bool(_SPAM_PATTERN.search(blob))


def _suggest_integrate_plan(description: str | None, *, stars: int) -> str:
    """_suggest_integrate_plan。

    参数说明：
    :param description: 参数 description
    :param stars: 参数 stars
    :return: 返回处理结果。
    """
    desc = (description or "").lower()
    if any(k in desc for k in ("spark", "hadoop", "flink", "java")):
        return "sidecar_env — Spark/Java 外置 vendor + 网关，禁止 fork 进 backend/"
    if any(k in desc for k in ("crawler", "spider", "scrapy")):
        return "sidecar_env — 爬虫 Sidecar + 合规门禁，见 deploy/examples"
    if any(k in desc for k in ("crm", "inquiry", "pipeline")):
        return "reference_only — schema/字段对标，不整仓 fork"
    if any(k in desc for k in ("agent", "langgraph", "llm")):
        return "reference_only — Skill/workflow 清单并入 Hermes，不自动群发"
    if stars >= 500:
        return "sidecar_env — 高星项目优先 Sidecar 试点，须 ECC 评审"
    return "reference_only — 研究员收录至 catalog github_curated"


def search_github_repositories(query: str, *, per_page: int = 5) -> list[dict[str, Any]]:
    """GitHub Search API — 失败返回空列表，不抛到上层。"""
    url = "https://api.github.com/search/repositories"
    try:
        with httpx.Client(timeout=20, headers=_github_headers()) as client:
            resp = client.get(url, params={"q": query, "sort": "stars", "order": "desc", "per_page": per_page})
            if resp.status_code == 403:
                logger.warning("GitHub scout rate limited for query=%s", query[:60])
                return []
            resp.raise_for_status()
            payload = resp.json()
    except Exception as exc:
        logger.warning("GitHub scout search failed q=%s: %s", query[:60], exc)
        return []

    items: list[dict[str, Any]] = []
    for row in payload.get("items") or []:
        if not isinstance(row, dict):
            continue
        full_name = (row.get("full_name") or "").strip()
        if not full_name:
            continue
        items.append(
            {
                "repo": full_name,
                "stars": int(row.get("stargazers_count") or 0),
                "description": (row.get("description") or "")[:320],
                "html_url": row.get("html_url") or f"https://github.com/{full_name}",
                "language": row.get("language") or "",
                "updated_at": row.get("updated_at") or "",
            }
        )
    return items


def run_github_ecosystem_scout(*, max_queries: int = 6, per_query: int = 4) -> dict[str, Any]:
    """执行一轮 GitHub 侦察；只读，不写业务表、不 clone。"""
    assert_maintenance_action("read_probe")
    if not _scout_enabled():
        return {"skipped": True, "reason": "github_scout_disabled"}

    curated = _curated_repo_set()
    integrated = _integrated_repo_set()
    queries = _build_dynamic_queries()[:max_queries]
    all_candidates: list[dict[str, Any]] = []
    new_candidates: list[dict[str, Any]] = []
    errors: list[str] = []
    queries_run = 0
    for spec in queries:
        q = spec["query"]
        rows = search_github_repositories(q, per_page=per_query)
        queries_run += 1
        if not rows and q:
            errors.append(f"empty_or_failed:{q[:40]}")
        for row in rows:
            repo_key = row["repo"].lower()
            if _is_spam_repo(row["repo"], row.get("description")):
                continue
            in_catalog = repo_key in curated
            is_integrated = repo_key in integrated
            plan = _suggest_integrate_plan(row.get("description"), stars=row["stars"])
            candidate = {
                **row,
                "scout_query": q,
                "scout_label": spec.get("label"),
                "fills_gap_ids": list(spec.get("gap_ids") or []),
                "lane": spec.get("lane") or "GW-PM",
                "in_catalog": in_catalog,
                "already_integrated": is_integrated,
                "integrate_plan": plan,
                "is_new_discovery": not in_catalog and not is_integrated,
            }
            all_candidates.append(candidate)
            if candidate["is_new_discovery"] and row["stars"] >= 30:
                new_candidates.append(candidate)

    # 去重：同 repo 保留最高星
    by_repo: dict[str, dict[str, Any]] = {}
    for c in all_candidates:
        key = c["repo"].lower()
        prev = by_repo.get(key)
        if not prev or c["stars"] > prev["stars"]:
            by_repo[key] = c
    deduped = sorted(by_repo.values(), key=lambda x: x["stars"], reverse=True)
    new_deduped = [c for c in deduped if c.get("is_new_discovery")][:12]
    body: dict[str, Any] = {
        "scouted_at": datetime.now(timezone.utc).isoformat(),
        "queries_run": queries_run,
        "queries_total_available": len(_build_dynamic_queries()),
        "curated_count": len(curated),
        "integrated_count": len(integrated),
        "candidates_total": len(deduped),
        "new_candidates": new_deduped,
        "new_candidates_count": len(new_deduped),
        "top_curated_hits": [c for c in deduped if c.get("in_catalog")][:6],
        "fetch_errors": errors[:8],
        "user_message_zh": _user_message_zh(new_deduped),
        "mode": "live" if queries_run else "skipped",
    }
    save_scout_snapshot(body)
    return body


def _user_message_zh(new_candidates: list[dict[str, Any]]) -> str:
    """_user_message_zh。

    参数说明：
    :param new_candidates: 参数 new_candidates
    :return: 返回处理结果。
    """
    if not new_candidates:
        return (
            "专家已代您扫描 GitHub，暂无新的高价值开源项目需您亲自翻找。"
            "已收录项目见生态目录；Sidecar 已接入项可在增长工具里一键探测。"
        )
    names = "、".join(c["repo"].split("/")[-1] for c in new_candidates[:3])
    return (
        f"专家已在 GitHub 发现 {len(new_candidates)} 个可补齐短板的新项目（如 {names}）。"
        "请打开 Hermes 司令部 → Inbox，点「同意排期」即可，无需您自己搜 repo。"
    )


def save_scout_snapshot(body: dict[str, Any]) -> dict[str, Any]:
    """save_scout_snapshot。

    参数说明：
    :param body: 参数 body
    :return: 返回处理结果。
    """
    assert_maintenance_action("write_patrol_snapshot")
    if redis_client:
        redis_client.set(SCOUT_SNAPSHOT_KEY, json.dumps(body, ensure_ascii=False), ex=86400 * 14)
    return body


def load_scout_snapshot() -> dict[str, Any] | None:
    """load_scout_snapshot。
    :return: 返回处理结果。
    """
    assert_maintenance_action("read_probe")
    if not redis_client:
        return None
    raw = redis_client.get(SCOUT_SNAPSHOT_KEY)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


def scout_summary_for_signals() -> dict[str, Any]:
    """collect_signals 用：优先读缓存，无缓存则返回占位。"""
    snap = load_scout_snapshot()
    if snap:
        return {
            "new_candidates_count": snap.get("new_candidates_count") or 0,
            "scouted_at": snap.get("scouted_at"),
            "user_message_zh": snap.get("user_message_zh"),
            "top_new": [
                {"repo": c.get("repo"), "stars": c.get("stars"), "lane": c.get("lane")}
                for c in (snap.get("new_candidates") or [])[:3]
            ],
        }
    return {"new_candidates_count": 0, "scouted_at": None, "note": "await_first_scout_cycle"}


def _hour_slot_key(at: datetime | None = None) -> str:
    """_hour_slot_key。

    参数说明：
    :param at: 参数 at
    :return: 返回处理结果。
    """
    now = at or datetime.now(timezone.utc)
    return f"{SCOUT_HOUR_PREFIX}{now.strftime('%Y%m%d%H')}"


def _scout_already_ran_this_hour(*, force: bool) -> bool:
    """_scout_already_ran_this_hour。

    参数说明：
    :param force: 参数 force
    :return: 返回处理结果。
    """
    if force or not redis_client:
        return False
    return bool(redis_client.get(_hour_slot_key()))


def _mark_scout_hour() -> None:
    """_mark_scout_hour。
    :return: 返回处理结果。
    """
    if redis_client:
        redis_client.set(_hour_slot_key(), "1", ex=7200)


def _inbox_dedupe_hit(repo: str) -> bool:
    """_inbox_dedupe_hit。

    参数说明：
    :param repo: 参数 repo
    :return: 返回处理结果。
    """
    if not redis_client:
        return False
    key = f"{SCOUT_INBOX_DEDUPE_PREFIX}{repo.lower()}"
    if redis_client.get(key):
        return True
    redis_client.set(key, "1", ex=86400 * 7)
    return False


def compose_scout_brief(candidate: dict[str, Any]) -> dict[str, Any]:
    """单条新发现 → ResearchBrief 形状（供 Inbox）。"""
    now = datetime.now(timezone.utc)
    repo = candidate.get("repo") or "unknown"
    stars = candidate.get("stars") or 0
    gaps = "、".join(candidate.get("fills_gap_ids") or []) or "生态短板"
    finding = (
        f"【GitHub 侦察】发现 {repo}（★{stars}），可补齐：{gaps}。"
        f"建议：{candidate.get('integrate_plan') or 'reference_only'}。"
        f"说明：{(candidate.get('description') or '')[:180]}"
        " — 请您在 Inbox 点同意，ECC 将评审 Sidecar 方案；禁止自动 clone/安装。"
    )
    impact = "high" if stars >= 500 else "medium" if stars >= 100 else "low"
    return {
        "brief_id": f"{now.strftime('%Y%m%d%H')}:github_scout:{repo.replace('/', '-')[:40]}",
        "topic_key": "github_ecosystem_scout",
        "topic_label": "GitHub 生态侦察（专家代搜）",
        "lane": candidate.get("lane") or "GW-PM",
        "category": "paper",
        "finding": finding,
        "evidence": [
            {"type": "github_repo", "ref": repo, "url": candidate.get("html_url"), "stars": stars},
            {"type": "integrate_plan", "ref": candidate.get("integrate_plan")},
        ],
        "impact": impact,
        "confidence": "medium",
        "suggested_tasks": [
            {
                "id_hint": "GW-R-AGENT-02",
                "title": f"评审并登记 {repo} 至 github_curated",
                "lane": candidate.get("lane") or "GW-PM",
            }
        ],
        "forbidden_auto_actions": ["code_merge", "config_mutate", "auto_install_repo"],
        "generated_at": now.isoformat(),
    }


def append_scout_discoveries_to_inbox(scout: dict[str, Any], *, max_items: int = 3) -> int:
    """新高星项目写入 PM Inbox；返回写入条数。"""
    from app.services.hermes.hermes_continuous_iteration_service import route_departments
    from app.services.hermes.research_brief_service import append_brief_inbox
    assert_maintenance_action("write_patrol_snapshot")
    queued = 0
    for cand in scout.get("new_candidates") or []:
        if queued >= max_items:
            break
        repo = cand.get("repo") or ""
        if not repo or _inbox_dedupe_hit(repo):
            continue
        stars = int(cand.get("stars") or 0)
        if stars < 80:
            continue
        brief = compose_scout_brief(cand)
        routing = route_departments(brief, ecc_reviews=[])
        append_brief_inbox(brief, ecc_verdict="pass", department_routing=routing)
        queued += 1
    return queued


def run_github_scout_cycle(*, force: bool = False, max_queries: int = 6) -> dict[str, Any]:
    """带小时去重的侦察 + Inbox 推送。"""
    if not _scout_enabled():
        return {"skipped": True, "reason": "github_scout_disabled"}
    if _scout_already_ran_this_hour(force=force):
        snap = load_scout_snapshot()
        return {"skipped": True, "reason": "already_ran_this_hour", "latest": snap}

    scout = run_github_ecosystem_scout(max_queries=max_queries)
    inbox_queued = append_scout_discoveries_to_inbox(scout)
    _mark_scout_hour()
    scout["inbox_queued"] = inbox_queued
    save_scout_snapshot(scout)
    return scout
