"""
商家IM路由配置和建材垂直参数的Pydantic Schemas

用于FastAPI请求/响应验证和序列化
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime


# ==================== MerchantIMRouting Schemas ====================

class MerchantIMRoutingBase(BaseModel):
    """商家IM路由配置基础Schema"""
    merchant_id: int = Field(..., description="商家/用户ID")
    country_code: str = Field(..., min_length=2, max_length=2, description="ISO国家代码 (如SA, BR, RU)")
    channel_type: str = Field(..., description="渠道类型: whatsapp, telegram, line, zalo, live_chat, form")
    account_id: str = Field(..., min_length=1, max_length=100, description="账号/手机号/链接")
    prefilled_text: Optional[str] = Field(None, description="预填母语迎客话术")
    is_active: bool = Field(True, description="是否启用")
    @field_validator('channel_type')
    @classmethod
    def validate_channel_type(cls, v):
        """validate_channel_type。

        参数说明：
        :param cls: 参数 cls
        :param v: 参数 v
        :return: 返回处理结果。
        """
        allowed = ['whatsapp', 'telegram', 'line', 'zalo', 'live_chat', 'form']
        if v not in allowed:
            raise ValueError(f'channel_type must be one of {allowed}')
        return v

    @field_validator('country_code')
    @classmethod
    def validate_country_code(cls, v):
        """validate_country_code。

        参数说明：
        :param cls: 参数 cls
        :param v: 参数 v
        :return: 返回处理结果。
        """
        return v.upper()


class MerchantIMRoutingCreate(MerchantIMRoutingBase):
    """创建IM路由配置请求Schema"""
    pass


class MerchantIMRoutingUpdate(BaseModel):
    """更新IM路由配置请求Schema（部分字段可选）"""
    country_code: Optional[str] = Field(None, min_length=2, max_length=2)
    channel_type: Optional[str] = Field(None)
    account_id: Optional[str] = Field(None, min_length=1, max_length=100)
    prefilled_text: Optional[str] = Field(None)
    is_active: Optional[bool] = Field(None)
    @field_validator('channel_type')
    @classmethod
    def validate_channel_type(cls, v):
        """validate_channel_type。

        参数说明：
        :param cls: 参数 cls
        :param v: 参数 v
        :return: 返回处理结果。
        """
        if v is not None:
            allowed = ['whatsapp', 'telegram', 'line', 'zalo', 'live_chat', 'form']
            if v not in allowed:
                raise ValueError(f'channel_type must be one of {allowed}')
            return v
        return v

    @field_validator('country_code')
    @classmethod
    def validate_country_code(cls, v):
        """validate_country_code。

        参数说明：
        :param cls: 参数 cls
        :param v: 参数 v
        :return: 返回处理结果。
        """
        if v is not None:
            return v.upper()
        return v


class MerchantIMRoutingResponse(MerchantIMRoutingBase):
    """IM路由配置响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class IMChannelResponse(BaseModel):
    """IM渠道响应（供前端动态加载）"""
    model_config = ConfigDict(from_attributes=True)
    channel_type: str
    account_id: str
    prefilled_text: Optional[str]
    im_link: str  # 生成的链接 (wa.me, t.me等)
    display_text: str  # 显示文本 ("Chat on WhatsApp"等)


# ==================== BuildingMaterialSpec Schemas ====================

class BuildingMaterialSpecBase(BaseModel):
    """建材垂直参数基础Schema"""
    product_id: int = Field(..., description="产品ID")
    spec_key: str = Field(..., min_length=1, max_length=50, description="参数名: weight, mesh_size, tensile_strength")
    spec_value: float = Field(..., description="参数值: 160, 4, 1200")
    metric_unit: str = Field(..., min_length=1, max_length=10, description="公制单位: g/m², mm, N/50mm")
    imperial_unit: Optional[str] = Field(None, description="英制单位: oz/yd², inch")
    imperial_scale_factor: Optional[float] = Field(None, description="换算系数 (公制转英制)")
    trust_badges: Optional[List[str]] = Field(None, description="证书数组: ['CE', 'ISO9001', 'SABER']")


class BuildingMaterialSpecCreate(BuildingMaterialSpecBase):
    """创建建材参数请求Schema"""
    pass


class BuildingMaterialSpecUpdate(BaseModel):
    """更新建材参数请求Schema（部分字段可选）"""
    spec_key: Optional[str] = Field(None, min_length=1, max_length=50)
    spec_value: Optional[float] = Field(None)
    metric_unit: Optional[str] = Field(None, min_length=1, max_length=10)
    imperial_unit: Optional[str] = Field(None)
    imperial_scale_factor: Optional[float] = Field(None)
    trust_badges: Optional[List[str]] = Field(None)


class BuildingMaterialSpecResponse(BuildingMaterialSpecBase):
    """建材参数响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class BuildingMaterialSpecWithUnitResponse(BaseModel):
    """建材参数响应（含单位换算）"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    spec_key: str
    spec_value: float
    spec_unit: str  # 根据use_imperial动态选择
    trust_badges: Optional[List[str]]
    @classmethod
    def from_orm_with_unit(cls, spec, use_imperial: bool = False):
        """从ORM对象创建响应（含单位换算）"""
        if use_imperial and spec.imperial_unit and spec.imperial_scale_factor:
            display_value = float(spec.spec_value) * float(spec.imperial_scale_factor)
            display_unit = spec.imperial_unit
        else:
            display_value = float(spec.spec_value)
            display_unit = spec.metric_unit
        
        return cls(
            id=spec.id,
            product_id=spec.product_id,
            spec_key=spec.spec_key,
            spec_value=display_value,
            spec_unit=display_unit,
            trust_badges=spec.trust_badges or []
        )


class ProductSpecsResponse(BaseModel):
    """产品参数列表响应（供移动端渲染折叠框）"""
    model_config = ConfigDict(from_attributes=True)
    product_id: int
    specs: List[BuildingMaterialSpecWithUnitResponse]
    trust_badges: List[str]  # 去重的证书列表
