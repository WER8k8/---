"""
全球化多语言模型
- GlossaryTerm: 行业术语多语言标准化
- TranslationTask: 翻译任务与进度跟踪
- TranslationRecord: 逐条翻译记录
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text

from app.core.database import UUID_TYPE, Base


class GlossaryTerm(Base):
    """行业术语库 — 多语言标准化映射"""
    __tablename__ = "glossary_terms"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    zh = Column(String(200), nullable=False, index=True)        # 中文
    en = Column(String(200), nullable=False, index=True)         # English
    ja = Column(String(200), index=True)                         # 日本語
    ko = Column(String(200), index=True)                         # 한국어
    # 欧美
    de = Column(String(200), index=True)                         # Deutsch
    fr = Column(String(200), index=True)                         # Français
    es = Column(String(200), index=True)                         # Español
    pt = Column(String(200), index=True)                         # Português
    it = Column(String(200), index=True)                         # Italiano
    nl = Column(String(200), index=True)                         # Nederlands
    ru = Column(String(200), index=True)                         # Русский
    # 中东
    ar = Column(String(200), index=True)                         # العربية
    tr = Column(String(200), index=True)                         # Türkçe
    fa = Column(String(200), index=True)                         # فارسی
    he = Column(String(200), index=True)                         # עברית
    # 东南亚
    th = Column(String(200), index=True)                         # ไทย
    vi = Column(String(200), index=True)                         # Tiếng Việt
    ms = Column(String(200), index=True)                         # Bahasa Melayu
    # 南亚
    hi = Column(String(200), index=True)                         # हिन्दी
    _id_ba = Column("id_ba", String(200), index=True)            # Bahasa Indonesia
    tl = Column(String(200), index=True)                         # Filipino
    bn = Column(String(200), index=True)                         # বাংলা
    my = Column(String(200), index=True)                         # မြန်မာဘာသာ
    km = Column(String(200), index=True)                         # ភាសាខ្មែរ
    # 中东欧
    pl = Column(String(200), index=True)                         # Polski
    cs = Column(String(200), index=True)                         # Čeština
    uk = Column(String(200), index=True)                         # Українська
    # 北欧
    sv = Column(String(200), index=True)                         # Svenska
    # 非洲
    sw = Column(String(200), index=True)                         # Kiswahili
    ha = Column(String(200), index=True)                         # Hausa
    zu = Column(String(200), index=True)                         # isiZulu
    am = Column(String(200), index=True)                         # አማርኛ
    category = Column(String(50), default="建材", index=True)     # 行业分类
    status = Column(String(20), default="pending", index=True)    # draft/pending/confirmed
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class TranslationTask(Base):
    """翻译任务"""
    __tablename__ = "translation_tasks"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    source_lang = Column(String(10), default="zh", nullable=False)
    target_lang = Column(String(10), nullable=False)
    total_items = Column(Integer, default=0)
    completed_items = Column(Integer, default=0)
    status = Column(String(20), default="queued", index=True)     # queued/running/done/failed
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class TranslationRecord(Base):
    """逐条翻译记录"""
    __tablename__ = "translation_records"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(UUID_TYPE, ForeignKey("translation_tasks.id"), index=True)
    source_text = Column(Text, nullable=False)
    translated_text = Column(Text)
    source_lang = Column(String(10), default="zh", nullable=False)
    target_lang = Column(String(10), nullable=False)
    status = Column(String(20), default="queued", index=True)
    rating = Column(Integer, default=0)                           # 人工评分 1-5
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
