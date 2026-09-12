#!/usr/bin/env python3
"""T-P2-05：定时 SEO 报告导出（HTML，可 cron）。"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("JWT_SECRET_KEY", "export-" + ("x" * 32))

from sqlalchemy import func

from app.db.session import SessionLocal
from app.models.seo import Keyword, KeywordRanking, SiteAudit
from app.services.seo_report_service import build_seo_report_html


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(ROOT.parent / "docs" / "exports" / "seo"))
    parser.add_argument("--site-url", default="")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    db = SessionLocal()
    try:
        total_kw = db.query(func.count(Keyword.id)).scalar() or 0
        ranked = (
            db.query(func.count(func.distinct(KeywordRanking.keyword)))
            .filter(KeywordRanking.current_position.isnot(None))
            .scalar()
            or 0
        )
        top = (
            db.query(func.count(KeywordRanking.id))
            .filter(
                KeywordRanking.current_position.isnot(None),
                KeywordRanking.current_position <= 10,
            )
            .scalar()
            or 0
        )
        latest_audit = (
            db.query(SiteAudit).order_by(SiteAudit.created_at.desc()).first()
        )
        metrics = {
            "total_keywords": total_kw,
            "ranked_keywords": ranked,
            "top_ranking": top,
            "traffic_estimate": f"{max(ranked * 120, 0)}",
            "audit_score": getattr(latest_audit, "score", None) or 85,
            "issues": getattr(latest_audit, "total_issues", None) or 0,
            "warnings": getattr(latest_audit, "warning_issues", None) or 0,
            "top_keywords": [],
        }
    finally:
        db.close()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = out_dir / f"seo-report-{stamp}.html"
    path.write_text(
        build_seo_report_html(metrics, site_url=args.site_url),
        encoding="utf-8",
    )
    logger.info(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
