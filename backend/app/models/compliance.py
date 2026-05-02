"""合规检查相关数据库模型"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON, Float, Integer
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class ComplianceRule(Base):
    """合规规则模型"""
    __tablename__ = "compliance_rules"
    
    id = Column(String(36), primary_key=True, index=True)
    rule_name = Column(String(100), nullable=False)
    rule_type = Column(String(50), nullable=False, index=True)  # forbidden_word, sensitive_content, ad_law
    keywords = Column(JSON, nullable=False)  # 违禁词/敏感词列表
    severity = Column(String(20), nullable=False)  # high, medium, low
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ComplianceScanResult(Base):
    """合规扫描结果模型"""
    __tablename__ = "compliance_scan_results"
    
    id = Column(String(36), primary_key=True, index=True)
    content_id = Column(String(36), nullable=False, index=True)
    content_type = Column(String(50), nullable=False)
    content_title = Column(String(255))
    content_text = Column(Text)
    scan_status = Column(String(20), nullable=False)  # pending, scanning, completed, error
    total_issues = Column(Integer, default=0)
    high_severity_count = Column(Integer, default=0)
    medium_severity_count = Column(Integer, default=0)
    low_severity_count = Column(Integer, default=0)
    scan_details = Column(JSON)  # 详细扫描结果
    suggestions = Column(JSON)  # 改进建议
    scanned_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class ComplianceViolation(Base):
    """违规记录模型"""
    __tablename__ = "compliance_violations"
    
    id = Column(String(36), primary_key=True, index=True)
    scan_result_id = Column(String(36), index=True)
    rule_id = Column(String(36), index=True)
    rule_name = Column(String(100))
    rule_type = Column(String(50))
    severity = Column(String(20))
    matched_text = Column(String(255))  # 匹配到的违规文本
    context = Column(String(500))  # 上下文
    suggestion = Column(Text)  # 修正建议
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class AdvertisementLawKeyword(Base):
    """广告法违禁词模型"""
    __tablename__ = "ad_law_keywords"
    
    id = Column(String(36), primary_key=True, index=True)
    keyword = Column(String(100), nullable=False, unique=True)
    category = Column(String(100), nullable=False)  # 极限词、虚假宣传、医疗用语等
    severity = Column(String(20), nullable=False)  # high, medium, low
    description = Column(Text)  # 违规说明
    alternative = Column(String(255))  # 建议替换词
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
