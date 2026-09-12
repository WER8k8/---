import uuid
from datetime import datetime, timezone

from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String, Text)
from sqlalchemy.orm import relationship

from app.core.database import UUID_TYPE, Base


class Province(Base):
    __tablename__ = "provinces"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(50), nullable=False, index=True)
    name_en = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc))
    updated_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc), onupdate=lambda: datetime.now(
                timezone.utc))

    cities = relationship("City", back_populates="province")


class City(Base):
    __tablename__ = "cities"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(50), nullable=False, index=True)
    name_en = Column(String(100))
    province_id = Column(
        UUID_TYPE,
        ForeignKey("provinces.id"),
        nullable=False,
        index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc))
    updated_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc), onupdate=lambda: datetime.now(
                timezone.utc))

    province = relationship("Province", back_populates="cities")
    districts = relationship("District", back_populates="city")


class District(Base):
    __tablename__ = "districts"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    name_en = Column(String(200))
    city_id = Column(
        UUID_TYPE,
        ForeignKey("cities.id"),
        nullable=False,
        index=True)
    province_id = Column(
        UUID_TYPE,
        ForeignKey("provinces.id"),
        nullable=False,
        index=True)
    is_active = Column(Boolean, default=True)
    is_disabled = Column(Boolean, default=False)
    created_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc))
    updated_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc), onupdate=lambda: datetime.now(
                timezone.utc))

    city = relationship("City", back_populates="districts")
    province = relationship("Province")


class IndustryKeyword(Base):
    __tablename__ = "industry_keywords"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    keyword = Column(String(200), nullable=False, index=True)
    keyword_type = Column(
        String(50), nullable=False, index=True
    )  # product, manufacturer, project, supply, price, local
    search_volume = Column(Integer, default=0)
    difficulty = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    category = Column(String(100))
    created_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc))
    updated_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc), onupdate=lambda: datetime.now(
                timezone.utc))


class KeywordGroup(Base):
    __tablename__ = "keyword_groups"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc))
    updated_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc), onupdate=lambda: datetime.now(
                timezone.utc))


class GroupKeyword(Base):
    __tablename__ = "group_keywords"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id = Column(
        UUID_TYPE,
        ForeignKey("keyword_groups.id"),
        nullable=False,
        index=True)
    keyword_id = Column(
        UUID_TYPE,
        ForeignKey("industry_keywords.id"),
        nullable=False,
        index=True)
    created_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc))

    group = relationship("KeywordGroup")
    keyword = relationship("IndustryKeyword")


class CombinatorialRule(Base):
    __tablename__ = "combinatorial_rules"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    # {district} + {product} + 厂家
    template = Column(String(500), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=10)
    created_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc))
    updated_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc), onupdate=lambda: datetime.now(
                timezone.utc))


class GeneratedKeyword(Base):
    __tablename__ = "generated_keywords"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    keyword = Column(String(500), nullable=False, index=True)
    district_id = Column(
        UUID_TYPE,
        ForeignKey("districts.id"),
        nullable=False,
        index=True)
    industry_keyword_id = Column(
        UUID_TYPE,
        ForeignKey("industry_keywords.id"),
        nullable=False,
        index=True)
    rule_id = Column(UUID_TYPE, ForeignKey(
        "combinatorial_rules.id"), index=True)
    search_volume = Column(Integer, default=0)
    difficulty = Column(Float, default=0.0)
    is_valid = Column(Boolean, default=True)
    is_used = Column(Boolean, default=False)
    created_at = Column(
        DateTime(
            timezone=True), default=lambda: datetime.now(
            timezone.utc))

    district = relationship("District")
    industry_keyword = relationship("IndustryKeyword")
    rule = relationship("CombinatorialRule")
