from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.models.seo import Keyword, KeywordRanking, SiteAudit, AiOptimizationLog
from app.models.content import ContentPage
from app.models.product import Product


class SeoAnalyzer:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard(self) -> dict:
        total_keywords = self.db.query(func.count(Keyword.id)).filter(Keyword.is_active == True).scalar() or 0
        ranked_keywords = self.db.query(func.count(Keyword.id)).filter(
            Keyword.is_active == True, Keyword.current_ranking.isnot(None)
        ).scalar() or 0

        avg_rank_result = self.db.query(func.avg(Keyword.current_ranking)).filter(
            Keyword.is_active == True, Keyword.current_ranking.isnot(None)
        ).scalar()
        avg_rank = round(float(avg_rank_result), 1) if avg_rank_result else None

        recent_audits = self.db.query(func.count(SiteAudit.id)).filter(
            SiteAudit.created_at >= datetime.now(timezone.utc) - timedelta(days=30)
        ).scalar() or 0

        last_audit = self.db.query(SiteAudit).order_by(SiteAudit.created_at.desc()).first()
        last_audit_score = last_audit.score if last_audit else None

        ai_optimized_pages = self.db.query(
            func.count(func.distinct(AiOptimizationLog.resource_id))
        ).filter(
            AiOptimizationLog.created_at >= datetime.now(timezone.utc) - timedelta(days=30)
        ).scalar() or 0

        llms_config_exists = self.db.query(func.count(ContentPage.id)).filter(
            ContentPage.slug == "llms-txt", ContentPage.is_active == True
        ).scalar() > 0

        keyword_trend_raw = self.db.query(
            func.date(KeywordRanking.last_checked_at),
            func.avg(KeywordRanking.current_position)
        ).filter(
            KeywordRanking.last_checked_at.isnot(None)  # 过滤NULL值
        ).group_by(
            func.date(KeywordRanking.last_checked_at)
        ).order_by(
            func.date(KeywordRanking.last_checked_at)
        ).limit(30).all()

        keyword_trend = []
        for row in keyword_trend_raw:
            date_val = row[0]
            avg_r = round(float(row[1]), 1) if row[1] else None
            keyword_trend.append({"date": str(date_val), "avg_rank": avg_r})

        if not keyword_trend:
            keyword_trend = [
                {"date": (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d"), "avg_rank": None}
                for i in range(7, -1, -1)
            ]

        page_coverage = [
            {"type": "已优化", "count": ai_optimized_pages},
            {"type": "待优化", "count": max(0, total_keywords - ai_optimized_pages)},
        ]

        return {
            "total_keywords": total_keywords,
            "ranked_keywords": ranked_keywords,
            "avg_rank": avg_rank,
            "ai_optimized_pages": ai_optimized_pages,
            "llms_txt_generated": llms_config_exists,
            "last_audit_score": last_audit_score,
            "keyword_trend": keyword_trend,
            "page_coverage": page_coverage,
        }

    def analyze_keyword_rankings(self, keyword_id: str) -> dict:
        keyword = self.db.query(Keyword).filter(Keyword.id == keyword_id).first()
        if not keyword:
            return {"error": "关键词不存在"}

        rankings = self.db.query(KeywordRanking).filter(
            KeywordRanking.keyword_id == keyword_id
        ).order_by(KeywordRanking.checked_at.desc()).limit(30).all()

        trend = []
        for r in reversed(rankings):
            trend.append({"date": r.checked_at.strftime("%Y-%m-%d"), "rank": r.ranking, "engine": r.search_engine})

        rank_change = None
        if len(rankings) >= 2:
            rank_change = (rankings[0].ranking or 0) - (rankings[-1].ranking or 0)

        suggestions = []
        if keyword.current_ranking and keyword.current_ranking > 10:
            suggestions.append("排名较低，建议增加该关键词的内容密度")
        if keyword.current_ranking and keyword.current_ranking > 3 and keyword.current_ranking <= 10:
            suggestions.append("排名中等，建议优化页面Meta标签和内链结构")

        return {
            "keyword": keyword.keyword,
            "slug": keyword.slug,
            "search_volume": keyword.search_volume,
            "difficulty": keyword.difficulty,
            "current_rank": keyword.current_ranking,
            "target_rank": keyword.target_url,
            "rank_change": rank_change,
            "trend": trend,
            "suggestions": suggestions,
        }

    def get_keyword_groups(self) -> list[dict]:
        keywords = self.db.query(Keyword).filter(Keyword.is_active == True).all()
        groups = {}
        for kw in keywords:
            prefix = kw.keyword[:2] if len(kw.keyword) >= 2 else kw.keyword
            if prefix not in groups:
                groups[prefix] = {"group": prefix, "count": 0, "ranked": 0}
            groups[prefix]["count"] += 1
            if kw.current_ranking:
                groups[prefix]["ranked"] += 1
        return list(groups.values())

    def get_seo_pages_summary(self) -> list[dict]:
        from app.models.content import SeoMetadata
        pages = self.db.query(ContentPage).filter(ContentPage.is_active == True).all()
        results = []
        for p in pages:
            seo = self.db.query(SeoMetadata).filter(
                SeoMetadata.resource_type == 'content_page',
                SeoMetadata.resource_id == str(p.id)
            ).first()
            meta_title = seo.meta_title if seo else None
            meta_description = seo.meta_description if seo else None
            has_meta = bool(meta_title or meta_description)
            results.append({
                "id": str(p.id),
                "title": p.title,
                "slug": p.slug,
                "meta_title": meta_title,
                "meta_description": meta_description,
                "ai_optimized": has_meta,
                "status": "optimized" if has_meta else "pending",
                "view_count": p.view_count,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            })
        return results
