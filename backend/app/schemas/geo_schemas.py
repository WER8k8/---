# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""GEO Schemas - Pydantic models for GEO engine

This module defines the Pydantic models used by the GEO engine API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional


class GenerateRequest(BaseModel):
    """Request model for content generation/evaluation"""
    keyword: str = Field(min_length=1, max_length=255, description="Target keyword")
    intent: str = Field(min_length=1, description="User intent / query objective")
    content: str = Field(min_length=1, description="Content to evaluate or use as base")
    product_slug: str = Field(default="polyurethane-lightweight-concrete", description="Related product slug")


class LeadRequest(BaseModel):
    """Request model for creating a new lead inquiry"""
    product_slug: str = Field(default="polyurethane-lightweight-concrete", description="Product slug")
    keyword: Optional[str] = Field(default=None, description="Source keyword")
    name: Optional[str] = Field(default=None, description="Customer name")
    phone: str = Field(min_length=6, max_length=50, description="Customer phone")
    region: Optional[str] = Field(default=None, description="Customer region")
    distance_km: Optional[float] = Field(default=None, description="Distance to factory in km")
    quantity_m3: Optional[float] = Field(default=None, description="Concrete quantity in cubic meters")
    message: Optional[str] = Field(default=None, description="Customer message")
    source_url: Optional[str] = Field(default=None, description="Source URL that generated this inquiry")
    source_channel: Optional[str] = Field(default="mobile_h5", description="Traffic source channel")


class GuardRequest(BaseModel):
    """Request model for RankGuard evaluation"""
    lcp_ms: int = Field(description="Largest Contentful Paint in milliseconds")
    inp_ms: int = Field(description="Interaction to Next Paint in milliseconds")
    error_rate: float = Field(default=0, ge=0, le=1, description="Error rate (0-1)")
    inquiry_rate_delta: float = Field(default=0, description="Inquiry rate change delta")
    rank_signal_delta: float = Field(default=0, description="Rank signal change delta")


class ProductResponse(BaseModel):
    """Response model for product information"""
    slug: str
    name: str
    density_kg_m3: int
    strength_mpa: float
    thermal_conductivity: float
    factory_price: float
    price_valid_until: str
    phone: str
