# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
商家IM路由配置表和建材垂直参数表 - SQLAlchemy ORM模型

根据文档14.1章节：
1. MerchantIMRouting - 商家即时通讯分流配置表
2. BuildingMaterialSpec - 建材垂直参数表
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, Numeric, TIMESTAMP, func
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import json


class MerchantIMRouting(Base):
    """商家即时通讯分流配置表
    
    功能：根据买家IP国家代码，动态返回对应的IM渠道配置
    用途：全球买家看到适合自己习惯的沟通工具（WhatsApp/Telegram/Line等）
    """
    __tablename__ = 'merchant_im_routing'
    # 库与 schemas/im_routing_and_specs.py 的响应模型都按整型 id 定义，
    # 此前模型被改成 UUID_TYPE 但没有配套迁移，写入必然失败；按真实形状订正。
    id = Column(Integer, primary_key=True, autoincrement=True)
    merchant_id = Column(Integer, nullable=False, index=True)  # 关联商家/用户ID
    country_code = Column(String(2), nullable=False, index=True)  # ISO国家代码 (SA, BR, RU, TH, NG)
    channel_type = Column(String(20), nullable=False)  # 渠道: whatsapp, telegram, line, zalo, live_chat, form
    account_id = Column(String(100), nullable=False)  # 账号/手机号/链接 (如 +966500000000)
    prefilled_text = Column(Text, nullable=True)  # 预填母语迎客话术
    is_active = Column(Boolean, default=True)  # 是否启用
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    # 索引已在迁移文件中创建：idx_merchant_country (merchant_id, country_code)
    def __repr__(self):
        """__repr__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return f"<MerchantIMRouting(id={self.id}, merchant_id={self.merchant_id}, country={self.country_code}, channel={self.channel_type})>"
    
    def to_dict(self):
        """转换为字典（供FastAPI返回JSON）"""
        return {
            "id": self.id,
            "merchant_id": self.merchant_id,
            "country_code": self.country_code,
            "channel_type": self.channel_type,
            "account_id": self.account_id,
            "prefilled_text": self.prefilled_text,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class BuildingMaterialSpec(Base):
    """建材垂直参数表
    
    功能：存储建材产品的结构化技术参数（拒绝富文本）
    用途：Nuxt 3拿到JSON后自动在手机端渲染成折叠框（手风琴组件）
    """
    __tablename__ = 'building_material_specs'
    id = Column(Integer, primary_key=True, autoincrement=True)  # 同上：库与响应模型均为整型
    product_id = Column(Integer, nullable=False, index=True)  # 关联产品ID
    spec_key = Column(String(50), nullable=False, index=True)  # 参数名: weight, mesh_size, tensile_strength
    spec_value = Column(Numeric, nullable=False)  # 参数值: 160, 4, 1200
    metric_unit = Column(String(10), nullable=False)  # 公制单位: g/m², mm, N/50mm
    imperial_unit = Column(String(10), nullable=True)  # 英制单位: oz/yd², inch (欧美IP自动换算)
    imperial_scale_factor = Column(Numeric, nullable=True)  # 换算系数 (公制转英制的乘数)
    trust_badges = Column(Text, nullable=True)  # JSON字符串，勾选的证书数组: '["CE", "ISO9001", "SABER"]'
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    # 索引已在迁移文件中创建：idx_product_spec (product_id, spec_key)
    def __repr__(self):
        """__repr__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return f"<BuildingMaterialSpec(id={self.id}, product_id={self.product_id}, key={self.spec_key}, value={self.spec_value})>"
    
    def to_dict(self, use_imperial=False):
        """转换为字典（供FastAPI返回JSON）
        
        Args:
            use_imperial: 是否使用英制单位（欧美IP自动切换）
        """
        result = {
            "id": self.id,
            "product_id": self.product_id,
            "spec_key": self.spec_key,
            "trust_badges": json.loads(self.trust_badges) if self.trust_badges else [],
        }
        if use_imperial and self.imperial_unit and self.imperial_scale_factor:
            # 使用英制单位
            result["spec_value"] = float(self.spec_value) * float(self.imperial_scale_factor)
            result["spec_unit"] = self.imperial_unit
        else:
            # 使用公制单位
            result["spec_value"] = float(self.spec_value)
            result["spec_unit"] = self.metric_unit
        
        return result
    
    def get_formatted_spec(self, use_imperial=False):
        """返回格式化的参数字符串（供前端显示）
        
        Example: "160 g/m²" or "4.72 oz/yd²"
        """
        if use_imperial and self.imperial_unit and self.imperial_scale_factor:
            value = float(self.spec_value) * float(self.imperial_scale_factor)
            return f"{value:.2f} {self.imperial_unit}"
        else:
            return f"{float(self.spec_value)} {self.metric_unit}"
