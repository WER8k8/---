from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Author(Base):
    """作者/专家模型"""
    __tablename__ = "eeat_authors"
    
    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    bio = Column(Text)
    title = Column(String(100))
    company = Column(String(100))
    email = Column(String(100))
    linkedin_url = Column(String(255))
    twitter_url = Column(String(255))
    expertise_areas = Column(JSON)
    credentials = Column(JSON)
    is_verified = Column(Boolean, default=False)
    trust_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    articles = relationship("ArticleAuthor", back_populates="author")
    certifications = relationship("AuthorCertification", back_populates="author")

class AuthorCertification(Base):
    """作者认证/资质模型"""
    __tablename__ = "eeat_author_certifications"
    
    id = Column(String(36), primary_key=True, index=True)
    author_id = Column(String(36), ForeignKey("eeat_authors.id"))
    certification_name = Column(String(200), nullable=False)
    issuing_body = Column(String(200))
    issue_date = Column(DateTime)
    expiration_date = Column(DateTime)
    credential_number = Column(String(100))
    is_valid = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    author = relationship("Author", back_populates="certifications")

class ArticleAuthor(Base):
    """文章-作者关联模型"""
    __tablename__ = "eeat_article_authors"
    
    id = Column(String(36), primary_key=True, index=True)
    article_id = Column(String(36), nullable=False)
    author_id = Column(String(36), ForeignKey("eeat_authors.id"))
    author_type = Column(String(50), default="primary")  # primary, co-author, contributor
    role = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    author = relationship("Author", back_populates="articles")

class EEATScore(Base):
    """EEAT评分记录模型"""
    __tablename__ = "eeat_scores"
    
    id = Column(String(36), primary_key=True, index=True)
    content_id = Column(String(36), nullable=False)
    content_type = Column(String(50), nullable=False)  # article, page, product
    experience_score = Column(Float, default=0.0)
    expertise_score = Column(Float, default=0.0)
    authoritativeness_score = Column(Float, default=0.0)
    trustworthiness_score = Column(Float, default=0.0)
    overall_score = Column(Float, default=0.0)
    factors = Column(JSON)
    recommendations = Column(JSON)
    evaluated_at = Column(DateTime, default=datetime.utcnow)

class TrustSignal(Base):
    """可信度信号模型"""
    __tablename__ = "eeat_trust_signals"
    
    id = Column(String(36), primary_key=True, index=True)
    content_id = Column(String(36), nullable=False)
    signal_type = Column(String(100), nullable=False)
    signal_value = Column(String(500))
    score_impact = Column(Float, default=0.0)
    is_positive = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
