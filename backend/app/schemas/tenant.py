# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""SaaS多租户Schema"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ==================== 自定义域名绑定 ====================

class DomainBinding(BaseModel):
    """添加域名请求"""
    domain: str


class DomainBindingResponse(BaseModel):
    """域名绑定信息"""
    domain: str
    verified: bool = False
    ssl_status: str = "none"  # none/pending/active/failed
    cname_target: str = "saas.youding.com"


class DomainListResponse(BaseModel):
    """域名列表响应"""
    items: List[DomainBindingResponse]


# ==================== TenantPlan ====================

class TenantPlanCreate(BaseModel):
    name: str
    code: str
    price_monthly: int = 0
    price_yearly: int = 0
    max_users: int = 1
    max_sites: int = 1
    max_products: int = 10
    max_ai_quota: int = 0
    features: Optional[str] = "[]"
    is_active: Optional[bool] = True


class TenantPlanUpdate(BaseModel):
    name: Optional[str] = None
    price_monthly: Optional[int] = None
    price_yearly: Optional[int] = None
    max_users: Optional[int] = None
    max_sites: Optional[int] = None
    max_products: Optional[int] = None
    max_ai_quota: Optional[int] = None
    features: Optional[str] = None
    is_active: Optional[bool] = None


class TenantPlanResponse(BaseModel):
    id: str
    name: str
    code: str
    price_monthly: int
    price_yearly: int
    max_users: int
    max_sites: int
    max_products: int
    max_ai_quota: int
    features: str
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


# ==================== Tenant ====================

class TenantCreate(BaseModel):
    name: str
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    domain: str
    plan_id: str
    status: Optional[str] = "trial"
    trial_ends_at: Optional[datetime] = None


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    domain: Optional[str] = None
    plan_id: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None
    settings: Optional[str] = None  # JSON 字符串，租户自定义设置


class TenantSelfUpdate(BaseModel):
    """租户自助更新（仅允许更新 settings）"""
    settings: str  # JSON 字符串，租户自定义设置


class TenantResponse(BaseModel):
    id: str
    name: str
    contact_name: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    domain: str
    custom_domains: Optional[str] = ""
    plan_id: str
    plan: Optional[TenantPlanResponse] = None
    status: str
    trial_ends_at: Optional[datetime]
    subscribed_at: Optional[datetime]
    expires_at: Optional[datetime]
    ai_quota_used: int
    storage_used: int
    settings: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class TenantListResponse(BaseModel):
    items: List[TenantResponse]
    total: int
    page: int
    page_size: int


# ==================== Stats ====================

class TenantStatsResponse(BaseModel):
    total_tenants: int
    active_tenants: int
    trial_tenants: int
    suspended_tenants: int
    expiring_soon: int
    new_tenants_this_month: int = 0
    monthly_revenue: int  # 本月实收，单位：分（台账或已支付订单）


class TenantOverviewResponse(BaseModel):
    stats: TenantStatsResponse
    recent_tenants: List[TenantResponse]


# ==================== Invoice ====================

class TenantInvoiceResponse(BaseModel):
    id: str
    tenant_id: str
    subscription_id: Optional[str]
    amount: int
    status: str
    paid_at: Optional[datetime]
    due_at: Optional[datetime]
    created_at: datetime
    model_config = {"from_attributes": True}


class TenantInvoiceListResponse(BaseModel):
    items: List[TenantInvoiceResponse]
    total: int
    page: int
    page_size: int


# ==================== White Label ====================

class BrandColors(BaseModel):
    """租户品牌色配置"""
    primary: str = "#1890ff"
    secondary: str = "#6b7280"
    accent: str = "#f59e0b"


class TenantBrandConfig(BaseModel):
    """租户品牌信息（settings.brand）"""
    site_title: str = ""
    logo_url: str = ""
    brand_colors: BrandColors = BrandColors()
    product_categories: List[str] = []
    company_name: str = ""
    slogan: str = ""
    about_summary: str = ""
    contact_phone: str = ""
    contact_email: str = ""
    footer_text: str = ""
    custom_css: str = ""
    site_content: Optional[Dict[str, Any]] = None


# ==================== Public API (无认证) ====================

class TenantPublicResponse(BaseModel):
    """
    租户公开信息响应（无需登录）。

    当访客访问租户独立子域名时，前端用此接口加载站点配置。
    """
    id: str
    name: str
    domain: str
    status: str
    plan_code: Optional[str] = None
    brand: TenantBrandConfig = TenantBrandConfig()
    is_online: bool = False


# ==================== White Label ====================

class WhiteLabelConfig(BaseModel):
    brand_name: str = ""
    logo_url: str = ""
    domain: str = ""
    custom_css: str = ""
    primary_color: str = "#1890ff"
    footer_text: str = ""


class WhiteLabelUpdate(BaseModel):
    brand_name: Optional[str] = None
    logo_url: Optional[str] = None
    domain: Optional[str] = None
    custom_css: Optional[str] = None
    primary_color: Optional[str] = None
    footer_text: Optional[str] = None


# ==================== 自助注册 ====================

class TenantRegisterSchema(BaseModel):
    """客户自助注册请求"""
    company_name: str
    admin_name: str
    email: str
    password: str
    email_code: str = Field(..., min_length=4, max_length=8, description="邮箱验证码")
    contact_phone: Optional[str] = Field(None, max_length=50)
    primary_product: Optional[str] = Field(None, max_length=80, description="主营产品，用于 AI 快速建站")
    location_hint: Optional[str] = Field(
        None,
        max_length=120,
        description="产地/产业带，如河北廊坊大城县",
    )
    plan_code: str = "free"
    referral_code: Optional[str] = Field(None, max_length=32)
    guest_token: Optional[str] = Field(
        None,
        max_length=64,
        description="未登录期间多媒体工厂访客令牌，注册后绑定历史视频",
    )
    platform_names: Optional[list[str]] = Field(
        None,
        description="开户时预置的平台名称列表（如 微信公众号、YouTube）",
    )
