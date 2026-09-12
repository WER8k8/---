from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class InquiryCreate(BaseModel):
    name: str
    phone: str
    wechat: Optional[str] = None
    email: Optional[str] = None
    product: Optional[str] = None  # 改为 product 以匹配 Inquiry 模型
    message: str


class InquiryUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    wechat: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    message: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None


class InquiryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    phone: str
    wechat: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    message: str
    status: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
