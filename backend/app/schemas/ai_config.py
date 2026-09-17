# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class AIModelProviderCreate(BaseModel):
    name: str
    provider_type: str  # openai, anthropic, gemini, nvidia, deepseek
    api_key: str
    base_url: Optional[str] = None
    default_model: Optional[str] = None
    is_active: Optional[bool] = True
    is_default: Optional[bool] = False
    description: Optional[str] = None


class AIModelProviderUpdate(BaseModel):
    name: Optional[str] = None
    provider_type: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    default_model: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    description: Optional[str] = None


class AIModelProviderResponse(BaseModel):
    id: str
    name: str
    provider_type: str
    base_url: Optional[str]
    default_model: Optional[str]
    is_active: bool
    is_default: bool
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class AIModelConfigCreate(BaseModel):
    provider_id: str
    model_name: str
    model_type: str  # code, logic, general, chinese, vision
    temperature: Optional[str] = "0.7"
    max_tokens: Optional[str] = "4096"
    context_window: Optional[str] = None
    is_active: Optional[bool] = True
    is_default: Optional[bool] = False
    metadata: Optional[Dict[str, Any]] = None


class AIModelConfigUpdate(BaseModel):
    model_name: Optional[str] = None
    model_type: Optional[str] = None
    temperature: Optional[str] = None
    max_tokens: Optional[str] = None
    context_window: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class AIModelConfigResponse(BaseModel):
    id: str
    provider_id: str
    provider_name: Optional[str]
    model_name: str
    model_type: str
    temperature: str
    max_tokens: str
    context_window: Optional[str]
    is_active: bool
    is_default: bool
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class ModelSwitchRequest(BaseModel):
    provider_id: str
    model_type: Optional[str] = "general"


class CurrentModelResponse(BaseModel):
    provider_id: str
    provider_name: str
    provider_type: str
    model_name: str
    model_type: str
    temperature: str
    max_tokens: str


class AIUsageStatsResponse(BaseModel):
    total_requests: int
    total_tokens: int
    total_cost: float
    success_rate: float
    avg_duration_ms: float


class ProviderListResponse(BaseModel):
    items: List[AIModelProviderResponse]
    total: int


class ModelListResponse(BaseModel):
    items: List[AIModelConfigResponse]
    total: int
