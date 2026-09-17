# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
GEO Agents — 竞品追踪 + 技术雷达 + 定时调度
移植自 sourcechain-geo-engine/backend/app/agents/
  - competitor_monitor.py  → CompetitorMonitorAgent
  - tech_radar.py          → TechRadarAgent
  - scheduler.py            → GEOScheduler（适配 UJ Celery）

适配 UJ 项目：
  - 使用 UJ 的 Celery 任务系统（tasks/celery_app.py）
  - 与现有 seo_tasks.py 并行运行
  - 数据持久化到 UJ 数据库（新增 geo_agent_task 表）
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.core.config import settings
from app.core.cache import redis_client


logger = logging.getLogger(__name__)


def _safe_asyncio_run(coro):
    """安全执行异步协程：兼容已有事件循环（FastAPI）和无事件循环（Celery）。"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)


# ─────────────────────────────────────────────
# Data Models
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class CompetitorTarget:
    name: str
    priority: str   # "p0" | "p1" | "p2"
    notes: str


@dataclass(frozen=True)
class TechSource:
    name: str
    url: str
    category: str      # "frontend" | "backend" | "performance" | "structured_data" | "paper"
    license_policy: str # "public_reference" | "oss_check_required" | "citation_required"


@dataclass
class MonitorResult:
    keyword: str
    platform: str       # "baidu" | "wenxiaoyan" | "doubao" | "deepseek" | "chatgpt"
    rank_position: Optional[int] = None
    ai_citation_present: bool = False
    mobile_lcp_ms: Optional[int] = None
    content_coverage: float = 0.0    # 0~1
    jsonld_present: bool = False
    cta_visibility: bool = False
    checked_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ScanResult:
    title: str
    url: str
    category: str
    impact: str          # "high" | "medium" | "low"
    status: str = "draft_only"
    next_step: str = "license_check_then_isolated_test"
    scanned_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ─────────────────────────────────────────────
# Competitor Monitor Agent
# ─────────────────────────────────────────────

class CompetitorMonitorAgent:
    """
    竞品 GEO 监控 Agent
    追踪关键词在各大 AI 平台和搜索引擎中的表现
    """
    default_targets = (
        CompetitorTarget("全国前十搜索结果", "p0", "每天采样目标关键词前十名"),
        CompetitorTarget("智推时代", "p0", "专项监测内容覆盖、移动端速度和AI引用"),
        CompetitorTarget("优丁建材（自身）", "p0", "自身品牌在 AI 中的引用率基线"),
    )
    default_platforms = (
        "baidu",
        "wenxiaoyan",    # 文心一言搜索
        "doubao",        # 豆包
        "deepseek",       # DeepSeek
        "chatgpt",       # ChatGPT
    )
    default_metrics = (
        "rank_position",
        "ai_citation_presence",
        "mobile_lcp",
        "content_coverage",
        "jsonld_presence",
        "cta_visibility",
    )
    def build_monitor_plan(self, keyword: str) -> dict[str, object]:
        """生成监控计划（可序列化为 JSON 存储）"""
        return {
            "keyword": keyword,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "platforms": list(self.default_platforms),
            "targets": [t.__dict__ for t in self.default_targets],
            "metrics": list(self.default_metrics),
            "schedule": "daily_09_00",
        }

    def build_gap_action(self, missing_topic: str) -> dict[str, str]:
        """生成内容缺口补救动作"""
        return {
            "topic": missing_topic,
            "action": "create_or_rewrite_mobile_chunk",
            "guard": "shadow_qc_then_rank_guard",
            "priority": "p1",
        }

    async def run_check(
        self,
        keyword: str,
        platforms: Optional[list[str]] = None,
    ) -> list[MonitorResult]:
        """
        执行一次竞品监控检查

        注意：此为框架代码，实际调用需要：
        1. 对接 UJ 现有 geo_engine_service.GEOEngine.check_keyword()
        2. 对接 rank_checker.py 获取搜索引擎排名

        Args:
            keyword: 监控关键词
            platforms: 指定平台（默认全部）

        Returns:
            list[MonitorResult]: 各平台监控结果
        """
        platforms = platforms or list(self.default_platforms)
        results: list[MonitorResult] = []
        # 通过 GEOEngine 检查 AI 平台引用状态
        from app.services.geo_engine_service import GEOEngine
        for platform in platforms:
            try:
                engine_result = await GEOEngine.check_keyword(
                    keyword,
                    models=[platform] if platform in {m["id"] for m in GEOEngine.MODELS} else None,
                    probe_mode="recommend",
                    brand_name=keyword,
                    product_category=keyword,
                )
                if engine_result and engine_result.get("models"):
                    for m in engine_result["models"]:
                        in_top = m.get("status") == "indexed" and (
                            m.get("rank_position") in (1, 2, 3) or m.get("mentions_brand")
                        )
                        results.append(
                            MonitorResult(
                                platform=platform,
                                keyword=keyword,
                                rank_position=m.get("rank_position"),
                                ai_citation_present=bool(in_top),
                                checked_at=datetime.now(timezone.utc).isoformat(),
                            )
                        )
            except Exception as e:
                logger.warning("[CompetitorMonitor] GEOEngine 检查失败 (%s): %s", platform, e)
                results.append(
                    MonitorResult(
                        platform=platform,
                        keyword=keyword,
                        ai_citation_present=False,
                        checked_at=datetime.now(timezone.utc).isoformat(),
                    )
                )

        logger.info(f"[CompetitorMonitor] 检查关键词: {keyword}, 平台: {platforms}")
        # 占位：记录检查计划到 Redis（避免重复执行）
        cache_key = f"geo:monitor:{keyword}:{datetime.now(timezone.utc).strftime('%Y%m%d')}"
        redis_client.set(cache_key, json.dumps({
            "keyword": keyword,
            "platforms": platforms,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }), ex=86400)
        return results

    def get_latest_results(self, keyword: str, days: int = 7) -> list[dict]:
        """从 Redis/DB 获取最近 N 天的监控结果"""
        if not redis_client:
            return []
        pattern = f"geo:monitor:{keyword}:*"
        keys = list(redis_client.scan_iter(match=pattern, count=100))
        results = []
        cutoff = datetime.now(timezone.utc) - __import__('datetime').timedelta(days=days)
        for k in keys[:days * 10]:
            try:
                raw = redis_client.get(k)
                if raw:
                    data = json.loads(raw)
                    started = data.get("started_at", "")
                    if started:
                        from datetime import datetime as _dt
                        started_dt = _dt.fromisoformat(started)
                        if started_dt >= cutoff:
                            results.append(data)
            except Exception:
                pass
        return sorted(results, key=lambda x: x.get("started_at", ""), reverse=True)[:50]


# ─────────────────────────────────────────────
# Tech Radar Agent
# ─────────────────────────────────────────────

class TechRadarAgent:
    """
    技术雷达 Agent
    每日扫描前端/后端/性能/结构化数据相关技术动态
    """
    sources = (
        TechSource("Nuxt Blog", "https://nuxt.com/blog", "frontend", "public_reference"),
        TechSource("Vue Blog", "https://blog.vuejs.org/", "frontend", "public_reference"),
        TechSource("FastAPI Releases", "https://github.com/fastapi/fastapi/releases", "backend", "oss_check_required"),
        TechSource("web.dev", "https://web.dev/articles", "performance", "public_reference"),
        TechSource("Schema.org", "https://schema.org/docs/releases.html", "structured_data", "public_reference"),
        TechSource("arXiv CS IR", "https://arxiv.org/list/cs.IR/recent", "paper", "citation_required"),
        # UJ 扩展源
        TechSource("Vite Blog", "https://vitejs.dev/blog/", "frontend", "public_reference"),
        TechSource("Tailwind Blog", "https://tailwindcss.com/blog", "frontend", "public_reference"),
    )
    def build_daily_scan_plan(self) -> dict[str, object]:
        """生成每日技术扫描计划"""
        return {
            "run_at": "08:00 Asia/Shanghai",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "rules": [
                "only_public_sources",
                "license_check_required",
                "no_direct_production_hot_update",
                "test_canary_rollback_required",
            ],
            "sources": [s.__dict__ for s in self.sources],
            "output_dir": "docs/geo/tech-radar/",
        }

    def summarize_candidate(self, title: str, url: str, impact: str) -> ScanResult:
        """汇总扫描候选技术，生成初步评估"""
        return ScanResult(
            title=title,
            url=url,
            category=self._detect_category(url),
            impact=impact,
        )

    def _detect_category(self, url: str) -> str:
        """根据 URL 自动检测技术分类"""
        url_lower = url.lower()
        if "nuxt" in url_lower or "vue" in url_lower or "vite" in url_lower:
            return "frontend"
        if "fastapi" in url_lower or "django" in url_lower or "sqlalchemy" in url_lower:
            return "backend"
        if "web.dev" in url_lower or "performance" in url_lower or "lcp" in url_lower:
            return "performance"
        if "schema" in url_lower or "jsonld" in url_lower or "structured" in url_lower:
            return "structured_data"
        if "arxiv" in url_lower or "paper" in url_lower:
            return "paper"
        return "unknown"

    async def run_daily_scan(self) -> dict[str, object]:
        """
        执行每日技术扫描：公开源抓取 → Hermes 只读验证 → 高影响项飞书通知。
        """
        from app.core.database import SessionLocal
        from app.services.hermes.ops_autopilot import run_tech_radar_cycle
        plan = self.build_daily_scan_plan()
        logger.info("[TechRadar] 开始每日技术扫描，计划: %s 个源", len(self.sources))
        db = SessionLocal()
        try:
            report = run_tech_radar_cycle(db, trigger="celery_daily")
        finally:
            db.close()

        return {
            "status": "completed",
            "mode": report.get("mode", "fetch_and_validate"),
            "plan": plan,
            "sources_count": len(self.sources),
            "candidates_count": len(report.get("candidates") or []),
            "high_impact_count": report.get("high_impact_count", 0),
            "validation_fail_count": report.get("validation_fail_count", 0),
            "alert": report.get("alert"),
            "fetch_errors": report.get("fetch_errors") or [],
        }


# ─────────────────────────────────────────────
# GEO Scheduler（适配 UJ Celery）
# ─────────────────────────────────────────────

# Celery 任务名称（与 tasks/celery_app.py 注册）
CELERY_TASK_TECH_RADAR = "geo_tech_radar_daily"
CELERY_TASK_RANK_GUARD = "geo_rank_guard_check"
CELERY_TASK_COMPETITOR = "geo_competitor_monitor"
CELERY_TASK_HERMES_RANK = "hermes_daily_rank_cycle"


def build_daily_jobs() -> list[dict[str, str]]:
    """
    构建每日定时任务列表
    与 UJ 现有 tasks/seo_tasks.py 的 Celery Beat 调度并行运行

    Returns:
        任务配置列表，可注入 Celery Beat 配置
    """
    return [
        {
            "name": CELERY_TASK_HERMES_RANK,
            "cron": "0 7 * * *",          # 每天 07:00 — 排名第一准则，先于技术雷达
            "description": "Hermes 多引擎排名攻坚（豆包/通义/DeepSeek + ECC 评审）",
            "guard": "read_probe_only,regression_alert",
        },
        {
            "name": CELERY_TASK_TECH_RADAR,
            "cron": "0 8 * * *",          # 每天 08:00
            "description": "技术雷达每日扫描",
            "guard": "license_check,test,canary,rollback",
        },
        {
            "name": CELERY_TASK_RANK_GUARD,
            "cron": "0 */6 * * *",        # 每 6 小时
            "description": "Rank Guard 质量门禁检查",
            "guard": "rollback_on_regression",
        },
        {
            "name": CELERY_TASK_COMPETITOR,
            "cron": "0 9 * * *",          # 每天 09:00
            "description": "竞品 GEO 监控",
            "guard": "top10_and_zhitui_tracking",
        },
    ]


async def run_scheduler_once() -> dict[str, object]:
    """
    手动触发一次调度器（用于 API 调用 / 调试）
    不直接操作 Celery，而是返回调度计划
    """
    return {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "jobs": build_daily_jobs(),
        "tech_radar": TechRadarAgent().run_daily_scan(),
        "competitor_monitor": CompetitorMonitorAgent().build_monitor_plan(
            "轻集料混凝土"
        ),
        "note": "此接口仅返回调度计划，实际执行需配置 Celery Beat 或手动触发任务",
    }


def register_celery_tasks():
    """
    注册 Celery 任务到 app
    在 tasks/celery_app.py 中调用此函数完成注册

    用法：
        # 在 celery_app.py 中：
        from app.services.geo_agents import register_celery_tasks
        register_celery_tasks()
    """
    try:
        from celery import Celery
        from tasks.celery_app import celery_app
        @celery_app.task(name=CELERY_TASK_TECH_RADAR)
        def tech_radar_daily():
            """tech_radar_daily。
            :return: 返回处理结果。
            """
            return _safe_asyncio_run(TechRadarAgent().run_daily_scan())

        @celery_app.task(name=CELERY_TASK_RANK_GUARD)
        def rank_guard_check():
            """rank_guard_check。
            :return: 返回处理结果。
            """
            from app.services.geo_engine_service import GEOEngine
            async def _run():
                """_run。
                :return: 返回处理结果。
                """
                result = await GEOEngine.check_keyword("轻集料混凝土")
                return result or {"status": "completed", "indexed_rate": 0}
            return _safe_asyncio_run(_run())

        @celery_app.task(name=CELERY_TASK_COMPETITOR)
        def competitor_monitor():
            """competitor_monitor。
            :return: 返回处理结果。
            """
            agent = CompetitorMonitorAgent()
            return _safe_asyncio_run(agent.run_check("轻集料混凝土"))

        logger.info("[GEOScheduler] Celery 任务注册完成")
        return True
    except ImportError as e:
        logger.warning(f"[GEOScheduler] Celery 未安装，跳过任务注册: {e}")
        return False
