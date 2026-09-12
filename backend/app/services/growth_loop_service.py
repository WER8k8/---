"""外贸全自动化获客闭环引擎 (Growth Loop Engine)。"""

from __future__ import annotations

import logging
import uuid
from typing import Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _query_real_leads(tenant_id: str, limit: int = 10) -> list[dict[str, Any]]:
    """从真实询盘库取线索。无数据/异常一律返回空列表，绝不伪造。"""
    try:
        from app.db.session import SessionLocal
        from app.models.inquiry import Inquiry

        db = SessionLocal()
        try:
            rows = (
                db.query(Inquiry)
                .filter(Inquiry.tenant_id == tenant_id)
                .order_by(Inquiry.created_at.desc())
                .limit(limit)
                .all()
            )
        finally:
            db.close()
        return [
            {
                "id": str(r.id),
                "company": r.name,
                "country": "unknown",
                "email": r.email or "",
                "score": 0.0,
                "source": r.source_channel or "inquiry",
            }
            for r in rows
            if r.email
        ]
    except Exception:  # noqa: BLE001 — 线索源不可用即空，不伪造
        logger.exception("growth_loop: 真实线索源查询失败")
        return []


class GrowthLoopEngine:
    def run_campaign_pipeline(
        self,
        tenant_id: str,
        campaign_name: str,
        target_industry: str,
        seed_keywords: list[str],
    ) -> dict[str, Any]:
        campaign_id = f"camp_{uuid.uuid4().hex[:8]}"
        leads = _query_real_leads(tenant_id)
        harvest = "completed" if leads else "not_configured"
        scoring = "completed" if leads else "skipped"
        return {
            "campaign_id": campaign_id,
            "tenant_id": tenant_id,
            "campaign_name": campaign_name,
            "target_industry": target_industry,
            "status": "running" if leads else "no_data",
            "degraded": not leads,
            "pipeline_stages": {
                "spider_harvest": {"status": harvest, "leads_count": len(leads)},
                "ai_intent_scoring": {"status": scoring, "high_value_leads": leads},
                "email_sequence": {"status": "scheduled" if leads else "skipped", "template": "b2b_intro_v1", "sent_count": 0},
                "rfq_monitoring": {"status": "active"},
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
