from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class InquiryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=1, max_length=50)
    email: Optional[str] = Field(None, max_length=200)
    product: Optional[str] = Field(None, max_length=100)
    message: str = Field(..., min_length=1, max_length=2000)


class InquiryUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern=r"^(pending|contacted|closed|archived)$")


class InquiryResponse(BaseModel):
    id: str
    name: str
    phone: str
    email: Optional[str]
    product: Optional[str]
    message: str
    status: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
