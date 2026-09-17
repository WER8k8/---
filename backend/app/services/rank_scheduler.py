# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""排名定时任务调度服务"""

import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.services.rank_checker import RankChecker

logger = logging.getLogger("uj-admin.rank_scheduler")


class RankScheduler:
    """管理关键词排名检查的定时调度"""
    _instance = None
    _running = False
    def __new__(cls):
        """__new__。

        参数说明：
        :param cls: 参数 cls
        :return: 返回处理结果。
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        """_init。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._tracked_keywords: List[Dict[str, Any]] = []
        self.last_run: Optional[str] = None
        self.run_count = 0
        self.errors: List[str] = []

    # ─── 启动 / 停止 ──────────────────────────────
    def start(self, check_hour: int = 6, check_minute: int = 0):
        """启动每日定时排名检查"""
        if self._running:
            return {"status": "already_running"}

        self._running = True
        threading.Thread(
            target=self._daily_loop,
            args=(check_hour, check_minute),
            daemon=True,
        ).start()
        logger.info(f"RankScheduler started (daily at {check_hour:02d}:{check_minute:02d})")
        return {
            "status": "started",
            "check_time": f"{check_hour:02d}:{check_minute:02d}",
        }

    def stop(self):
        """停止定时任务"""
        self._running = False
        logger.info("RankScheduler stopped")
        return {"status": "stopped"}

    def _daily_loop(self, check_hour: int, check_minute: int):
        """_daily_loop。

        参数说明：
        :param self: 参数 self
        :param check_hour: 参数 check_hour
        :param check_minute: 参数 check_minute
        :return: 返回处理结果。
        """
        while self._running:
            now = datetime.now()
            next_run = now.replace(hour=check_hour, minute=check_minute, second=0, microsecond=0)
            if now >= next_run:
                next_run += timedelta(days=1)
            wait = (next_run - now).total_seconds()
            time.sleep(wait)
            if self._running:
                try:
                    self.schedule_daily_check()
                except Exception as e:
                    logger.error(f"RankScheduler daily check failed: {e}")
                    self.errors.append(str(e))

    # ─── 核心功能 ──────────────────────────────
    def schedule_daily_check(self) -> List[Dict[str, Any]]:
        """每天检查所有追踪关键词的排名"""
        if not self._tracked_keywords:
            logger.info("RankScheduler: no keywords to track")
            return []

        keywords: List[str] = []
        domain_map: Dict[str, str] = {}
        for item in self._tracked_keywords:
            kw = item["keyword"]
            domain = item.get("domain", "youding.com")
            keywords.append(kw)
            if kw not in domain_map:
                domain_map[kw] = domain

        logger.info(f"RankScheduler: checking {len(keywords)} keywords")
        results = []
        for kw in keywords:
            domain = domain_map.get(kw, "youding.com")
            result = self.check_now(kw, domain)
            results.append(result)
            time.sleep(1.5)  # 避免请求过快

        self.last_run = datetime.now(timezone.utc).isoformat()
        self.run_count += 1
        logger.info(f"RankScheduler: daily check completed, {len(results)} results")
        return results

    def check_now(self, keyword: str, domain: str, engines: Optional[List[str]] = None) -> Dict[str, Any]:
        """立即检查指定关键词在多个搜索引擎的排名"""
        if engines is None:
            engines = ["baidu", "google", "bing"]

        results = []
        for engine in engines:
            try:
                check = RankChecker.check(keyword, domain, engine)
                results.append(check.to_dict())
            except Exception as e:
                logger.error(f"RankScheduler check failed: {keyword}@{engine}: {e}")
                results.append({
                    "keyword": keyword,
                    "engine": engine,
                    "domain": domain,
                    "best_rank": None,
                    "is_simulated": True,
                    "error": str(e),
                })

        return {
            "keyword": keyword,
            "domain": domain,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "engines": results,
            "best_rank": min(
                (r.get("best_rank") for r in results if r.get("best_rank") is not None),
                default=None,
            ),
        }

    # ─── 关键词管理 ──────────────────────────────
    def add_keywords(self, keywords: List[Dict[str, Any]]):
        """添加追踪关键词"""
        for item in keywords:
            kw = item["keyword"]
            domain = item.get("domain", "youding.com")
            existing = next(
                (x for x in self._tracked_keywords if x["keyword"] == kw and x["domain"] == domain),
                None,
            )
            if not existing:
                self._tracked_keywords.append({"keyword": kw, "domain": domain})
        return {"tracked": len(self._tracked_keywords)}

    def remove_keyword(self, keyword: str, domain: Optional[str] = None):
        """移除追踪关键词"""
        before = len(self._tracked_keywords)
        self._tracked_keywords = [
            x for x in self._tracked_keywords
            if not (x["keyword"] == keyword and (domain is None or x.get("domain") == domain))
        ]
        return {"removed": before - len(self._tracked_keywords), "tracked": len(self._tracked_keywords)}

    def get_tracked_keywords(self) -> List[Dict[str, Any]]:
        """获取当前追踪关键词列表"""
        return list(self._tracked_keywords)

    # ─── 状态 ──────────────────────────────────
    def get_status(self) -> Dict[str, Any]:
        """get_status。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "running": self._running,
            "tracked_count": len(self._tracked_keywords),
            "last_run": self.last_run,
            "run_count": self.run_count,
            "errors_recent": self.errors[-5:],
        }


rank_scheduler = RankScheduler()
