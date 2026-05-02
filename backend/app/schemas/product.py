from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ProductDocumentCreate(BaseModel):
    doc_type: str
    file_name: str
    file_path: str
    file_size: Optional[int] = 0
    description: Optional[str] = None
    sort_order: Optional[int] = 0


class ProductDocumentResponse(BaseModel):
    id: str
    product_id: str
    doc_type: str
    file_name: str
    file_path: str
    file_size: int
    description: Optional[str]
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}

class CategoryCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
    sort_order: Optional[int] = 0

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None

class CategoryResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str]
    parent_id: Optional[str]
    sort_order: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CategoryTreeResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str]
    parent_id: Optional[str]
    sort_order: int
    is_active: bool
    created_at: datetime
    children: list["CategoryTreeResponse"] = []

    model_config = {"from_attributes": True}

class ProductCreate(BaseModel):
    category_id: str
    name: str
    slug: str
    subtitle: Optional[str] = None
    description: Optional[str] = None
    technical_params: Optional[str] = None
    application_scenarios: Optional[str] = None
    advantages: Optional[str] = None
    specifications: Optional[dict] = None
    specifications_text: Optional[str] = None
    density: Optional[str] = None
    strength: Optional[str] = None
    thermal_conductivity: Optional[str] = None
    unit_weight: Optional[str] = None
    fire_rating: Optional[str] = None
    image_url: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    sort_order: Optional[int] = 0

class ProductUpdate(BaseModel):
    category_id: Optional[str] = None
    name: Optional[str] = None
    slug: Optional[str] = None
    subtitle: Optional[str] = None
    description: Optional[str] = None
    technical_params: Optional[str] = None
    application_scenarios: Optional[str] = None
    advantages: Optional[str] = None
    specifications: Optional[dict] = None
    specifications_text: Optional[str] = None
    density: Optional[str] = None
    strength: Optional[str] = None
    thermal_conductivity: Optional[str] = None
    unit_weight: Optional[str] = None
    fire_rating: Optional[str] = None
    image_url: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None

class ProductResponse(BaseModel):
    id: str
    category_id: str
    name: str
    slug: str
    subtitle: Optional[str]
    description: Optional[str]
    technical_params: Optional[str]
    application_scenarios: Optional[str]
    advantages: Optional[str]
    specifications: Optional[dict]
    specifications_text: Optional[str]
    density: Optional[str]
    strength: Optional[str]
    thermal_conductivity: Optional[str]
    unit_weight: Optional[str]
    fire_rating: Optional[str]
    image_url: Optional[str]
    meta_title: Optional[str]
    meta_description: Optional[str]
    sort_order: int
    is_active: bool
    view_count: int
    created_at: datetime

    model_config = {"from_attributes": True}