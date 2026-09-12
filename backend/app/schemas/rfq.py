"""RFQ 请求 / 响应 Pydantic 模型 — 买家需求单（B2B 询价）。"""

from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator

# 允许的贸易条款与项目阶段（受控词表）
INCOTERMS = {"EXW", "FOB", "CIF", "DAP", "DDP"}
PROJECT_STAGES = {"Concept", "Design", "Tender", "Procurement", "Construction"}
QUANTITY_UNITS = {"m2", "m3", "kg", "pcs", "lm", "panel"}


class RFQItemIn(BaseModel):
    """RFQ 明细行（Finder/产品页自动带入）"""
    product_id: Optional[str] = Field(None, max_length=36)
    product_name: str = Field(..., min_length=1, max_length=200)
    product_slug: Optional[str] = Field(None, max_length=200)
    quantity: Optional[float] = Field(None, gt=0)
    unit: Optional[str] = Field(None, max_length=20)
    dimensions: Optional[dict] = None
    notes: Optional[str] = None


class RFQRequirementIn(BaseModel):
    """RFQ 结构化技术要求"""
    req_key: str = Field(..., min_length=1, max_length=100)
    req_label: Optional[str] = Field(None, max_length=200)
    req_value: Optional[str] = None
    required: bool = True


class RFQCreate(BaseModel):
    """RFQ 创建请求（公开端点，无需登录）。"""
    company: str = Field(..., min_length=1, max_length=200)
    company_domain: Optional[str] = Field(None, max_length=300)
    country: str = Field(..., min_length=1, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    project: Optional[str] = Field(None, max_length=300)
    project_type: Optional[str] = Field(None, max_length=100)
    project_stage: Optional[str] = Field(None, max_length=50)
    application: str = Field(..., min_length=1, max_length=200)
    contact_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., max_length=200)
    phone: Optional[str] = Field(None, max_length=50)
    wechat: Optional[str] = Field(None, max_length=100)
    quantity: Optional[float] = Field(None, gt=0)
    quantity_unit: Optional[str] = Field(None, max_length=20)
    delivery_date: Optional[str] = Field(None, description="YYYY-MM-DD")
    incoterm: Optional[str] = Field(None, max_length=20)
    currency: Optional[str] = Field("USD", max_length=10)
    notes: Optional[str] = None
    source: Optional[str] = Field(None, max_length=50)
    source_channel: Optional[str] = Field(None, max_length=50)
    source_url: Optional[str] = Field(None, max_length=1000)
    session_id: Optional[str] = Field(None, max_length=64)
    tenant_id: Optional[str] = Field(None, max_length=36)
    matched_product_ids: Optional[list[str]] = None
    requirements: Optional[list[RFQRequirementIn]] = None
    items: Optional[list[RFQItemIn]] = None
    model_config = {"extra": "ignore"}
    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        """_normalize_email。

        参数说明：
        :param cls: 参数 cls
        :param value: 参数 value
        :return: 返回处理结果。
        """
        email = value.strip().lower()
        if not re.fullmatch(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", email):
            raise ValueError("邮箱格式不正确")
        return email

    @field_validator("incoterm")
    @classmethod
    def _validate_incoterm(cls, value: Optional[str]) -> Optional[str]:
        """_validate_incoterm。

        参数说明：
        :param cls: 参数 cls
        :param value: 参数 value
        :return: 返回处理结果。
        """
        if value is None:
            return None
        v = value.strip().upper()
        if v not in INCOTERMS:
            raise ValueError(f"不支持的贸易条款: {value}，可选 {', '.join(sorted(INCOTERMS))}")
        return v

    @field_validator("project_stage")
    @classmethod
    def _validate_stage(cls, value: Optional[str]) -> Optional[str]:
        """_validate_stage。

        参数说明：
        :param cls: 参数 cls
        :param value: 参数 value
        :return: 返回处理结果。
        """
        if value is None:
            return None
        v = value.strip()
        if v not in PROJECT_STAGES:
            raise ValueError(f"不支持的项目阶段: {value}")
        return v

    @field_validator("quantity_unit")
    @classmethod
    def _validate_unit(cls, value: Optional[str]) -> Optional[str]:
        """_validate_unit。

        参数说明：
        :param cls: 参数 cls
        :param value: 参数 value
        :return: 返回处理结果。
        """
        if value is None:
            return None
        v = value.strip().lower()
        if v not in QUANTITY_UNITS:
            raise ValueError(f"不支持的数量单位: {value}，可选 {', '.join(sorted(QUANTITY_UNITS))}")
        return v


class RFQStatusUpdate(BaseModel):
    """RFQ 状态更新（管理端）。"""
    status: str = Field(..., min_length=1, max_length=50)


class RFQAssignRequest(BaseModel):
    """RFQ 负责人分配（管理端）。"""
    assigned_to: str = Field(..., min_length=1, max_length=36)
