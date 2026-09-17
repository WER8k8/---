# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""GW-G-AEO-01 — 站点/母版文案 vs 禁泄露品牌词 + 租户事实一致性。"""

from __future__ import annotations

import json
import re
from typing import Any

from sqlalchemy.orm import Session

from app.models.content_master import ContentMaster
from app.models.tenant import Tenant
from app.services.hermes.brand_audit_service import FORBIDDEN_PATTERNS, audit_brand_leaks

FACT_CLAIM_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(\d+)\s*\+?\s*(countries|国家|markets)", re.I), "market_reach"),
    (re.compile(r"(\d+)\s*\+?\s*(years|年)\s*(experience|经验)", re.I), "years_experience"),
    (re.compile(r"(world[\s-]?leading|行业第一|全球领先|largest)", re.I), "superlative"),
)


def _tenant_facts(tenant: Tenant) -> dict[str, str]:
    """实现 租户facts 的功能。
    
    :param tenant: 参数 tenant（类型: Tenant）
    :return: 返回 dict[str, str] 结果
    """
    settings: dict[str, Any] = {}
    if tenant.settings:
        try:
            settings = json.loads(tenant.settings)
        except (json.JSONDecodeError, TypeError):
            settings = {}
    return {
        "tenant_name": tenant.name or "",
        "domain": tenant.domain or "",
        "tagline": str(settings.get("tagline") or settings.get("company_intro") or "")[:500],
    }


def audit_tenant_content_masters(db: Session, *, tenant_id: str, limit: int = 30) -> list[dict[str, Any]]:
    """实现 audit租户内容masters 的功能。
    
    :param db: 参数 db（类型: Session）
    :param tenant_id: 参数 tenant_id（类型: str）
    :param limit: 参数 limit（类型: int）
    :return: 返回 list[dict[str, Any]] 结果
    """
    rows = (
        db.query(ContentMaster)
        .filter(ContentMaster.tenant_id == tenant_id)
        .order_by(ContentMaster.updated_at.desc())
        .limit(limit)
        .all()
    )
    findings: list[dict[str, Any]] = []
    for row in rows:
        text = f"{row.title or ''}\n{row.body or ''}"
        for pattern, label in FORBIDDEN_PATTERNS:
            if pattern.search(text):
                findings.append(
                    {
                        "kind": "brand_leak",
                        "content_master_id": row.id,
                        "term": label,
                        "title": row.title,
                    }
                )
        for pattern, kind in FACT_CLAIM_PATTERNS:
            m = pattern.search(text)
            if m:
                findings.append(
                    {
                        "kind": "unverified_fact_claim",
                        "claim_type": kind,
                        "content_master_id": row.id,
                        "excerpt": m.group(0)[:120],
                        "title": row.title,
                    }
                )
    return findings


def run_aeo_fact_audit(db: Session, *, tenant_id: str | None = None) -> dict[str, Any]:
    """AEO 事实审计：代码库品牌抽检 + 租户母版事实声明。"""
    brand = audit_brand_leaks(max_findings=30)
    tenant_findings: list[dict[str, Any]] = []
    tenants_scanned = 0
    q = db.query(Tenant).filter(Tenant.is_active.is_(True))
    if tenant_id:
        q = q.filter(Tenant.id == tenant_id)
    for tenant in q.limit(20).all():
        tenants_scanned += 1
        facts = _tenant_facts(tenant)
        cms = audit_tenant_content_masters(db, tenant_id=str(tenant.id))
        tenant_findings.append(
            {
                "tenant_id": str(tenant.id),
                "tenant_name": facts["tenant_name"],
                "domain": facts["domain"],
                "findings": cms,
                "findings_count": len(cms),
            }
        )

    total_cms = sum(t["findings_count"] for t in tenant_findings)
    ok = brand.get("ok", True) and total_cms == 0
    return {
        "ok": ok,
        "gw_task": "GW-G-AEO-01",
        "brand_audit": brand,
        "tenants_scanned": tenants_scanned,
        "tenant_content_findings": tenant_findings,
        "total_content_findings": total_cms,
    }
