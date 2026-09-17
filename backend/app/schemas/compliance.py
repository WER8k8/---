# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ComplianceRuleCreate(BaseModel):
    rule_name: str
    rule_type: str
    keywords: List[str]
    severity: str
    description: Optional[str] = None


class ComplianceRuleUpdate(BaseModel):
    rule_name: Optional[str] = None
    rule_type: Optional[str] = None
    keywords: Optional[List[str]] = None
    severity: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ComplianceRuleResponse(BaseModel):
    id: str
    rule_name: str
    rule_type: str
    keywords: List[str]
    severity: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class ComplianceScanResultCreate(BaseModel):
    content_id: str
    content_type: str
    content_title: Optional[str] = None
    content_text: str


class ComplianceScanResultResponse(BaseModel):
    id: str
    content_id: str
    content_type: str
    content_title: Optional[str]
    content_text: str
    scan_status: str
    total_issues: int
    high_severity_count: int
    medium_severity_count: int
    low_severity_count: int
    scan_details: Optional[dict]
    suggestions: Optional[List[str]]
    scanned_at: Optional[datetime]
    created_at: datetime
    model_config = {"from_attributes": True}


class ComplianceViolationResponse(BaseModel):
    id: str
    scan_result_id: str
    rule_id: str
    rule_name: str
    rule_type: str
    severity: str
    matched_text: str
    context: str
    suggestion: Optional[str]
    is_resolved: bool
    resolved_at: Optional[datetime]
    created_at: datetime
    model_config = {"from_attributes": True}


class AdvertisementLawKeywordCreate(BaseModel):
    keyword: str
    category: str
    severity: str
    description: Optional[str] = None
    alternative: Optional[str] = None


class AdvertisementLawKeywordUpdate(BaseModel):
    keyword: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    description: Optional[str] = None
    alternative: Optional[str] = None
    is_active: Optional[bool] = None


class AdvertisementLawKeywordResponse(BaseModel):
    id: str
    keyword: str
    category: str
    severity: str
    description: Optional[str]
    alternative: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class BatchDeleteRequest(BaseModel):
    ids: List[str]
