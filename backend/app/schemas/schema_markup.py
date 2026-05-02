from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class SchemaMarkupCreate(BaseModel):
    name: str
    schema_type: str
    content: Dict[str, Any]
    page_url: Optional[str] = None


class SchemaMarkupUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    page_url: Optional[str] = None
    version: Optional[str] = None


class SchemaMarkupResponse(BaseModel):
    id: str
    name: str
    schema_type: str
    content: Dict[str, Any]
    is_active: bool
    page_url: Optional[str]
    version: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SchemaTemplateResponse(BaseModel):
    id: str
    name: str
    schema_type: str
    template: Dict[str, Any]
    description: Optional[str]
    category: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class GenerateSchemaRequest(BaseModel):
    schema_type: str
    data: Dict[str, Any]
    include_context: bool = True


class ValidateSchemaRequest(BaseModel):
    content: Dict[str, Any]


class SchemaValidationResult(BaseModel):
    is_valid: bool
    errors: List[Dict[str, str]]
    warnings: List[Dict[str, str]]
    schema_type: Optional[str]