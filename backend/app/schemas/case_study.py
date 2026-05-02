from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CaseImageCreate(BaseModel):
    image_url: str
    image_alt: Optional[str] = None
    sort_order: Optional[int] = 0


class CaseImageUpdate(BaseModel):
    image_url: Optional[str] = None
    image_alt: Optional[str] = None
    sort_order: Optional[int] = None


class CaseImageResponse(BaseModel):
    id: str
    case_id: str
    image_url: str
    image_alt: Optional[str]
    sort_order: int
    created_at: datetime
    model_config = {"from_attributes": True}


class CaseStudyCreate(BaseModel):
    product_id: Optional[str] = None
    project_name: str
    slug: str
    client_name: Optional[str] = None
    materials_used: Optional[str] = None
    construction_area: Optional[str] = None
    project_date: Optional[str] = None
    location: Optional[str] = None
    project_address: Optional[str] = None
    description: Optional[str] = None
    cover_image: Optional[str] = None
    status: Optional[str] = "draft"
    sort_order: Optional[int] = 0


class CaseStudyUpdate(BaseModel):
    product_id: Optional[str] = None
    project_name: Optional[str] = None
    slug: Optional[str] = None
    client_name: Optional[str] = None
    materials_used: Optional[str] = None
    construction_area: Optional[str] = None
    project_date: Optional[str] = None
    location: Optional[str] = None
    project_address: Optional[str] = None
    description: Optional[str] = None
    cover_image: Optional[str] = None
    status: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class CaseStudyResponse(BaseModel):
    id: str
    product_id: Optional[str]
    project_name: str
    slug: str
    client_name: Optional[str]
    materials_used: Optional[str]
    construction_area: Optional[str]
    project_date: Optional[str]
    location: Optional[str]
    project_address: Optional[str]
    description: Optional[str]
    cover_image: Optional[str]
    status: str
    sort_order: int
    view_count: int
    is_active: bool
    images: list[CaseImageResponse] = []
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
