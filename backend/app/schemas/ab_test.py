from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator


class ABTestVariantConfig(BaseModel):
    """A/B 测试变体配置"""
    id: str
    name: str
    weight: float = Field(..., ge=0, le=100, description="流量权重，范围 0-100")


class ABTestVariantsConfig(BaseModel):
    """A/B 测试变体完整配置"""
    variants: List[ABTestVariantConfig]
    
    @field_validator('variants')
    @classmethod
    def validate_variants(cls, v):
        if not v:
            raise ValueError('variants 列表不能为空')
        
        # 验证 variant id 唯一性
        variant_ids = [variant.id for variant in v]
        if len(variant_ids) != len(set(variant_ids)):
            raise ValueError('variant id 必须唯一')
        
        # 验证权重总和（允许小误差）
        total_weight = sum(variant.weight for variant in v)
        if abs(total_weight - 100) > 0.01:
            raise ValueError(f'权重总和必须为 100，当前为 {total_weight}')
        
        return v


class ABTestCreate(BaseModel):
    """创建 A/B 测试的请求"""
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    experiment_type: str = Field(default='page', max_length=50, description="实验类型: page/component/element")
    target_url: str = Field(..., max_length=500)
    variants_config: ABTestVariantsConfig
    traffic_percentage: float = Field(default=100.0, ge=0, le=100)
    primary_metric: Optional[str] = Field(default=None, max_length=100)
    secondary_metrics: Optional[List[str]] = None
    min_sample_size: int = Field(default=1000, ge=1)
    confidence_level: float = Field(default=0.95, ge=0.8, le=0.999)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ABTestUpdate(BaseModel):
    """更新 A/B 测试的请求"""
    name: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = None
    experiment_type: Optional[str] = Field(default=None, max_length=50)
    target_url: Optional[str] = Field(default=None, max_length=500)
    status: Optional[str] = Field(default=None, max_length=20, description="状态: draft/running/paused/completed")
    variants_config: Optional[ABTestVariantsConfig] = None
    traffic_percentage: Optional[float] = Field(default=None, ge=0, le=100)
    primary_metric: Optional[str] = Field(default=None, max_length=100)
    secondary_metrics: Optional[List[str]] = None
    min_sample_size: Optional[int] = Field(default=None, ge=1)
    confidence_level: Optional[float] = Field(default=None, ge=0.8, le=0.999)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    winner_variant: Optional[str] = Field(default=None, max_length=50)


class ABTestResponse(BaseModel):
    """A/B 测试响应"""
    id: int
    name: str
    description: Optional[str] = None
    experiment_type: str
    target_url: str
    status: str
    variants_config: Dict[str, Any]
    traffic_percentage: float
    primary_metric: Optional[str] = None
    secondary_metrics: Optional[List[str]] = None
    min_sample_size: int
    confidence_level: float
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    total_visitors: int = 0
    winner_variant: Optional[str] = None
    statistical_significance: float = 0.0
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    
    model_config = {"from_attributes": True}


class ABTestVariantCreate(BaseModel):
    """创建 A/B 测试变体的请求"""
    variant_id: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    content_config: Optional[Dict[str, Any]] = None
    weight: float = Field(default=50.0, ge=0, le=100)
    is_control: bool = False


class ABTestVariantUpdate(BaseModel):
    """更新 A/B 测试变体的请求"""
    name: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = None
    content_config: Optional[Dict[str, Any]] = None
    weight: Optional[float] = Field(default=None, ge=0, le=100)
    is_control: Optional[bool] = None


class ABTestVariantResponse(BaseModel):
    """A/B 测试变体响应"""
    id: int
    experiment_id: int
    variant_id: str
    name: str
    description: Optional[str] = None
    content_config: Optional[Dict[str, Any]] = None
    weight: float
    visitors: int = 0
    conversions: int = 0
    conversion_rate: float = 0.0
    metrics_data: Optional[Dict[str, Any]] = None
    is_control: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}


class ABTestEventCreate(BaseModel):
    """创建 A/B 测试事件的请求"""
    session_id: str = Field(..., max_length=100)
    user_id: Optional[int] = None
    variant_id: str = Field(..., max_length=50)
    event_type: str = Field(..., max_length=50)
    event_data: Optional[Dict[str, Any]] = None
    page_url: Optional[str] = Field(default=None, max_length=500)
    referrer: Optional[str] = Field(default=None, max_length=500)
    device_type: Optional[str] = Field(default=None, max_length=50)
    browser: Optional[str] = Field(default=None, max_length=100)


class ABTestEventResponse(BaseModel):
    """A/B 测试事件响应"""
    id: int
    experiment_id: int
    session_id: str
    user_id: Optional[int] = None
    variant_id: str
    event_type: str
    event_data: Optional[Dict[str, Any]] = None
    page_url: Optional[str] = None
    referrer: Optional[str] = None
    device_type: Optional[str] = None
    browser: Optional[str] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}


class ABTestConversionCreate(BaseModel):
    """创建 A/B 测试转化的请求"""
    session_id: str = Field(..., max_length=100)
    user_id: Optional[int] = None
    variant_id: str = Field(..., max_length=50)
    conversion_type: str = Field(..., max_length=50)
    conversion_value: float = 0.0
    conversion_data: Optional[Dict[str, Any]] = None


class ABTestConversionResponse(BaseModel):
    """A/B 测试转化响应"""
    id: int
    experiment_id: int
    variant_id: str
    session_id: str
    user_id: Optional[int] = None
    conversion_type: str
    conversion_value: float
    conversion_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}
