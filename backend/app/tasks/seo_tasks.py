import logging
from celery import shared_task
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.seo import Keyword, KeywordRanking, SiteAudit, AiOptimizationLog
from app.services.seo_analyzer import SeoAnalyzer
from app.services.site_audit import SiteAuditEngine

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def check_single_keyword_ranking(self, keyword_id: str):
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
        keyword.last_checked = db.query(KeywordRanking.created_at).filter(
            KeywordRanking.keyword_id == keyword_id
        ).order_by(KeywordRanking.created_at.desc()).first()[0] if db.query(KeywordRanking).filter(
            KeywordRanking.keyword_id == keyword_id
        ).first() else None
        db.commit()
        return {"keyword_id": keyword_id, "rank": result.get("current_rank")}
    except Exception as e:
        logger.error(f"检查关键词 {keyword_id} 排名失败: {e}")
        raise self.retry(exc=e)
    finally:
        db.close()


@shared_task(bind=True, max_retries=3, default_retry_delay=600)
def check_all_keyword_rankings(self):
    db: Session = SessionLocal()
    try:
        keywords = db.query(Keyword).filter(Keyword.is_active == True).all()
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


@shared_task(bind=True, max_retries=2, default_retry_delay=3600)
def run_site_audit(self, url: str = None):
    from app.core.config import settings
    target_url = url or settings.SITE_BASE_URL
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
