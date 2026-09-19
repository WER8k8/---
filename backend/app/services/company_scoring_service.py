# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P0-7 — ICP / Intent / Account 评分引擎。

背景：Company.icp_score / intent_score / account_score 三列全库无写入方，恒为 0，
导致「用户分层」维度完全失效（CRM 无法按价值排序、线索分配无公司价值依据）。

本模块提供结构化 ICP 规则 + 信号加权，在公司落库/更新时写入三列，并留痕
IntentEngineRun 以便审计与回溯。规则以模块级 CONFIG 形式集中管理，便于运营调参。
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.company import Company, CompanySignal, IntentEngineRun

logger = logging.getLogger(__name__)


# ── 结构化 ICP 配置（集中管理，运营可在不改动代码逻辑的前提下调参）──
ICP_CONFIG: dict[str, Any] = {
    # 建材/外贸 B2B 目标行业（子串匹配，命中即视为高匹配）
    "target_industries": [
        "building material", "building_material", "buildings", "construction",
        "architecture", "real estate", "real_estate", "hardware", "cement",
        "steel", "ceramic", "glass", "concrete", "timber", "plumbing",
        "electrical", "decoration", "decorative", "infrastructure", "contractor",
    ],
    # 国家分层（一线高价值市场）
    "country_tier1": [
        "us", "usa", "united states", "uk", "united kingdom", "germany", "de",
        "france", "fr", "united arab emirates", "uae", "saudi arabia", "sa",
        "australia", "au", "canada", "ca", "japan", "jp", "netherlands", "nl",
    ],
    "country_tier2": [
        "spain", "es", "italy", "it", "poland", "pl", "sweden", "se",
        "norway", "no", "singapore", "sg", "south korea", "kr", "qatar", "qa",
        "kuwait", "kw", "oman", "om", "mexico", "mx", "brazil", "br",
    ],
    # 员工规模分层（字符串值，常见形如 "51-200" / "1000+" / "11-50"）
    "employees_high": ["1000+", "5000+", "10000+", "500-1000"],
    "employees_mid": ["201-500", "51-200", "101-200"],
    # 营收分层（常见形如 "$10M-$50M" / "50M+"）
    "revenue_high": ["100m+", "50m+", "$100m", "$50m"],
    "revenue_mid": ["10m+", "$10m", "1m-10m", "$1m"],
    # 认证加分项
    "certifications_bonus": ["ce", "fcc", "iso", "ul", "rohs", "reach"],
}


def _norm(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def compute_icp_score(company: Company) -> tuple[int, dict[str, int]]:
    """计算 ICP 匹配分（0-100），返回 (总分, 分项明细)。"""
    breakdown: dict[str, int] = {}
    ind = _norm(company.industry)
    if ind:
        if any(t in ind for t in ICP_CONFIG["target_industries"]):
            breakdown["industry"] = 40
        else:
            breakdown["industry"] = 20
    else:
        breakdown["industry"] = 0

    country = _norm(company.country)
    if country in ICP_CONFIG["country_tier1"]:
        breakdown["country"] = 25
    elif country in ICP_CONFIG["country_tier2"]:
        breakdown["country"] = 12
    else:
        breakdown["country"] = 0

    emp = _norm(company.employees)
    if emp in ICP_CONFIG["employees_high"]:
        breakdown["employees"] = 15
    elif emp in ICP_CONFIG["employees_mid"]:
        breakdown["employees"] = 10
    elif emp:
        breakdown["employees"] = 5
    else:
        breakdown["employees"] = 0

    rev = _norm(company.revenue_range)
    if rev in ICP_CONFIG["revenue_high"]:
        breakdown["revenue"] = 10
    elif rev in ICP_CONFIG["revenue_mid"]:
        breakdown["revenue"] = 5
    else:
        breakdown["revenue"] = 0

    certs = _norm(company.certifications)
    if any(c in certs for c in ICP_CONFIG["certifications_bonus"]):
        breakdown["certifications"] = 10
    else:
        breakdown["certifications"] = 0

    total = sum(breakdown.values())
    return min(total, 100), breakdown


def compute_intent_score(db: Session, company: Company) -> tuple[int, dict[str, Any]]:
    """基于 CompanySignal 加权求和（0-100）。无信号则为 0。"""
    if company.id is None:
        return 0, {"signals": 0, "raw_weight": 0}
    rows = (
        db.query(CompanySignal)
        .filter(CompanySignal.company_id == company.id)
        .all()
    )
    raw = 0
    for r in rows:
        w = int(getattr(r, "weight", 0) or 0)
        conf = float(getattr(r, "confidence", 1.0) or 1.0)
        raw += int(w * max(0.0, min(1.0, conf)))
    return min(raw, 100), {"signals": len(rows), "raw_weight": raw}


def compute_account_score(company: Company) -> tuple[int, dict[str, int]]:
    """基于公司规模/可触达性的账户价值分（0-100）。"""
    breakdown: dict[str, int] = {}
    emp = _norm(company.employees)
    if emp in ICP_CONFIG["employees_high"]:
        breakdown["employees"] = 30
    elif emp in ICP_CONFIG["employees_mid"]:
        breakdown["employees"] = 20
    elif emp:
        breakdown["employees"] = 10
    else:
        breakdown["employees"] = 0

    rev = _norm(company.revenue_range)
    if rev in ICP_CONFIG["revenue_high"]:
        breakdown["revenue"] = 25
    elif rev in ICP_CONFIG["revenue_mid"]:
        breakdown["revenue"] = 15
    else:
        breakdown["revenue"] = 0

    breakdown["linkedin"] = 10 if _norm(company.linkedin) else 0
    breakdown["website"] = 10 if _norm(company.website) else 0
    breakdown["phone"] = 5 if _norm(company.phone) else 0
    breakdown["domain"] = 5 if _norm(company.domain) else 0

    conf = float(getattr(company, "confidence", 0.0) or 0.0)
    breakdown["confidence"] = 15 if conf >= 0.6 else (5 if conf > 0 else 0)

    total = sum(breakdown.values())
    return min(total, 100), breakdown


def score_company(db: Session, company: Company) -> dict[str, Any]:
    """计算并回写三列评分，留痕 IntentEngineRun。返回汇总。"""
    icp, icp_bd = compute_icp_score(company)
    intent, intent_bd = compute_intent_score(db, company)
    account, account_bd = compute_account_score(company)

    company.icp_score = icp
    company.intent_score = intent
    company.account_score = account

    run = IntentEngineRun(
        company_id=company.id,
        intent_score=intent,
        icp_score=icp,
        account_score=account,
        signal_breakdown=json.dumps(
            {
                "icp": icp_bd,
                "intent": intent_bd,
                "account": account_bd,
            },
            ensure_ascii=False,
        ),
    )
    db.add(run)
    db.commit()
    db.refresh(company)
    return {
        "company_id": str(company.id) if company.id is not None else None,
        "icp_score": icp,
        "intent_score": intent,
        "account_score": account,
        "breakdown": {"icp": icp_bd, "intent": intent_bd, "account": account_bd},
    }
