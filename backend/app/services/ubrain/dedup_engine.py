# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
线索去重引擎 —— 统一模型的核心组件

去重策略（优先级降序）：
1. 邮箱精确匹配（最强信号）
2. LinkedIn URL 精确匹配
3. 域名 + 公司名模糊匹配（Jaro-Winkler 相似度）
4. 电话精确匹配

合并策略：
- 保留最新/最完整的信息
- 合并所有来源渠道
- 评分取最高值
- 标签取并集
"""

from __future__ import annotations

import logging
from difflib import SequenceMatcher
from typing import Optional, Any

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.prospect_lead import ProspectLead

logger = logging.getLogger(__name__)

# 公司名模糊匹配阈值
_COMPANY_NAME_SIMILARITY_THRESHOLD = 0.85


def _normalize_company_name(name: Optional[str]) -> Optional[str]:
    """规范化公司名用于模糊匹配。"""
    if not name:
        return None
    # 小写 + 移除常见后缀 + 移除标点
    normalized = name.lower().strip()
    for suffix in [
        " inc", " ltd", " limited", " llc", " corp", " corporation",
        " co.", " co ", " gmbh", " ag", " sa", " s.a.",
        " limited company", " pte", " pvt",
    ]:
        normalized = normalized.removesuffix(suffix).strip()
    # 移除标点
    normalized = "".join(c for c in normalized if c.isalnum() or c.isspace())
    return normalized.strip()


def _similarity(a: Optional[str], b: Optional[str]) -> float:
    """计算两个字符串的相似度（Jaro-Winkler 近似）。"""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def find_duplicate(
    db: Session,
    *,
    email: Optional[str] = None,
    linkedin_url: Optional[str] = None,
    domain: Optional[str] = None,
    company_name: Optional[str] = None,
    phone: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> Optional[ProspectLead]:
    """查找可能重复的线索。

    返回：如果找到重复，返回主线索；否则返回 None
    """
    # 策略 1：邮箱精确匹配（最强信号）
    if email and "@" in email:
        email_lower = email.lower().strip()
        existing = (
            db.query(ProspectLead)
            .filter(
                ProspectLead.email == email_lower,
                ProspectLead.is_duplicate.is_(None),
            )
        )
        if tenant_id:
            existing = existing.filter(ProspectLead.tenant_id == tenant_id)

        lead = existing.first()
        if lead:
            logger.debug(f"去重命中（邮箱）: {email} -> {lead.id}")
            return lead

    # 策略 2：LinkedIn URL 精确匹配
    if linkedin_url:
        linkedin_normalized = linkedin_url.rstrip("/").lower()
        existing = (
            db.query(ProspectLead)
            .filter(
                ProspectLead.linkedin_url == linkedin_normalized,
                ProspectLead.is_duplicate.is_(None),
            )
        )
        if tenant_id:
            existing = existing.filter(ProspectLead.tenant_id == tenant_id)

        lead = existing.first()
        if lead:
            logger.debug(f"去重命中（LinkedIn）: {linkedin_url} -> {lead.id}")
            return lead

    # 策略 3：域名 + 公司名模糊匹配
    if domain and company_name:
        domain_lower = domain.lower().strip()
        normalized_name = _normalize_company_name(company_name)
        existing = (
            db.query(ProspectLead)
            .filter(
                ProspectLead.domain == domain_lower,
                ProspectLead.is_duplicate.is_(None),
            )
        )
        if tenant_id:
            existing = existing.filter(ProspectLead.tenant_id == tenant_id)

        candidates = existing.all()
        for candidate in candidates:
            if candidate.company_name:
                candidate_normalized = _normalize_company_name(candidate.company_name)
                if candidate_normalized and normalized_name:
                    sim = _similarity(candidate_normalized, normalized_name)
                    if sim >= _COMPANY_NAME_SIMILARITY_THRESHOLD:
                        logger.debug(
                            f"去重命中（公司名相似 {sim:.2f}）: {company_name} -> {candidate.id}"
                        )
                        return candidate

    # 策略 4：电话精确匹配
    if phone:
        phone_normalized = "".join(c for c in phone if c.isdigit())
        if phone_normalized:
            existing = (
                db.query(ProspectLead)
                .filter(
                    ProspectLead.phone.contains(phone_normalized),
                    ProspectLead.is_duplicate.is_(None),
                )
            )
            if tenant_id:
                existing = existing.filter(ProspectLead.tenant_id == tenant_id)

            lead = existing.first()
            if lead:
                logger.debug(f"去重命中（电话）: {phone} -> {lead.id}")
                return lead

    return None


def merge_lead_data(
    existing: ProspectLead,
    new_data: dict,
) -> ProspectLead:
    """将新数据合并到现有线索中，保留最新/最完整的信息。

    Args:
        existing: 已存在的线索
        new_data: 新发现的数据字典

    Returns:
        更新后的线索（未 commit）
    """
    # 合并来源
    sources = set(existing.source_detail.get("sources", []))
    new_source = new_data.get("source")
    if new_source:
        sources.add(new_source)
    existing.source_detail["sources"] = list(sources)
    # 补充缺失字段（新数据更完整时覆盖）
    for field in [
        "company_name", "website", "country", "industry",
        "company_size", "revenue_range", "first_name", "last_name",
        "title", "department", "phone", "linkedin_url", "linkedin_id",
    ]:
        new_val = new_data.get(field)
        existing_val = getattr(existing, field, None)
        if new_val and not existing_val:
            setattr(existing, field, new_val)

    # 邮箱：保留已验证的；如果新邮箱已验证而旧的未验证，则覆盖
    new_email = new_data.get("email")
    new_email_verified = new_data.get("email_verified")
    if new_email:
        if not existing.email:
            existing.email = new_email.lower().strip()
            existing.email_verified = new_email_verified
        elif new_email_verified == "valid" and existing.email_verified != "valid":
            existing.email = new_email.lower().strip()
            existing.email_verified = new_email_verified

    # 合并标签
    new_tags = set(new_data.get("tags", []))
    existing_tags = set(existing.tags or [])
    existing.tags = list(existing_tags | new_tags)
    # 评分：取最高值
    new_fit = new_data.get("fit_score")
    if new_fit and new_fit > existing.fit_score:
        existing.fit_score = new_fit

    # 合并来源记录
    merged_from = set(existing.merged_from or [])
    new_source_id = new_data.get("source_id")
    if new_source_id and new_source_id != str(existing.id):
        merged_from.add(new_source_id)
    existing.merged_from = list(merged_from)
    # 重新计算综合分
    existing.overall_score = existing.compute_overall_score()
    existing.version += 1
    return existing


def save_or_merge_lead(
    db: Session,
    data: dict,
    *,
    tenant_id: Optional[str] = None,
    created_by: Optional[str] = None,
) -> tuple[ProspectLead, bool]:
    """保存或合并线索。

    Returns:
        (lead, is_new) — is_new=True 表示新创建，False 表示合并到已有线索
    """
    # 规范化数据
    email = data.get("email")
    linkedin_url = data.get("linkedin_url")
    domain = data.get("domain")
    company_name = data.get("company_name")
    phone = data.get("phone")
    # 查找重复
    duplicate = find_duplicate(
        db,
        email=email,
        linkedin_url=linkedin_url,
        domain=domain,
        company_name=company_name,
        phone=phone,
        tenant_id=tenant_id,
    )
    if duplicate:
        # 合并到已有线索
        merge_lead_data(duplicate, data)
        db.commit()
        db.refresh(duplicate)
        return duplicate, False

    # 创建新线索
    lead = ProspectLead(
        email=email.lower().strip() if email else None,
        email_domain=email.split("@")[1].lower() if email and "@" in email else None,
        linkedin_url=linkedin_url.rstrip("/").lower() if linkedin_url else None,
        linkedin_id=data.get("linkedin_id"),
        phone=phone,
        company_name=company_name,
        company_name_normalized=_normalize_company_name(company_name),
        domain=domain.lower().strip() if domain else None,
        website=data.get("website"),
        country=data.get("country"),
        industry=data.get("industry"),
        company_size=data.get("company_size"),
        revenue_range=data.get("revenue_range"),
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        title=data.get("title"),
        department=data.get("department"),
        source=data.get("source", "google_cse"),
        source_detail=data.get("source_detail", {}),
        fit_score=data.get("fit_score", 50),
        engagement_score=data.get("engagement_score", 0),
        overall_score=data.get("fit_score", 50),
        email_verified=data.get("email_verified"),
        tags=data.get("tags", []),
        notes=data.get("notes"),
        tenant_id=tenant_id,
        created_by=created_by,
        metadata=data.get("metadata", {}),
    )
    lead.overall_score = lead.compute_overall_score()
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead, True


class DedupEngine:
    """线索去重引擎类。"""

    def __init__(self, db: Session | None = None):
        self.db = db

    async def check_duplicate(self, criteria: dict[str, Any]) -> dict[str, Any]:
        """检查是否存在重复线索。"""
        email = criteria.get("email")
        company = criteria.get("company") or criteria.get("company_name")
        if self.db and (email or company):
            dup = find_duplicate(self.db, email=email, company_name=company)
            if dup:
                return {"is_duplicate": True, "lead_id": dup.id}
        return {"is_duplicate": False}
