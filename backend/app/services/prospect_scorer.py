# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""潜客线索 4 维评分服务（匹配度 / 邮箱可信度 / 证据完整度 / 联系人完整度）。"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models.prospect_lead import ProspectLead

logger = logging.getLogger(__name__)

# ── 权重常量 ──
WEIGHT_MATCH = 0.30
WEIGHT_EMAIL = 0.25
WEIGHT_EVIDENCE = 0.25
WEIGHT_CONTACT = 0.20

MAX_EVIDENCE_FOR_FULL = 5  # 5 条证据 = 满分


def compute_match_score(lead: ProspectLead, search_keywords: Optional[list[str]] = None) -> int:
    """计算匹配度（0-100）。

    维度：
    - 产品词覆盖（40分）
    - 行业匹配（30分）
    - 国家/地区匹配（30分）
    """
    score = 0
    # 产品词覆盖：source_detail 中的搜索关键词与公司信息匹配
    if search_keywords and lead.company_name:
        company_lower = (lead.company_name or "").lower()
        industry_lower = (lead.industry or "").lower()
        matched = sum(
            1 for kw in search_keywords
            if kw.lower() in company_lower or kw.lower() in industry_lower
        )
        score += min(40, int(matched / max(len(search_keywords), 1) * 40))
    elif lead.fit_score:
        # 回退到旧 fit_score，映射到 0-100 范围
        score += min(100, int(lead.fit_score))

    # 行业匹配
    if lead.industry:
        score += 30
    else:
        score += 5  # 有公司名但无行业，给基础分

    # 国家/地区
    if lead.country:
        score += 30
    else:
        score += 5

    return min(100, score)


def compute_email_score(lead: ProspectLead) -> int:
    """计算邮箱可信度（0-100）。

    根据 email_verified 状态直接映射：
    - valid → 90
    - risky → 50
    - unknown → 30
    - invalid → 0
    - 无邮箱 → 10（有其他联系方式）
    """
    if not lead.email:
        # 无邮箱但有电话/LinkedIn，给基础分
        if lead.phone or lead.linkedin_url:
            return 15
        return 0

    status = (lead.email_verified or "unknown").lower()
    return {"valid": 90, "risky": 50, "unknown": 30, "invalid": 0}.get(status, 30)


def compute_evidence_score(lead: ProspectLead) -> int:
    """计算证据完整度（0-100）。

    evidence_chain 中每条有效证据 20 分，满分需 5 条。
    """
    if not lead.evidence_chain:
        return 0
    count = len(lead.evidence_chain)
    return min(100, int(count / MAX_EVIDENCE_FOR_FULL * 100))


def compute_contact_score(lead: ProspectLead) -> int:
    """计算联系人完整度（0-100）。

    每项 25 分：邮箱 / 电话 / 职位 / LinkedIn
    """
    score = 0
    if lead.email:
        score += 25
    if lead.phone:
        score += 25
    if lead.title:
        score += 25
    if lead.linkedin_url:
        score += 25
    return score


def score_lead(
    lead: ProspectLead,
    search_keywords: Optional[list[str]] = None,
    *,
    persist: bool = True,
    db: Optional[Session] = None,
) -> dict:
    """计算 4 维评分并更新 ProspectLead 记录。

    Args:
        lead: 线索对象
        search_keywords: 搜客时使用的产品关键词列表
        persist: 是否持久化到数据库
        db: SQLAlchemy Session（persist=True 时必须）

    Returns:
        评分明细 dict: {match, email, evidence, contact, overall}
    """
    s_match = compute_match_score(lead, search_keywords)
    s_email = compute_email_score(lead)
    s_evidence = compute_evidence_score(lead)
    s_contact = compute_contact_score(lead)
    overall = int(
        s_match * WEIGHT_MATCH
        + s_email * WEIGHT_EMAIL
        + s_evidence * WEIGHT_EVIDENCE
        + s_contact * WEIGHT_CONTACT
    )
    # 追踪加分
    if lead.open_count and lead.open_count > 0:
        overall += 2
    if lead.reply_count and lead.reply_count > 0:
        overall += 5
    overall = max(0, min(100, overall))
    if persist and db:
        lead.score_match = s_match
        lead.score_email = s_email
        lead.score_evidence = s_evidence
        lead.score_contact = s_contact
        lead.overall_score = overall
        # 同步旧字段（向后兼容）
        lead.fit_score = s_match
        lead.engagement_score = int(
            s_email * 0.5 + s_contact * 0.5
        ) if (s_email or s_contact) else 0
        db.flush()

    return {
        "match": s_match,
        "email": s_email,
        "evidence": s_evidence,
        "contact": s_contact,
        "overall": overall,
    }


def batch_score_leads(
    db: Session,
    tenant_id: str,
    search_keywords: Optional[list[str]] = None,
    limit: int = 500,
) -> int:
    """批量重算评分。

    Returns:
        已更新的线索数量
    """
    leads = (
        db.query(ProspectLead)
        .filter(ProspectLead.tenant_id == tenant_id)
        .order_by(ProspectLead.created_at.desc())
        .limit(limit)
        .all()
    )
    count = 0
    for lead in leads:
        score_lead(lead, search_keywords, persist=True, db=db)
        count += 1
    db.flush()  # 交给上层调用者控制 commit/rollback
    logger.info("batch_score_leads: tenant=%s updated=%d", tenant_id, count)
    return count


class ProspectScorer:
    """线索与潜在客户多维评分引擎。"""

    def __init__(self, db: Session | None = None):
        self.db = db

    async def score_batch(
        self,
        tenant_id: str,
        leads: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """批量对线索进行价值与意向打分。"""
        leads = leads or []
        scored_results: list[dict[str, Any]] = []
        if not leads and self.db:
            # 从库中查询真实线索
            db_leads = (
                self.db.query(ProspectLead)
                .filter(ProspectLead.tenant_id == tenant_id)
                .limit(100)
                .all()
            )
            for l in db_leads:
                res = score_lead(l, persist=False, db=self.db)
                scored_results.append({"id": l.id, "score": res.get("overall", 65)})
        else:
            for item in leads:
                lead_id = item.get("id") or "lead"
                base_score = item.get("score") or 70
                scored_results.append({"id": lead_id, "score": base_score})
        return scored_results
