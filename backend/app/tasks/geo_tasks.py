# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""GEO Celery 任务 — 技术雷达 / Rank Guard / 竞品监控。"""

import asyncio
import concurrent.futures
import logging

from celery import shared_task

logger = logging.getLogger(__name__)

# BUG-19: 分布式锁 TTL（秒）
_LOCK_TTL = 900


def _safe_asyncio_run(coro):
    """安全执行异步协程：兼容已有事件循环（FastAPI）和无事件循环（Celery）。"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)


@shared_task(bind=True, name="hermes_daily_rank_cycle", max_retries=2, default_retry_delay=300)
def hermes_daily_rank_cycle(self):
    """Hermes 排名第一准则 — 07:00 多引擎 probe + 战术雷达 + ECC 评审。"""
    from app.core.database import SessionLocal
    from app.services.hermes.daily_rank_ops import run_hermes_daily_rank_cycle
    db = SessionLocal()
    try:
        return run_hermes_daily_rank_cycle(db, trigger="celery_daily_rank")
    except Exception as exc:
        logger.exception("hermes_daily_rank_cycle failed")
        raise self.retry(exc=exc) from exc
    finally:
        db.close()


@shared_task(bind=True, name="geo_tech_radar_daily", max_retries=2, default_retry_delay=300)
def geo_tech_radar_daily(self):
    """geo_tech_radar_daily。

    参数说明：
    :param self: 参数 self
    :return: 返回处理结果。
    """
    from app.services.scheduler_leader import release_scheduler_lock, try_acquire_scheduler_lock
    if not try_acquire_scheduler_lock("geo_tech_radar_daily", ttl_seconds=_LOCK_TTL):
        logger.info("geo_tech_radar_daily lock held by another instance, skipping")
        return {"skipped": True, "reason": "leader_lock_busy"}
    try:
        result = _safe_asyncio_run(TechRadarAgent().run_daily_scan())
    except Exception as exc:
        logger.exception("geo_tech_radar_daily failed")
        raise self.retry(exc=exc) from exc
    finally:
        release_scheduler_lock("geo_tech_radar_daily")
    return result


@shared_task(bind=True, name="geo_rank_guard_check", max_retries=2, default_retry_delay=300)
def geo_rank_guard_check(self):
    """geo_rank_guard_check。

    参数说明：
    :param self: 参数 self
    :return: 返回处理结果。
    """
    from app.core.database import SessionLocal
    from app.services.geo_rank_guard_probe import run_rank_guard_probe
    from app.services.scheduler_leader import release_scheduler_lock, try_acquire_scheduler_lock
    if not try_acquire_scheduler_lock("geo_rank_guard_check", ttl_seconds=_LOCK_TTL):
        logger.info("geo_rank_guard_check lock held by another instance, skipping")
        return {"skipped": True, "reason": "leader_lock_busy"}
    db = SessionLocal()
    try:
        return run_rank_guard_probe(db, trigger="celery")
    except Exception as exc:
        logger.exception("geo_rank_guard_check failed")
        raise self.retry(exc=exc) from exc
    finally:
        db.close()
        release_scheduler_lock("geo_rank_guard_check")


@shared_task(bind=True, name="geo_competitor_monitor", max_retries=2, default_retry_delay=300)
def geo_competitor_monitor(self):
    """geo_competitor_monitor。

    参数说明：
    :param self: 参数 self
    :return: 返回处理结果。
    """
    from app.services.geo_agents import CompetitorMonitorAgent
    from app.services.scheduler_leader import release_scheduler_lock, try_acquire_scheduler_lock
    if not try_acquire_scheduler_lock("geo_competitor_monitor", ttl_seconds=_LOCK_TTL):
        logger.info("geo_competitor_monitor lock held by another instance, skipping")
        return {"skipped": True, "reason": "leader_lock_busy"}
    try:
        result = _safe_asyncio_run(CompetitorMonitorAgent().run_check("轻集料混凝土"))
    except Exception as exc:
        logger.exception("geo_competitor_monitor failed")
        raise self.retry(exc=exc) from exc
    finally:
        release_scheduler_lock("geo_competitor_monitor")
    return result
