import json
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, field_validator


class ABTestVariantCreate(BaseModel):
    variant_id: str
    name: str
    description: Optional[str] = None
    content_config: Optional[dict] = None
    weight: Optional[float] = 50.0
    is_control: Optional[bool] = False


class ABTestVariantUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    content_config: Optional[dict] = None
    weight: Optional[float] = None
    is_control: Optional[bool] = None


class ABTestVariantResponse(BaseModel):
    id: int
    experiment_id: int
    variant_id: str
    name: str
    description: Optional[str]
    content_config: Optional[dict]
    weight: float
    visitors: int
    @field_validator("content_config", mode="before")
    @classmethod
    def parse_content_config(cls, v):
        """parse_content_config。

        参数说明：
        :param cls: 参数 cls
        :param v: 参数 v
        :return: 返回处理结果。
        """
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return None
        return v
    conversions: int
    conversion_rate: float
    metrics_data: Optional[dict]
    is_control: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class ABTestCreate(BaseModel):
    name: str
    description: Optional[str] = None
    experiment_type: Optional[str] = "page"
    target_url: str
    variants_config: dict
    traffic_percentage: Optional[float] = 100.0
    primary_metric: Optional[str] = None
    secondary_metrics: Optional[List[str]] = None
    min_sample_size: Optional[int] = 1000
    confidence_level: Optional[float] = 0.95
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ABTestUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    experiment_type: Optional[str] = None
    target_url: Optional[str] = None
    status: Optional[str] = None
    variants_config: Optional[dict] = None
    traffic_percentage: Optional[float] = None
    primary_metric: Optional[str] = None
    secondary_metrics: Optional[List[str]] = None
    min_sample_size: Optional[int] = None
    confidence_level: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ABTestResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    experiment_type: str
    target_url: str
    status: str
    variants_config: dict
    traffic_percentage: float
    @field_validator('variants_config', mode='before')
    @classmethod
    def parse_variants_config(cls, v):
        """parse_variants_config。

        参数说明：
        :param cls: 参数 cls
        :param v: 参数 v
        :return: 返回处理结果。
        """
        if isinstance(v, str):
            return json.loads(v)
        return v
    primary_metric: Optional[str]
    secondary_metrics: Optional[List[str]]
    @field_validator('secondary_metrics', mode='before')
    @classmethod
    def parse_secondary_metrics(cls, v):
        """parse_secondary_metrics。

        参数说明：
        :param cls: 参数 cls
        :param v: 参数 v
        :return: 返回处理结果。
        """
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return None
        return v
    secondary_metrics: Optional[List[str]]
    min_sample_size: int
    confidence_level: float
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    total_visitors: int
    winner_variant: Optional[str]
    statistical_significance: float
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    model_config = {"from_attributes": True}


class ABTestDetailResponse(ABTestResponse):
    variants: List[ABTestVariantResponse] = []


class ABTestEventResponse(BaseModel):
    id: int
    experiment_id: int
    session_id: str
    user_id: Optional[str]
    variant_id: str
    event_type: str
    event_data: Optional[dict]
    page_url: Optional[str]
    @field_validator("event_data", mode="before")
    @classmethod
    def parse_event_data(cls, v):
        """parse_event_data。

        参数说明：
        :param cls: 参数 cls
        :param v: 参数 v
        :return: 返回处理结果。
        """
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return None
        return v
    referrer: Optional[str]
    device_type: Optional[str]
    browser: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}


class ABTestConversionResponse(BaseModel):
    id: int
    experiment_id: int
    variant_id: str
    session_id: str
    user_id: Optional[str]
    conversion_type: str
    conversion_value: float
    conversion_data: Optional[dict]
    created_at: datetime
    @field_validator("conversion_data", mode="before")
    @classmethod
    def parse_conversion_data(cls, v):
        """parse_conversion_data。

        参数说明：
        :param cls: 参数 cls
        :param v: 参数 v
        :return: 返回处理结果。
        """
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return None
        return v

    model_config = {"from_attributes": True}


class ABTestListResponse(BaseModel):
    items: List[ABTestResponse]
    total: int
    page: int
    page_size: int


class BatchDeleteRequest(BaseModel):
    ids: List[int]
