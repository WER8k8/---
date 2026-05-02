"""A/B 测试数据模型"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class ABTest(Base):
    """A/B 测试实验表"""
    __tablename__ = "ab_tests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment="实验名称")
    description = Column(Text, comment="实验描述")
    
    # 实验配置
    experiment_type = Column(String(50), default='page', comment="实验类型: page/component/element")
    target_url = Column(String(500), nullable=False, comment="目标页面URL")
    status = Column(String(20), default='draft', comment="状态: draft/running/paused/completed")
    
    # 变体配置 (JSON格式)
    # 示例: {"variants": [{"id": "A", "name": "原版", "weight": 50}, {"id": "B", "name": "变体1", "weight": 50}]}
    variants_config = Column(JSON, nullable=False, comment="变体配置")
    
    # 流量分配
    traffic_percentage = Column(Float, default=100.0, comment="参与实验的流量百分比")
    
    # 目标指标
    primary_metric = Column(String(100), comment="主要指标: conversion/click_through/time_on_page")
    secondary_metrics = Column(JSON, comment="次要指标列表")
    
    # 统计配置
    min_sample_size = Column(Integer, default=1000, comment="最小样本量")
    confidence_level = Column(Float, default=0.95, comment="置信水平")
    
    # 时间配置
    start_date = Column(DateTime, comment="开始时间")
    end_date = Column(DateTime, comment="结束时间")
    
    # 结果统计
    total_visitors = Column(Integer, default=0, comment="总访问人数")
    winner_variant = Column(String(50), comment="获胜变体ID")
    statistical_significance = Column(Float, default=0.0, comment="统计显著性")
    
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")
    
    # 关系
    variants = relationship("ABTestVariant", back_populates="experiment", cascade="all, delete-orphan")
    events = relationship("ABTestEvent", back_populates="experiment", cascade="all, delete-orphan")
    creator = relationship("User")


class ABTestVariant(Base):
    """A/B 测试变体表"""
    __tablename__ = "ab_test_variants"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("ab_tests.id", ondelete="CASCADE"), nullable=False, comment="实验ID")
    
    variant_id = Column(String(50), nullable=False, comment="变体标识: A, B, C...")
    name = Column(String(200), nullable=False, comment="变体名称")
    description = Column(Text, comment="变体描述")
    
    # 变体内容配置
    content_config = Column(JSON, comment="变体内容配置")
    
    # 权重配置
    weight = Column(Float, default=50.0, comment="流量权重")
    
    # 统计数据
    visitors = Column(Integer, default=0, comment="访问人数")
    conversions = Column(Integer, default=0, comment="转化次数")
    conversion_rate = Column(Float, default=0.0, comment="转化率")
    
    # 其他指标
    metrics_data = Column(JSON, comment="详细指标数据")
    
    is_control = Column(Boolean, default=False, comment="是否为对照组")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    # 关系
    experiment = relationship("ABTest", back_populates="variants")


class ABTestEvent(Base):
    """A/B 测试事件记录表"""
    __tablename__ = "ab_test_events"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("ab_tests.id", ondelete="CASCADE"), nullable=False, comment="实验ID")
    
    # 用户标识
    session_id = Column(String(100), nullable=False, index=True, comment="会话ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="用户ID（如果已登录）")
    
    # 变体信息
    variant_id = Column(String(50), nullable=False, comment="分配的变体ID")
    
    # 事件类型
    event_type = Column(String(50), nullable=False, comment="事件类型: impression/click/conversion/scroll")
    
    # 事件数据
    event_data = Column(JSON, comment="事件详细数据")
    
    # 页面信息
    page_url = Column(String(500), comment="页面URL")
    referrer = Column(String(500), comment="来源页面")
    
    # 设备信息
    device_type = Column(String(50), comment="设备类型: desktop/mobile/tablet")
    browser = Column(String(100), comment="浏览器")
    
    created_at = Column(DateTime, default=datetime.now, index=True, comment="事件时间")
    
    # 关系
    experiment = relationship("ABTest", back_populates="events")
    user = relationship("User")


class ABTestConversion(Base):
    """A/B 测试转化记录表"""
    __tablename__ = "ab_test_conversions"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("ab_tests.id", ondelete="CASCADE"), nullable=False, comment="实验ID")
    variant_id = Column(String(50), nullable=False, comment="变体ID")
    
    session_id = Column(String(100), nullable=False, index=True, comment="会话ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="用户ID")
    
    # 转化信息
    conversion_type = Column(String(50), nullable=False, comment="转化类型: form_submit/click/purchase")
    conversion_value = Column(Float, default=0.0, comment="转化价值")
    
    # 转化详情
    conversion_data = Column(JSON, comment="转化详细数据")
    
    created_at = Column(DateTime, default=datetime.now, index=True, comment="转化时间")
    
    # 关系
    experiment = relationship("ABTest")
    user = relationship("User")
