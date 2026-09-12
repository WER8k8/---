import logging

from celery import shared_task
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.seo import (AiOptimizationLog, Keyword, KeywordRanking,
                            SiteAudit)
from app.services.seo_analyzer import SeoAnalyzer
from app.services.site_audit import SiteAuditEngine

logger = logging.getLogger(__name__)

# BUG-19: 分布式锁 TTL（秒）
_LOCK_TTL = 900


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def check_single_keyword_ranking(self, keyword_id: str):
    """check_single_keyword_ranking。

    参数说明：
    :param self: 参数 self
    :param keyword_id: 参数 keyword_id
    :return: 返回处理结果。
    """
    db: Session = SessionLocal()
    try:
        keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
        if not keyword:
            logger.warning(f"关键词 {keyword_id} 不存在")
            return {"error": "关键词不存在"}

        analyzer = SeoAnalyzer(db)
        result = analyzer.analyze_keyword_rankings(keyword_id)
        ranking = KeywordRanking(
            keyword_id=keyword_id,
            current_rank=result.get("current_rank", 0),
            previous_rank=result.get("previous_rank", 0),
            search_volume=keyword.search_volume,
            trend_data=result.get("trend", []),
        )
        db.add(ranking)
        keyword.last_checked = (
            db.query(KeywordRanking.created_at)
            .filter(KeywordRanking.keyword_id == keyword_id)
            .order_by(KeywordRanking.created_at.desc())
            .first()[0]
            if db.query(KeywordRanking).filter(KeywordRanking.keyword_id == keyword_id).first()
            else None
        )
        db.commit()
        return {"keyword_id": keyword_id, "rank": result.get("current_rank")}
    except Exception as e:
        logger.error(f"检查关键词 {keyword_id} 排名失败: {e}")
        raise self.retry(exc=e)
    finally:
        db.close()


@shared_task(bind=True, max_retries=3, default_retry_delay=600)
def check_all_keyword_rankings(self):
    """check_all_keyword_rankings。

    参数说明：
    :param self: 参数 self
    :return: 返回处理结果。
    """
    from app.services.scheduler_leader import release_scheduler_lock, try_acquire_scheduler_lock
    if not try_acquire_scheduler_lock("seo_check_all_keyword_rankings", ttl_seconds=_LOCK_TTL):
        logger.info("check_all_keyword_rankings lock held by another instance, skipping")
        return {"skipped": True, "reason": "leader_lock_busy"}
    db: Session = SessionLocal()
    try:
        keywords = db.query(Keyword).filter(Keyword.is_active).all()
        results = []
        for kw in keywords:
            try:
                result = check_single_keyword_ranking.delay(kw.id)
                results.append({"keyword_id": kw.id, "task_id": result.id})
            except Exception as e:
                logger.error(f"提交关键词 {kw.id} 检查任务失败: {e}")
        return {"total": len(keywords), "submitted": len(results)}
    finally:
        db.close()
        release_scheduler_lock("seo_check_all_keyword_rankings")


@shared_task(bind=True, max_retries=2, default_retry_delay=600)
def recheck_inclusion_daily(self, limit: int = 200):
    """SEO-08：每日批量复检收录（Celery Beat）。"""
    from app.services.scheduler_leader import release_scheduler_lock, try_acquire_scheduler_lock
    if not try_acquire_scheduler_lock("seo_recheck_inclusion_daily", ttl_seconds=_LOCK_TTL):
        logger.info("recheck_inclusion_daily lock held by another instance, skipping")
        return {"skipped": True, "reason": "leader_lock_busy"}
    db: Session = SessionLocal()
    try:
        from app.services.seo.inclusion_check_service import recheck_inclusion_batch
        return recheck_inclusion_batch(db, limit=limit)
    except Exception as exc:
        logger.error("收录复检失败: %s", exc)
        raise self.retry(exc=exc) from exc
    finally:
        db.close()
        release_scheduler_lock("seo_recheck_inclusion_daily")


@shared_task(bind=True, max_retries=2, default_retry_delay=3600)
def run_site_audit(self, url: str = None):
    """run_site_audit。

    参数说明：
    :param self: 参数 self
    :param url: 参数 url
    :return: 返回处理结果。
    """
    from app.core.config import settings
    from app.services.scheduler_leader import release_scheduler_lock, try_acquire_scheduler_lock
    if not try_acquire_scheduler_lock("seo_run_site_audit", ttl_seconds=_LOCK_TTL):
        logger.info("run_site_audit lock held by another instance, skipping")
        return {"skipped": True, "reason": "leader_lock_busy"}
    target_url = url or settings.SITE_URL
    db: Session = SessionLocal()
    try:
        engine = SiteAuditEngine()
        import asyncio
        result = asyncio.run(engine.run_audit(target_url, "basic"))
        audit = SiteAudit(
            url=target_url,
            score=result.get("score", 0),
            dimension_scores=result.get("dimension_scores", {}),
            issues=result.get("issues", []),
            suggestions=result.get("suggestions", []),
        )
        db.add(audit)
        db.commit()
        return {"url": target_url, "score": audit.score}
    except Exception as e:
        logger.error(f"站点审计失败: {e}")
        raise self.retry(exc=e)
    finally:
        db.close()
        release_scheduler_lock("seo_run_site_audit")


@shared_task(bind=True, name="seo_research_hints_sync", max_retries=1, default_retry_delay=300)
def seo_research_hints_sync(self, max_tenants: int = 100):
    """SEO-10：矩阵词反哺 research_hints。"""
    from app.services.scheduler_leader import release_scheduler_lock, try_acquire_scheduler_lock
    if not try_acquire_scheduler_lock("seo_research_hints_sync", ttl_seconds=_LOCK_TTL):
        logger.info("seo_research_hints_sync lock held by another instance, skipping")
        return {"skipped": True, "reason": "leader_lock_busy"}
    db: Session = SessionLocal()
    try:
        from app.services.seo.seo_research_hints_service import sync_all_active_tenants
        return sync_all_active_tenants(db, max_tenants=max_tenants)
    except Exception as exc:
        logger.error("seo_research_hints_sync failed: %s", exc)
        raise self.retry(exc=exc) from exc
    finally:
        db.close()
        release_scheduler_lock("seo_research_hints_sync")
