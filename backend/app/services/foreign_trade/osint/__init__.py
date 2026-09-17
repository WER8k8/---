# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""OSINT 六层背调 — 改编自 chefroger/smart-trade-ai (MIT)，见 THIRD_PARTY_ATTRIBUTION.md。"""

from app.services.foreign_trade.osint.constants import (
    FREE_PLATFORMS,
    PERSONAL_EMAIL_DOMAINS,
    SANCTIONS_SOURCES,
    get_sanctions_cache_dir,
    http_get,
    set_sanctions_cache_dir,
)
from app.services.foreign_trade.osint.email_verify import verify_corporate_email
from app.services.foreign_trade.osint.linkedin_verify import linkedin_company_verify
from app.services.foreign_trade.osint.orchestrator import osint_full_check
from app.services.foreign_trade.osint.sanctions import check_sanctions
from app.services.foreign_trade.osint.scoring import compute_risk_score, generate_recommendations
from app.services.foreign_trade.osint.tech_stack import detect_tech_stack
from app.services.foreign_trade.osint.whois import domain_whois

__all__ = [
    "domain_whois",
    "verify_corporate_email",
    "check_sanctions",
    "detect_tech_stack",
    "linkedin_company_verify",
    "osint_full_check",
    "compute_risk_score",
    "generate_recommendations",
    "PERSONAL_EMAIL_DOMAINS",
    "FREE_PLATFORMS",
    "SANCTIONS_SOURCES",
    "set_sanctions_cache_dir",
    "get_sanctions_cache_dir",
    "http_get",
]
