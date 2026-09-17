# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Pydantic schemas for PublishTask."""
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PublishTaskBase(BaseModel):
    """Base schema for PublishTask."""
    tenant_id: UUID
    content_id: UUID
    platform_id: str = Field(..., max_length=50)
    platform_account_id: Optional[UUID] = None
    content_data: Dict[str, Any] = Field(default_factory=dict)
    scheduled_at: Optional[datetime] = None
    created_by: Optional[UUID] = None


class PublishTaskCreate(PublishTaskBase):
    """Schema for creating a new PublishTask."""
    pass


class PublishTaskUpdate(BaseModel):
    """Schema for updating a PublishTask (partial)."""
    platform_account_id: Optional[UUID] = None
    content_data: Optional[Dict[str, Any]] = None
    scheduled_at: Optional[datetime] = None
    max_retries: Optional[str] = None


class PublishTaskResponse(PublishTaskBase):
    """Schema for PublishTask response."""
    id: UUID
    status: str
    retry_count: str
    max_retries: str
    platform_post_id: Optional[str] = None
    platform_post_url: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
