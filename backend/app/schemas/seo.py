from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class KeywordCreate(BaseModel):
    keyword: str
    slug: str
    search_volume: Optional[int] = 0
    difficulty: Optional[str] = "medium"
    target_url: Optional[str] = None

class KeywordUpdate(BaseModel):
    search_volume: Optional[int] = None
    difficulty: Optional[str] = None
    current_ranking: Optional[int] = None
    target_url: Optional[str] = None
    is_active: Optional[bool] = None

class KeywordResponse(BaseModel):
    id: str
    keyword: str
    slug: str
    search_volume: int
    difficulty: str
    current_ranking: Optional[int]
    target_url: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}

class KeywordRankingResponse(BaseModel):
    id: str
    keyword_id: str
    ranking: Optional[int]
    page_url: Optional[str]
    search_engine: str
    checked_at: datetime

    model_config = {"from_attributes": True}

class SiteAuditCreate(BaseModel):
    audit_type: str
    url: str

class SiteAuditResponse(BaseModel):
    id: str
    url: Optional[str]
    status: str
    audit_type: str
    score: Optional[float]
    total_issues: int
    critical_issues: int
    warning_issues: int
    report_data: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}

class AiOptimizationLogResponse(BaseModel):
    id: str
    resource_type: str
    resource_id: str
    optimization_type: str
    model_used: Optional[str]
    tokens_used: int
    score_before: Optional[float]
    score_after: Optional[float]
    created_at: datetime

    model_config = {"from_attributes": True}

class LlmsConfigCreate(BaseModel):
    section: str
    content: str

class LlmsConfigUpdate(BaseModel):
    content: Optional[str] = None
    is_active: Optional[bool] = None
    version: Optional[str] = None

class LlmsConfigResponse(BaseModel):
    id: str
    section: str
    content: str
    is_active: bool
    version: str
    created_at: datetime

    model_config = {"from_attributes": True}