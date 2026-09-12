"""GEO 技术雷达 v2 — 定时抓取 GEO/SEO 最新论文、论坛、白帽技术、开源工具。

抓取源分类：
  1. 学术论文 — arXiv GEO/LLM-SEO 相关论文
  2. 行业博客 — Moz, Ahrefs, Search Engine Journal, Backlinko
  3. 开源技术 — GitHub trending SEO/GEO 工具
  4. AI 厂商动态 — OpenAI/Google/Anthropic 搜索功能更新
  5. 白帽技术 — Google Search Central, Schema.org, LLMs.txt 规范
  6. 中文社区 — 百度搜索资源平台, 知乎 SEO 专栏

技术发现经 AI 分析后，自动更新 geo_writing_policy.py 的战术版本。
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx

from app.services.geo.geo_writing_policy import TACTICS_VERSION

logger = logging.getLogger("uj-admin.tech_radar")

# ──────────────────────────────────────────────
# 数据源定义
# ──────────────────────────────────────────────

@dataclass
class RadarSource:
    name: str
    url: str
    kind: str  # rss | api | html | github
    category: str  # paper | blog | opensource | ai_vendor | whitehat | cn_community
    description: str


RADAR_SOURCES: list[RadarSource] = [
    # ═══════════════════════════════════════════
    # 1. 学术论文（GEO/LLM-SEO 核心研究）
    # ═══════════════════════════════════════════
    RadarSource(
        name="arxiv_geo_princeton",
        url="https://export.arxiv.org/api/query?search_query=ti:%22generative+engine+optimization%22&sortBy=submittedDate&sortOrder=descending&max_results=8",
        kind="api",
        category="paper",
        description="arXiv GEO — Princeton KDD 2024 论文后续研究",
    ),
    RadarSource(
        name="arxiv_llm_search",
        url="https://export.arxiv.org/api/query?search_query=ti:%22LLM%22+AND+abs:ranking+AND+abs:search&sortBy=submittedDate&sortOrder=descending&max_results=5",
        kind="api",
        category="paper",
        description="arXiv LLM 搜索排名研究",
    ),
    RadarSource(
        name="arxiv_ai_overview",
        url="https://export.arxiv.org/api/query?search_query=ti:%22AI+search%22+AND+abs:optimization&sortBy=submittedDate&sortOrder=descending&max_results=5",
        kind="api",
        category="paper",
        description="arXiv AI Overview / SGE 优化研究",
    ),
    RadarSource(
        name="arxiv_answer_engine",
        url="https://export.arxiv.org/api/query?search_query=ti:%22answer+engine+optimization%22&sortBy=submittedDate&sortOrder=descending&max_results=5",
        kind="api",
        category="paper",
        description="arXiv AEO (Answer Engine Optimization) 研究",
    ),

    # ═══════════════════════════════════════════
    # 2. 国际 SEO/GEO 行业博客
    # ═══════════════════════════════════════════
    RadarSource(
        name="moz_blog",
        url="http://feedpress.me/mozblog",
        kind="rss",
        category="blog",
        description="Moz Blog — SEO 行业权威",
    ),
    RadarSource(
        name="search_engine_journal",
        url="https://www.searchenginejournal.com/feed/",
        kind="rss",
        category="blog",
        description="Search Engine Journal — SEO 新闻",
    ),
    RadarSource(
        name="search_engine_land",
        url="https://searchengineland.com/feed",
        kind="rss",
        category="blog",
        description="Search Engine Land — 搜索行业新闻",
    ),
    RadarSource(
        name="backlinko",
        url="https://backlinko.com/feed",
        kind="rss",
        category="blog",
        description="Backlinko — Brian Dean SEO 策略",
    ),
    RadarSource(
        name="ahrefs_blog",
        url="https://ahrefs.com/blog/feed/",
        kind="rss",
        category="blog",
        description="Ahrefs Blog — SEO 数据驱动策略",
    ),
    RadarSource(
        name="semrush_blog",
        url="https://www.semrush.com/blog/feed/",
        kind="rss",
        category="blog",
        description="SEMrush Blog — SEO/内容营销",
    ),
    RadarSource(
        name="yoast_seo",
        url="https://yoast.com/feed/",
        kind="rss",
        category="blog",
        description="Yoast SEO — WordPress SEO 技术",
    ),
    RadarSource(
        name="content_marketing_institute",
        url="https://contentmarketinginstitute.com/feed/",
        kind="rss",
        category="blog",
        description="Content Marketing Institute — 内容策略",
    ),

    # ═══════════════════════════════════════════
    # 3. GEO 专项社区和论坛
    # ═══════════════════════════════════════════
    RadarSource(
        name="reddit_seo",
        url="https://www.reddit.com/r/SEO/top.json?t=week&limit=10",
        kind="api",
        category="forum",
        description="Reddit r/SEO — SEO 社区讨论",
    ),
    RadarSource(
        name="reddit_bigseo",
        url="https://www.reddit.com/r/bigseo/top.json?t=week&limit=10",
        kind="api",
        category="forum",
        description="Reddit r/bigseo — 高级 SEO 讨论",
    ),
    RadarSource(
        name="reddit_geo",
        url="https://www.reddit.com/r/generativeengineoptimization/top.json?t=week&limit=10",
        kind="api",
        category="forum",
        description="Reddit r/generativeengineoptimization — GEO 专项",
    ),
    RadarSource(
        name="webmaster_world",
        url="https://www.webmasterworld.com/rss_news.xml",
        kind="rss",
        category="forum",
        description="WebmasterWorld — 老牌 SEO 论坛",
    ),
    RadarSource(
        name="web_dev_blog",
        url="https://web.dev/static/blog/feed.xml",
        kind="rss",
        category="whitehat",
        description="web.dev — Google 官方 Web 技术博客",
    ),

    # ═══════════════════════════════════════════
    # 4. AI 厂商动态（影响 AI 搜索的更新）
    # ═══════════════════════════════════════════
    RadarSource(
        name="openai_blog",
        url="https://openai.com/blog/rss.xml",
        kind="rss",
        category="ai_vendor",
        description="OpenAI Blog — ChatGPT Search 功能更新",
    ),
    RadarSource(
        name="google_ai_blog",
        url="https://blog.google/technology/ai/rss/",
        kind="rss",
        category="ai_vendor",
        description="Google AI Blog — Gemini/SGE/AI Overview 更新",
    ),
    RadarSource(
        name="google_search_central",
        url="https://developers.google.com/search/blog/feed.xml",
        kind="rss",
        category="whitehat",
        description="Google Search Central — 官方 SEO 指南更新",
    ),
    RadarSource(
        name="anthropic_blog",
        url="https://www.anthropic.com/rss.xml",
        kind="rss",
        category="ai_vendor",
        description="Anthropic Blog — Claude 搜索功能更新",
    ),
    RadarSource(
        name="bing_webmaster",
        url="https://blogs.bing.com/webmaster/feed",
        kind="rss",
        category="whitehat",
        description="Bing Webmaster Blog — Bing 搜索更新",
    ),
    RadarSource(
        name="perplexity_blog",
        url="https://www.perplexity.ai/hub/feed",
        kind="rss",
        category="ai_vendor",
        description="Perplexity Hub — AI 搜索引擎更新",
    ),

    # ═══════════════════════════════════════════
    # 5. 开源 GEO/SEO 工具（GitHub）
    # ═══════════════════════════════════════════
    RadarSource(
        name="github_geo_tools",
        url="https://api.github.com/search/repositories?q=generative+engine+optimization&sort=updated&order=desc",
        kind="github",
        category="opensource",
        description="GitHub GEO 工具",
    ),
    RadarSource(
        name="github_aeo_tools",
        url="https://api.github.com/search/repositories?q=answer+engine+optimization+AEO&sort=stars&order=desc",
        kind="github",
        category="opensource",
        description="GitHub AEO (Answer Engine Optimization) 工具",
    ),
    RadarSource(
        name="github_llms_txt",
        url="https://api.github.com/search/repositories?q=llms.txt+OR+llms-txt&sort=updated&order=desc",
        kind="github",
        category="opensource",
        description="GitHub LLMs.txt 相关项目",
    ),
    RadarSource(
        name="github_seo_tools",
        url="https://api.github.com/search/repositories?q=seo+automation+tool+stars:>50&sort=updated&order=desc",
        kind="github",
        category="opensource",
        description="GitHub SEO 自动化工具",
    ),
    RadarSource(
        name="github_schema_markup",
        url="https://api.github.com/search/repositories?q=schema+markup+structured+data+seo&sort=stars&order=desc",
        kind="github",
        category="opensource",
        description="GitHub Schema Markup 工具",
    ),

    # ═══════════════════════════════════════════
    # 6. 白帽技术规范
    # ═══════════════════════════════════════════
    RadarSource(
        name="schema_org",
        url="https://schema.org/docs/releases.html",
        kind="html",
        category="whitehat",
        description="Schema.org 规范更新",
    ),
    RadarSource(
        name="llms_txt_spec",
        url="https://llmstxt.org/",
        kind="html",
        category="whitehat",
        description="LLMs.txt 官方规范",
    ),

    # ═══════════════════════════════════════════
    # 7. GEO 专项研究资源
    # ═══════════════════════════════════════════
    RadarSource(
        name="awesome_geo",
        url="https://api.github.com/repos/amplifying-ai/awesome-generative-engine-optimization",
        kind="github",
        category="geo_resource",
        description="Awesome GEO — 最全 GEO 资源合集 (449★)",
    ),
    RadarSource(
        name="awesome_geo_luka",
        url="https://api.github.com/repos/luka2chat/awesome-geo",
        kind="github",
        category="geo_resource",
        description="Awesome GEO — 另一份 GEO 资源列表 (142★)",
    ),
    RadarSource(
        name="awesome_geo_david",
        url="https://api.github.com/repos/DavidHuji/Awesome-GEO",
        kind="github",
        category="geo_resource",
        description="Awesome GEO — 学术向 GEO 资源 (113★)",
    ),
    RadarSource(
        name="geo_optimizer_skill",
        url="https://api.github.com/repos/Auriti-Labs/geo-optimizer-skill",
        kind="github",
        category="geo_resource",
        description="GEO Optimizer Skill — AEO/GEO 开源优化工具 (598★)",
    ),
    RadarSource(
        name="gtm_engineer_skills",
        url="https://api.github.com/repos/onvoyage-ai/gtm-engineer-skills",
        kind="github",
        category="geo_resource",
        description="GTM Engineer — AEO/GEO Claude Code Skill (1252★)",
    ),
    RadarSource(
        name="auto_geo_iclr",
        url="https://api.github.com/repos/cxcscmu/AutoGEO",
        kind="github",
        category="geo_resource",
        description="AutoGEO — ICLR 2026 GEO 自动优化框架 (184★)",
    ),

    # ═══════════════════════════════════════════
    # 8. 中文社区
    # ═══════════════════════════════════════════
    RadarSource(
        name="zhihu_seo",
        url="https://www.zhihu.com/api/v4/column/c_1234567890/articles?limit=10",
        kind="api",
        category="cn_community",
        description="知乎 SEO 专栏（占位，需配置专栏ID）",
    ),
]

# ──────────────────────────────────────────────
# 抓取器
# ──────────────────────────────────────────────

@dataclass
class RadarItem:
    title: str
    url: str
    source: str
    category: str
    published_at: str
    summary: str = ""
    relevance_score: float = 0.0  # 0~1，AI 评估与 GEO 的相关性
    technique_extracted: str = ""  # AI 提取的具体技术/战术
    fetch_kind: str = ""


def _parse_atom(xml_text: str, source: RadarSource, limit: int = 5) -> list[RadarItem]:
    """解析 Atom/RSS feed"""
    from xml.etree import ElementTree
    items: list[RadarItem] = []
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError:
        return items

    ns = {"a": "http://www.w3.org/2005/Atom"}
    # Atom 格式
    entries = root.findall("a:entry", ns) or root.findall("entry")
    if entries:
        for entry in entries[:limit]:
            title_el = entry.find("a:title", ns) or entry.find("title")
            link_el = entry.find("a:link", ns) or entry.find("link")
            summary_el = entry.find("a:summary", ns) or entry.find("summary")
            updated_el = entry.find("a:updated", ns) or entry.find("updated")
            title = (title_el.text or "").strip() if title_el is not None else ""
            href = link_el.get("href") if link_el is not None else ""
            if not href and link_el is not None and link_el.text:
                href = link_el.text.strip()
            summary = (summary_el.text or "")[:300] if summary_el is not None else ""
            items.append(RadarItem(
                title=title, url=href, source=source.name, category=source.category,
                published_at=(updated_el.text or "") if updated_el is not None else "",
                summary=summary, fetch_kind="atom",
            ))
        return items

    # RSS 格式
    channel = root.find("channel")
    if channel is not None:
        for entry in channel.findall("item")[:limit]:
            title_el = entry.find("title")
            link_el = entry.find("link")
            desc_el = entry.find("description")
            pub_el = entry.find("pubDate")
            title = (title_el.text or "").strip() if title_el is not None else ""
            href = (link_el.text or "").strip() if link_el is not None else ""
            desc = (desc_el.text or "")[:300] if desc_el is not None else ""
            items.append(RadarItem(
                title=title, url=href, source=source.name, category=source.category,
                published_at=(pub_el.text or "") if pub_el is not None else "",
                summary=desc, fetch_kind="rss",
            ))
    return items


def _parse_github_search(data: dict, source: RadarSource, limit: int = 5) -> list[RadarItem]:
    """解析 GitHub 搜索结果"""
    items: list[RadarItem] = []
    # GitHub API 可能返回单个 repo（/repos/:owner/:repo）或搜索结果
    if "items" in data:
        repos = data["items"][:limit]
    elif "full_name" in data:
        repos = [data]
    else:
        repos = []
    for repo in repos:
        items.append(RadarItem(
            title=f"{repo.get('full_name', '')} — {(repo.get('description') or '')[:80]}",
            url=repo.get("html_url", ""),
            source=source.name,
            category=source.category,
            published_at=repo.get("updated_at", ""),
            summary=(repo.get("description") or "")[:300],
            fetch_kind="github",
        ))
    return items


def _parse_reddit_json(data: dict, source: RadarSource, limit: int = 5) -> list[RadarItem]:
    """解析 Reddit JSON API"""
    items: list[RadarItem] = []
    posts = (data.get("data") or {}).get("children") or []
    for post in posts[:limit]:
        d = post.get("data") or {}
        items.append(RadarItem(
            title=d.get("title", ""),
            url=f"https://reddit.com{d.get('permalink', '')}",
            source=source.name,
            category=source.category,
            published_at=datetime.fromtimestamp(d.get("created_utc", 0), tz=timezone.utc).isoformat() if d.get("created_utc") else "",
            summary=(d.get("selftext") or "")[:300],
            fetch_kind="reddit",
        ))
    return items


def _parse_arxiv(xml_text: str, source: RadarSource, limit: int = 5) -> list[RadarItem]:
    """解析 arXiv API 响应"""
    from xml.etree import ElementTree
    items: list[RadarItem] = []
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError:
        return items

    ns = {"a": "http://www.w3.org/2005/Atom"}
    for entry in root.findall("a:entry", ns)[:limit]:
        title_el = entry.find("a:title", ns)
        link_el = entry.find("a:link", ns)
        summary_el = entry.find("a:summary", ns)
        published_el = entry.find("a:published", ns)
        title = (title_el.text or "").strip().replace("\n", " ") if title_el is not None else ""
        href = link_el.get("href", "") if link_el is not None else ""
        summary = (summary_el.text or "").strip()[:300] if summary_el is not None else ""
        published = (published_el.text or "") if published_el is not None else ""
        items.append(RadarItem(
            title=title, url=href, source=source.name, category=source.category,
            published_at=published, summary=summary, fetch_kind="arxiv",
        ))
    return items


def _fetch_html_headings(url: str, source: RadarSource, limit: int = 5) -> list[RadarItem]:
    """从 HTML 页面提取标题"""
    items: list[RadarItem] = []
    try:
        with httpx.Client(timeout=15, headers={"User-Agent": "UJ-TechRadar/2.0"}) as client:
            resp = client.get(url)
            resp.raise_for_status()
            titles = re.findall(r"<h[23][^>]*>([^<]+)</h[23]>", resp.text[:10000])
            for t in titles[:limit]:
                items.append(RadarItem(
                    title=t.strip(), url=url, source=source.name, category=source.category,
                    published_at="", fetch_kind="html",
                ))
    except Exception as e:
        logger.warning("HTML fetch failed %s: %s", url, e)
    return items


# ──────────────────────────────────────────────
# GEO 相关性过滤关键词
# ──────────────────────────────────────────────

GEO_RELEVANCE_KEYWORDS = [
    # 核心 GEO
    "generative engine optimization", "geo", "llm search", "ai search",
    "ai overview", "search generative experience", "sge",
    # SEO 技术
    "structured data", "schema markup", "rich snippet", "featured snippet",
    "llms.txt", "llms-txt", "ai.txt",
    # LLM 收录
    "llm indexing", "ai citation", "ai brand mention", "chatgpt search",
    "perplexity", "google ai overview", "bing chat",
    # 内容策略
    "e-e-a-t", "topical authority", "content optimization",
    "semantic seo", "entity seo", "knowledge graph",
    # 技术 SEO
    "core web vitals", "page experience", "crawl budget",
    "javascript seo", "rendering", "indexing api",
    # 中文
    "生成式引擎优化", "ai搜索优化", "大模型收录", "百度ai",
    "结构化数据", "语义搜索", "知识图谱",
]


def _compute_relevance(item: RadarItem) -> float:
    """计算 GEO 相关性分数 0~1"""
    text = f"{item.title} {item.summary}".lower()
    hits = sum(1 for kw in GEO_RELEVANCE_KEYWORDS if kw in text)
    # 学术论文天然高相关
    if item.category == "paper":
        return min(1.0, 0.5 + hits * 0.1)
    # 白帽规范天然高相关
    if item.category == "whitehat":
        return min(1.0, 0.4 + hits * 0.15)
    return min(1.0, hits * 0.2)


# ──────────────────────────────────────────────
# 主抓取函数
# ──────────────────────────────────────────────

def fetch_tech_radar(
    categories: list[str] | None = None,
    limit_per_source: int = 5,
    min_relevance: float = 0.0,
) -> dict[str, Any]:
    """抓取所有配置的 GEO/SEO 技术源。

    Args:
        categories: 过滤类别，None=全部
        limit_per_source: 每个源最多抓取条数
        min_relevance: 最低相关性阈值（0=不过滤）
    """
    all_items: list[RadarItem] = []
    errors: list[str] = []
    sources_ok = 0
    sources_total = 0
    sources = RADAR_SOURCES
    if categories:
        sources = [s for s in sources if s.category in categories]

    timeout_sec = 15
    headers = {"User-Agent": "UJ-TechRadar/2.0 (GEO/SEO Research)"}
    with httpx.Client(timeout=timeout_sec, headers=headers, follow_redirects=True) as client:
        for source in sources:
            sources_total += 1
            try:
                if source.kind == "api" and "arxiv" in source.url:
                    resp = client.get(source.url)
                    resp.raise_for_status()
                    items = _parse_arxiv(resp.text, source, limit=limit_per_source)
                elif source.kind == "api" and "reddit" in source.url:
                    reddit_headers = {"User-Agent": "UJ-TechRadar/2.0"}
                    resp = client.get(source.url, headers=reddit_headers)
                    resp.raise_for_status()
                    items = _parse_reddit_json(resp.json(), source, limit=limit_per_source)
                elif source.kind == "rss":
                    resp = client.get(source.url)
                    resp.raise_for_status()
                    items = _parse_atom(resp.text, source, limit=limit_per_source)
                elif source.kind == "github" and "/repos/" in source.url:
                    resp = client.get(source.url)
                    resp.raise_for_status()
                    items = _parse_github_search(resp.json(), source, limit=limit_per_source)
                elif source.kind == "github":
                    resp = client.get(source.url)
                    resp.raise_for_status()
                    items = _parse_github_search(resp.json(), source, limit=limit_per_source)
                elif source.kind == "html":
                    items = _fetch_html_headings(source.url, source, limit=limit_per_source)
                else:
                    continue

                # 计算相关性
                for item in items:
                    item.relevance_score = _compute_relevance(item)

                all_items.extend(items)
                sources_ok += 1
                logger.info("Tech radar: %s fetched %d items", source.name, len(items))

            except Exception as exc:
                errors.append(f"{source.name}: {exc}")
                logger.warning("Tech radar fetch failed %s: %s", source.name, exc)

    # 过滤相关性
    if min_relevance > 0:
        all_items = [i for i in all_items if i.relevance_score >= min_relevance]

    # 按相关性排序
    all_items.sort(key=lambda x: x.relevance_score, reverse=True)
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "items": [
            {
                "title": i.title,
                "url": i.url,
                "source": i.source,
                "category": i.category,
                "published_at": i.published_at,
                "summary": i.summary,
                "relevance_score": round(i.relevance_score, 2),
                "technique_extracted": i.technique_extracted,
            }
            for i in all_items
        ],
        "total": len(all_items),
        "sources_ok": sources_ok,
        "sources_total": sources_total,
        "errors": errors,
        "categories_fetched": list(set(i.category for i in all_items)),
    }


def fetch_latest_geo_techniques() -> dict[str, Any]:
    """快捷函数：只抓取高相关性的 GEO 技术发现"""
    return fetch_tech_radar(min_relevance=0.3, limit_per_source=3)


# ──────────────────────────────────────────────
# Connection ⑤: Tech Radar → Writing Policy 自动更新
# ──────────────────────────────────────────────

_CHANGELOG_PATH: str = ""

import json as _json
import os as _os
from pathlib import Path as _Path


def _get_changelog_path() -> str:
    """获取 tactics_changelog.json 的绝对路径（延迟计算）。"""
    global _CHANGELOG_PATH
    if not _CHANGELOG_PATH:
        _CHANGELOG_PATH = str(
            _Path(__file__).resolve().parent / "tactics_changelog.json"
        )
    return _CHANGELOG_PATH


def _load_changelog() -> list[dict[str, Any]]:
    """加载现有的 tactics changelog。"""
    path = _get_changelog_path()
    if _os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return _json.load(f)
        except (ValueError, _json.JSONDecodeError):
            return []
    return []


def _save_changelog(entries: list[dict[str, Any]]) -> None:
    """保存 tactics changelog。"""
    path = _get_changelog_path()
    with open(path, "w", encoding="utf-8") as f:
        _json.dump(entries, f, ensure_ascii=False, indent=2)


def update_tactics_from_radar(
    findings: list[dict[str, Any]],
    *,
    min_score: float = 0.5,
) -> dict[str, Any]:
    """将高相关性 Tech Radar 发现写入 tactics changelog 并 bump 版本。

    Args:
        findings: Tech Radar 扫描结果列表（每个含 title/url/relevance_score 等）
        min_score: 最低相关性阈值（默认 0.5）

    Returns:
        {
            "changelog_entries_added": int,
            "total_changelog_entries": int,
            "new_tactics_version": str,
            "high_relevance_findings": list,
        }
    """
    # 过滤高相关性发现
    high_relevance = [
        f for f in findings
        if f.get("relevance_score", 0) >= min_score
    ]
    if not high_relevance:
        return {
            "changelog_entries_added": 0,
            "total_changelog_entries": len(_load_changelog()),
            "new_tactics_version": TACTICS_VERSION,
            "high_relevance_findings": [],
        }

    # 加载现有 changelog
    changelog = _load_changelog()
    # 已有的 URL 集合（去重）
    existing_urls = {e.get("url") for e in changelog}
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    today_label = datetime.now(timezone.utc).strftime("%Y-%m-%v")
    new_entries: list[dict[str, Any]] = []
    for finding in high_relevance:
        url = finding.get("url", "")
        if url in existing_urls:
            continue
        entry = {
            "title": finding.get("title", ""),
            "url": url,
            "source": finding.get("source", ""),
            "category": finding.get("category", ""),
            "relevance_score": finding.get("relevance_score", 0),
            "technique_extracted": finding.get("technique_extracted", ""),
            "summary": finding.get("summary", "")[:300],
            "applied_at": now,
            "tactics_version_before": TACTICS_VERSION,
        }
        new_entries.append(entry)
        existing_urls.add(url)

    if not new_entries:
        return {
            "changelog_entries_added": 0,
            "total_changelog_entries": len(changelog),
            "new_tactics_version": TACTICS_VERSION,
            "high_relevance_findings": high_relevance,
        }

    # 追加到 changelog
    changelog.extend(new_entries)
    _save_changelog(changelog)
    logger.info(
        "Tactics changelog updated: +%d entries (total %d), %d high-relevance findings",
        len(new_entries), len(changelog), len(high_relevance),
    )
    return {
        "changelog_entries_added": len(new_entries),
        "total_changelog_entries": len(changelog),
        "new_tactics_version": TACTICS_VERSION,
        "high_relevance_findings": high_relevance,
        "new_entries": new_entries,
    }
